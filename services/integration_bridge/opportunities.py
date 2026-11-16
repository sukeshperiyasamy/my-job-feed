"""Source-backed internship/research catalog. Unknown facts stay explicitly unknown."""
import hashlib
import json
import re
import threading
from datetime import datetime, timezone, timedelta, date
from zoneinfo import ZoneInfo
from pathlib import Path
from typing import Literal
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from services.integration_bridge.models import Job, WatchedCompany
from services.job_collector.careers import canonical_url

ROOT=Path(__file__).resolve().parents[2]
STORE=ROOT/'data'/'opportunities'/'catalog.json'
LOCK=threading.RLock()

class OpportunityInput(BaseModel):
    category:Literal['internship','research','job','remote']
    title:str=Field(min_length=1,max_length=300)
    organization:str=Field(min_length=1,max_length=255)
    location:str='Not stated'
    source_url:str
    application_url:str
    source_name:str
    status:Literal['Verified open','Unverified','Expired','Upcoming','Hiring signal']='Unverified'
    verified_at:str|None=None
    source_date:str|None=None
    deadline:str|None=None
    deadline_date:str|None=None
    deadline_note:str='Not published'
    evidence:str=''
    details:dict=Field(default_factory=dict)

def read_catalog():
    if STORE.exists():return json.loads(STORE.read_text(encoding='utf-8-sig'))
    seed=ROOT/'config'/'opportunity-seeds.json'
    rows=json.loads(seed.read_text(encoding='utf-8-sig')) if seed.exists() else []
    extra=ROOT/'config'/'opportunity-extra-seeds.json'
    if extra.exists():
        known={r['id'] for r in rows}
        rows.extend(r for r in json.loads(extra.read_text(encoding='utf-8-sig')) if r['id'] not in known)
    return rows

def effective_status(row, now=None):
    now=now or datetime.now(timezone.utc)
    if row.get('deadline_date'):
        try:
            if date.fromisoformat(row['deadline_date'])<now.astimezone(ZoneInfo('Asia/Kolkata')).date():return 'Expired'
        except ValueError:return 'Unverified'
    if row.get('deadline'):
        try:
            deadline=datetime.fromisoformat(row['deadline'].replace('Z','+00:00'))
            if deadline.tzinfo is None:return 'Unverified'
            if deadline<now:return 'Expired'
        except ValueError:return 'Unverified'
    if row.get('status')=='Verified open':
        try:
            checked=datetime.fromisoformat(row['verified_at'].replace('Z','+00:00'))
            if checked.tzinfo is None or checked>now+timedelta(minutes=5):return 'Unverified'
            if now-checked>timedelta(days=3):return 'Needs recheck'
        except (ValueError,KeyError,AttributeError):return 'Unverified'
    return row.get('status','Unverified')

