"""Dashboard operations: async collection, watchlist, and resumable applications."""
import json
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal
from urllib.parse import urlsplit
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.exc import IntegrityError
from services.integration_bridge.models import Job, Application, ApplicationState, ExecutionLog, WatchedCompany
from services.application_engine.sessions import ApplicationSessions
from services.application_engine.portals import PORTALS
from services.application_engine.form_worker import load_json
from services.job_collector.careers import canonical_url, collect_careers

ROOT=Path(__file__).resolve().parents[2]

class Decision(BaseModel):
    application_id:int
    decision:Literal['prepare','approve','resume','cancel','reject','reset_after_check']
    use_saved_portal_resume:bool=False

class Discovery(BaseModel):
    search_term:str=Field(min_length=2,max_length=200)
    location:str=Field(default='India',max_length=120)
    sites:list[str]=Field(default_factory=lambda:['naukri'],min_length=1,max_length=4)
    results_wanted:int=Field(default=10,ge=1,le=30)

class CompanyInput(BaseModel):
    name:str=Field(min_length=1,max_length=255)
    careers_url:str
    region:Literal['Tamil Nadu','Bengaluru','Andhra Pradesh']
    sector:str='MedTech'
    company_type:str='Company'
    notes:str=''

class CompanyUpdate(BaseModel):
    enabled:bool

class AnswersInput(BaseModel):
    answers:dict[str,str|bool|int|float]

class PolicyInput(BaseModel):
    auto_submit_domains:list[str]=Field(default_factory=list,max_length=20)
    daily_submission_limit:int=Field(default=15,ge=1,le=30)