def catalog_router(db_factory):
    router=APIRouter()
    @router.get('/api/opportunities')
    def list_opportunities(category:str|None=None):
        with LOCK:rows=read_catalog()
        with db_factory() as db:
            watched={c.name:c for c in db.query(WatchedCompany).all()}
            known={canonical_url(r['application_url']).removesuffix('/apply') for r in rows}
            for job in db.query(Job).order_by(Job.discovery_date.desc()).all():
                if not re.search(r'\bintern(?:ship)?\b|\bapprentice\b|\btrainee\b',job.title,re.I):continue
                try:url=canonical_url(job.canonical_url)
                except ValueError:continue
                if url.removesuffix('/apply') in known:continue
                company=watched.get(job.company_name)
                rows.append({'id':'job-'+str(job.id),'job_id':job.id,'category':'internship','title':job.title,'organization':job.company_name,'location':job.location or 'Not stated','status':'Unverified','source_name':job.source,'source_url':company.careers_url if company else job.canonical_url,'application_url':job.canonical_url,'verified_at':None,'source_date':job.posting_date.isoformat() if job.posting_date else None,'first_seen_at':job.discovery_date.isoformat(),'deadline':None,'deadline_note':'Not published / not checked','evidence':'Imported by the collector; current application availability and eligibility have not been reviewed.','details':{'description':job.description or 'No description provided by the source.','experience':'Not verified; read the original description','eligibility':'Requires review','pay':'Undisclosed','duration':'Not stated','fit':'Potential lead based on title. Eligibility not established.','recommended_resume':'Biomedical / embedded resume for device roles; software resume for AI/software roles.','apply_mode':'Review before adding to the application queue'}})
        result=[]
        for original in rows:
            if category and original.get('category')!=category:continue
            row=dict(original);row['effective_status']=effective_status(row)
            if row.get('deadline'):
                try:row['days_left']=max(0,(datetime.fromisoformat(row['deadline'])-datetime.now(timezone.utc)).total_seconds()/86400)
                except (ValueError,TypeError):row['days_left']=None
            elif row.get('deadline_date'):
                try:row['days_left']=max(0,(date.fromisoformat(row['deadline_date'])-datetime.now(ZoneInfo('Asia/Kolkata')).date()).days)
                except ValueError:row['days_left']=None
            row['urgent']=row.get('effective_status')=='Verified open' and row.get('days_left') is not None and row['days_left']<=14
            result.append(row)
        result.sort(key=lambda r:(not r['urgent'],r['effective_status']!='Verified open',r.get('deadline') or '9999',r['title']))
        return result

    @router.post('/api/opportunities')
    def save_opportunity(body:OpportunityInput):
        data=body.model_dump()
        try:
            data['source_url']=canonical_url(body.source_url)
            data['application_url']=canonical_url(body.application_url)
            if body.deadline and datetime.fromisoformat(body.deadline).tzinfo is None:raise ValueError('Deadline must include a timezone; do not invent a closing time.')
            if body.deadline_date:date.fromisoformat(body.deadline_date)
            if body.status=='Verified open':
                if not body.evidence or not body.verified_at:raise ValueError('Verified open requires dated source-review evidence.')
                if effective_status(data)=='Unverified':raise ValueError('Invalid source verification time.')
        except ValueError as exc:raise HTTPException(422,str(exc))
        key=hashlib.sha256(data['application_url'].removesuffix('/apply').encode()).hexdigest()[:20]
        now=datetime.now(timezone.utc).isoformat()
        with LOCK:
            rows=read_catalog();old=next((r for r in rows if r.get('id')==key or r['application_url'].removesuffix('/apply')==data['application_url'].removesuffix('/apply')),None)
            changed=old is None or any(old.get(k)!=data.get(k) for k in ['title','location','status','deadline','deadline_date','deadline_note','details','evidence'])
            data.update(id=old.get('id',key) if old else key,first_seen_at=old.get('first_seen_at',now) if old else now,changed_at=now if changed else old.get('changed_at',now))
            if old:rows.remove(old)
            rows.append(data)
            STORE.parent.mkdir(parents=True,exist_ok=True)
            temp=STORE.with_suffix('.tmp');temp.write_text(json.dumps(rows,indent=2,ensure_ascii=False),encoding='utf-8');temp.replace(STORE)
        return {'id':data['id'],'changed':changed}

    @router.get('/api/opportunity-sources')
    def sources():
        path=ROOT/'config'/'opportunity-sources.json'
        return json.loads(path.read_text(encoding='utf-8-sig')) if path.exists() else []

    @router.get('/api/opportunity-briefing')
    def briefing():
        path=ROOT/'data'/'opportunities'/'reports'/'latest.json'
        if not path.exists():return {'is_baseline':True,'new_ids':[],'changed_ids':[]}
        data=json.loads(path.read_text(encoding='utf-8'))
        data.pop('hashes',None)
        data.pop('record_hashes',None)
        data['report_url']='/api/opportunity-reports/'+data['report_filename']
        return data

    @router.get('/api/opportunity-reports/{name}')
    def report_file(name:str):
        if not re.fullmatch(r'\d{4}-\d{2}-\d{2}T\d{2}-\d{2}-\d{2}Z\.md',name):raise HTTPException(404,'Report not found.')
        path=ROOT/'data'/'opportunities'/'reports'/name
        if not path.is_file():raise HTTPException(404,'Report not found.')
        return FileResponse(path,media_type='text/markdown',filename=name)
    return router