def create_operations(session_factory):
    router=APIRouter()
    runner=ApplicationSessions(session_factory)
    scan_lock=threading.Lock()
    task_lock=threading.Lock()
    tasks={}
    def log_task(task):
        with session_factory() as db:
            db.add(ExecutionLog(service='collection',level='ERROR' if task['status']=='Failed' else 'INFO',message=task['status'],details=task))
            db.commit()
    def save_jobs(records):
        created=0
        with session_factory() as db:
            for data in records:
                url=canonical_url(data['canonical_url'])
                if db.query(Job).filter(Job.canonical_url==url).first():continue
                db.add(Job(canonical_url=url,title=data['title'],company_name=data['company_name'],location=data.get('location'),description=data.get('description',''),source=data.get('source','company_careers'),work_arrangement=data.get('work_arrangement','Not specified'),status=ApplicationState.DISCOVERED))
                try:
                    db.commit()
                    created+=1
                except IntegrityError:
                    db.rollback()
        return created
    def start_task(kind,work):
        with task_lock:
            if not scan_lock.acquire(blocking=False):
                raise HTTPException(409,'A collection run is already active. Wait for it to finish.')
            task={'id':uuid.uuid4().hex,'kind':kind,'status':'Running','started_at':datetime.now(timezone.utc).isoformat(),'new_jobs':0,'results':[]}
            tasks[task['id']]=task
            log_task(task)
        def run():
            try:
                work(task)
                task['status']='Completed with warnings' if any(r.get('error') for r in task['results']) else 'Completed'
            except Exception as exc:
                task.update(status='Failed',error=str(exc))
            finally:
                task['finished_at']=datetime.now(timezone.utc).isoformat()
                log_task(task)
                scan_lock.release()
        threading.Thread(target=run,daemon=True).start()
        return task

    # Add seeds once; do not overwrite user-managed settings on future starts.
    with session_factory() as db:
        for data in load_json('medtech-watchlist.json',[]):
            if not db.query(WatchedCompany).filter_by(careers_url=data['careers_url']).first():
                db.add(WatchedCompany(**data))
        # A process restart never silently replays an in-flight submission.
        for record in db.query(Application).filter_by(state=ApplicationState.APPLYING).all():
            record.state=ApplicationState.MANUAL_ACTION_REQUIRED
            db.add(ExecutionLog(service='application',level='WARNING',message='Service restarted during an application.',details={'application_id':record.id,'outcome':{'status':'Manual Action Required','error':'Service restarted during an application. Verify the portal before any retry.','submission_attempted':True}}))
        db.commit()

    @router.get('/api/portals')
    def portals():
        from jobspy.model import Site
        installed={s.value for s in Site}
        return [{**p,'search_available':p['search'] and p['id'] in installed} for p in PORTALS]

    @router.get('/api/answers')
    def answers():
        return load_json('application-answers.json',{'answers':{}})

    @router.get('/api/application-policy')
    def application_policy():
        return load_json('application-policy.json',{})

    @router.put('/api/application-policy')
    def update_policy(body:PolicyInput):
        import re
        blocked={'linkedin.com','www.linkedin.com','indeed.com','www.indeed.com','in.indeed.com','glassdoor.com','www.glassdoor.com'}
        domains=list(dict.fromkeys(d.strip().lower() for d in body.auto_submit_domains))
        if any(not re.fullmatch(r'(?:[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\.)+[a-z]{2,}',d) or d in blocked or any(d.endswith('.'+x) for x in ['linkedin.com','indeed.com','glassdoor.com']) for d in domains):
            raise HTTPException(422,'Use exact employer hostnames, without URLs or wildcards. LinkedIn, Indeed and Glassdoor applications use employer links.')
        policy=load_json('application-policy.json',{})
        policy.update(auto_submit_domains=domains,daily_submission_limit=body.daily_submission_limit)
        path=ROOT/'config'/'application-policy.json'
        temp=path.with_suffix('.tmp');temp.write_text(json.dumps(policy,indent=2),encoding='utf-8');temp.replace(path)
        return policy

    @router.post('/api/applications/run-approved')
    def run_approved_queue():
        policy=load_json('application-policy.json',{})
        allowed=policy.get('auto_submit_domains',[])
        if runner.active:return {'status':'Browser active','application_id':runner.active['id']}
        with session_factory() as db:
            ids=[a.id for a in db.query(Application).filter_by(state=ApplicationState.PENDING_APPROVAL).order_by(Application.created_at).all() if (urlsplit(a.job.canonical_url).hostname or '').lower() in allowed]
        for application_id in ids:
            try:return runner.start(application_id,approved=False)
            except ValueError:continue
        return {'status':'No eligible applications','message':'Only pending applications on your exact auto-submit allowlist can run unattended.'}

    @router.put('/api/answers')
    def update_answers(body:AnswersInput):
        if len(body.answers)>100 or any(len(k)>500 or len(str(v))>5000 for k,v in body.answers.items()):
            raise HTTPException(422,'Too many or oversized answers.')
        path=ROOT/'config'/'application-answers.json'
        temp=path.with_suffix('.tmp')
        temp.write_text(json.dumps({'answers':body.answers},indent=2),encoding='utf-8')
        temp.replace(path)
        return {'status':'Saved'}

    @router.get('/api/watchlist')
    def watchlist():
        with session_factory() as db:
            return [{k:getattr(c,k) for k in ['id','name','careers_url','region','sector','company_type','evidence_url','notes','enabled','last_checked_at','last_status','last_error','last_new_jobs','details']} for c in db.query(WatchedCompany).order_by(WatchedCompany.region,WatchedCompany.name).all()]

    @router.post('/api/watchlist')
    def add_company(body:CompanyInput):
        values=body.model_dump()
        values['careers_url']=canonical_url(body.careers_url)
        with session_factory() as db:
            if db.query(WatchedCompany).filter_by(careers_url=values['careers_url']).first():raise HTTPException(409,'Company career page already watched.')
            c=WatchedCompany(**values)
            db.add(c);db.commit();db.refresh(c)
            return {'id':c.id}

    @router.patch('/api/watchlist/{company_id}')
    def update_company(company_id:int,body:CompanyUpdate):
        with session_factory() as db:
            c=db.get(WatchedCompany,company_id)
            if not c:raise HTTPException(404,'Company not found.')
            c.enabled=body.enabled;db.commit()
            return {'status':'Saved'}

    @router.post('/api/watchlist/check')
    def check_watchlist():
        def collect(task):
            with session_factory() as db:
                companies=[{'id':c.id,'name':c.name,'careers_url':c.careers_url} for c in db.query(WatchedCompany).filter_by(enabled=True).all()]
            for company in companies:
                try:
                    result=collect_careers(company)
                    created=save_jobs(result['jobs'])
                    task['new_jobs']+=created
                    with session_factory() as db:
                        c=db.get(WatchedCompany,company['id'])
                        changed=c.content_hash is not None and c.content_hash!=result['content_hash']
                        c.content_hash=result['content_hash'];c.last_checked_at=datetime.now(timezone.utc)
                        c.last_status=result['status'];c.last_new_jobs=created;c.last_error=None
                        c.details={'changed':changed,'links':result['links'],'note':result['note'],'jobs_found':len(result['jobs'])}
                        db.commit()
                    task['results'].append({'name':company['name'],'new_jobs':created,'changed':changed,'status':result['status']})
                except Exception as exc:
                    task['results'].append({'name':company['name'],'error':str(exc)})
                    with session_factory() as db:
                        c=db.get(WatchedCompany,company['id']);c.last_checked_at=datetime.now(timezone.utc);c.last_status='Check failed';c.last_error=str(exc);c.last_new_jobs=0;db.commit()
        return start_task('watchlist',collect)

    @router.post('/api/discovery/run')
    def discovery(body:Discovery):
        available={p['id'] for p in portals() if p['search_available']}
        if not set(body.sites)<=available:raise HTTPException(422,'Choose a portal with public search support. HirePro requires employer-specific links.')
        def collect(task):
            from services.job_collector.collector import run_jobspy_discovery
            for site in dict.fromkeys(body.sites):
                try:
                    records=run_jobspy_discovery(search_term=body.search_term,location=body.location,sites=[site],results_wanted=body.results_wanted,raise_errors=True)
                    count=save_jobs(records);task['new_jobs']+=count
                    task['results'].append({'name':site,'found':len(records),'new_jobs':count,'status':'No public results; site may require login or may have blocked search.' if not records else 'Collected'})
                except Exception as exc:task['results'].append({'name':site,'error':str(exc)})
        return start_task('discovery',collect)

    @router.get('/api/collection/status')
    def collection_status():
        with task_lock:
            running=[t for t in tasks.values() if t['status']=='Running']
        if running:return running[-1]
        with session_factory() as db:
            last=db.query(ExecutionLog).filter_by(service='collection').order_by(ExecutionLog.id.desc()).first()
            task=dict(last.details) if last else {'status':'Not run','results':[]}
            if task['status']=='Running':task.update(status='Interrupted',error='Service restarted. Start collection again.')
            return task

    @router.post('/api/applications/decide')
    def decide(body:Decision):
        try:
            if body.decision in ['resume','cancel']:return runner.command(body.application_id,body.decision)
            if body.decision in ['prepare','approve']:
                return runner.start(body.application_id,approved=body.decision=='approve',use_saved_portal_resume=body.use_saved_portal_resume)
            with session_factory() as db:
                record=db.get(Application,body.application_id)
                if not record:raise HTTPException(404,'Application not found.')
                if record.state==ApplicationState.SUBMITTED:raise HTTPException(409,'Already submitted. Duplicate prevented.')
                if runner.status(record.id).get('active'):raise HTTPException(409,'Close the live browser session first.')
                if body.decision=='reset_after_check':
                    record.state=ApplicationState.PENDING_APPROVAL
                    db.add(ExecutionLog(service='application',message='User verified portal: not submitted.',details={'application_id':record.id,'outcome':{'status':'Pending Approval','submission_attempted':False,'error':'User verified the portal and reset this application.'}}))
                else:record.state=ApplicationState.SKIPPED
                db.commit()
                return {'status':record.state.value}
        except ValueError as exc:raise HTTPException(409,str(exc))

    return router,runner
