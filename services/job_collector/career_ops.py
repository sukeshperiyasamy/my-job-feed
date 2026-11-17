"""Bounded subprocess bridge to pinned Career Ops read-only providers."""
import hashlib
import json
import os
import re
import shutil
import subprocess
import threading
from datetime import datetime,timezone,timedelta
from pathlib import Path
from urllib.parse import urlsplit
import psutil
from services.job_collector.careers import canonical_url
from services.job_collector.matching import assess_job,campaign_config

ROOT=Path(__file__).resolve().parents[2]
REPO=ROOT/'apps'/'career-ops'
DATA=ROOT/'data'/'career-ops'
CONFIG=ROOT/'config'/'career-ops.json'
CUSTOM=DATA/'sources.json'
LOCK=threading.RLock()
PROVIDERS=['greenhouse','lever','ashby','smartrecruiters','recruitee','himalayas','remotive','weworkremotely']

def read_config():return json.loads(CONFIG.read_text(encoding='utf-8'))
def sources():
    with LOCK:
        return read_config()['sources']+(json.loads(CUSTOM.read_text(encoding='utf-8')) if CUSTOM.exists() else [])
def run_bridge(payload,timeout=110):
    node=shutil.which('node')
    if not node or not (REPO/'package.json').exists():raise ValueError('Career Ops is not installed. Run scripts/install_career_ops.ps1.')
    env={**os.environ,'CAREER_OPS_ROOT':str(DATA),'CAREER_OPS_DATA_DIR':str(DATA),'NODE_OPTIONS':''}
    process=subprocess.Popen([node,str(ROOT/'scripts'/'career_ops_bridge.mjs')],cwd=ROOT,env=env,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,encoding='utf-8',creationflags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0)
    try:out,err=process.communicate(json.dumps(payload),timeout=timeout)
    except subprocess.TimeoutExpired:
        # Only descendants of this explicitly launched adapter; never attach to user browsers.
        try:
            for child in psutil.Process(process.pid).children(recursive=True):
                try:child.kill()
                except psutil.Error:pass
        finally:
            process.kill();process.communicate()
        raise ValueError('Career Ops timed out; no complete result was imported.')
    try:result=json.loads(out)
    except ValueError:raise ValueError('Career Ops returned an unreadable result. Check its installation.')
    if process.returncode or result.get('error'):raise ValueError(result.get('error') or err[-600:])
    return result
def status():
    config=read_config()
    try:
        state=run_bridge({'operation':'health'},timeout=15)
        commit=subprocess.check_output(['git','-C',str(REPO),'rev-parse','HEAD'],text=True,timeout=5,creationflags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0).strip()
        if commit!=config['commit']:return {'ready':False,'error':'Installed revision differs from the tested pin. Run the install script in a clean checkout.','commit':commit}
        return {**state,'commit':commit,'repository':config['repository'],'mode':'Read-only discovery and availability checks'}
    except (ValueError,OSError,subprocess.SubprocessError) as exc:return {'ready':False,'error':str(exc),'repository':config['repository']}
def add_source(name,provider,url):
    if provider not in PROVIDERS:raise ValueError('Unsupported Career Ops provider.')
    clean=canonical_url(url)
    if not name.strip():raise ValueError('Enter an employer/source name.')
    run_bridge({'operation':'inspect','source':{'name':name,'provider':provider,'url':clean}},timeout=15)
    with LOCK:
        if any(s['provider']==provider and (provider in ['himalayas','remotive','weworkremotely'] or canonical_url(s['url'])==clean) for s in sources()):raise ValueError('That source is already connected.')
        saved=json.loads(CUSTOM.read_text(encoding='utf-8')) if CUSTOM.exists() else []
        row={'id':'custom-'+hashlib.sha256((provider+'|'+clean).encode()).hexdigest()[:16],'name':name.strip(),'provider':provider,'url':clean,'default':False}
        saved.append(row);CUSTOM.parent.mkdir(parents=True,exist_ok=True)
        temp=CUSTOM.with_suffix('.tmp');temp.write_text(json.dumps(saved,indent=2),encoding='utf-8');temp.replace(CUSTOM)
        return row
def collect_source(source):
    ttl={'remotive':21600,'himalayas':86400,'weworkremotely':3600}.get(source['provider'],900)
    key=hashlib.sha256((source['provider']+'|'+('public-feed' if source['provider'] in ['himalayas','remotive','weworkremotely'] else source['url'])).encode()).hexdigest()
    path=DATA/'cache'/(key+'.json');now=datetime.now(timezone.utc)
    if path.exists():
        try:
            saved=json.loads(path.read_text(encoding='utf-8'))
            if now-datetime.fromisoformat(saved['collected_at'])<timedelta(seconds=ttl):return {**saved,'cached':True}
        except (ValueError,KeyError):pass
    result=run_bridge({'operation':'collect','source':source})
    result.update(collected_at=now.isoformat(),cached=False)
    path.parent.mkdir(parents=True,exist_ok=True);temp=path.with_suffix('.tmp');temp.write_text(json.dumps(result),encoding='utf-8');temp.replace(path)
    return result
def posting_key(url):
    url=canonical_url(url)
    p=urlsplit(url)
    if p.hostname in ['jobs.lever.co','jobs.eu.lever.co'] and p.path.endswith('/apply'):url=url.removesuffix('/apply')
    if p.hostname=='jobs.ashbyhq.com' and p.path.endswith('/application'):url=url.removesuffix('/application')
    return url
def normalize_job(raw,source,selected_campaigns=None):
    title=str(raw.get('title') or '').strip()
    if not title or not raw.get('url'):return None
    if not re.search(r'engineer|develop|research|scientist|analyst|\b(?:ai|ml|qa|jrf|intern|trainee)\b|test|verification|validation|firmware|embedded|software|biomedical|instrument|technical support|application specialist|product.*(?:manager|associate)|quality|regulatory|biosensor|project associate|\b(?:ui|ux|hci)\b',title,re.I):return None
    url=canonical_url(raw['url']);description=str(raw.get('description') or '')
    if raw.get('eligibilityText'):description+='\nCountry eligibility from source: '+str(raw['eligibilityText'])
    location=str(raw.get('location') or '')
    if source['provider'] in ['himalayas','remotive','weworkremotely'] and 'remote' not in location.lower():location='Remote · '+(location or 'Country not specified')
    screening=assess_job(title,description,location)
    lanes={c['id'] for c in screening['campaigns']}
    if not lanes.intersection(selected_campaigns or [c['id'] for c in campaign_config()['campaigns']]):return None
    if lanes=={'internships'}:return None
    place=location.lower()
    indian=str(raw.get('country') or '').lower() in ['in','ind','india'] or any(k in place for k in ['india','bengaluru','bangalore','chennai','coimbatore','mysuru','mysore','karur','hyderabad','pune','delhi','visakhapatnam','tamil nadu','karnataka','andhra pradesh'])
    # Remote is a lead for review, never proof of hiring from India.
    remote=raw.get('workplaceType')=='remote' or any(k in place for k in ['remote','worldwide','anywhere'])
    if place and not indian and not remote:return None
    if remote and not indian and str(raw.get('location') or '').strip().lower() in ['united states','usa','us','canada','united kingdom','uk','europe','germany']:return None
    posted=None
    if isinstance(raw.get('postedAt'),(int,float)):
        try:posted=datetime.fromtimestamp(raw['postedAt']/1000,timezone.utc)
        except (ValueError,OverflowError,OSError):pass
    salary=raw.get('salary') or {}
    return {'canonical_url':url,'title':title,'company_name':str(raw.get('company') or source['name']),'location':location or 'Not stated','description':description,'source':'career_ops:'+source['provider'],'work_arrangement':raw.get('workplaceType') or raw.get('employmentType') or 'Not specified','source_job_id':raw.get('externalId'),'posting_date':posted,'salary_min':salary.get('min'),'salary_max':salary.get('max'),'salary_currency':salary.get('currency'),'screening':screening,'provenance':{'native_identity':raw.get('listingIdentity'),'salary':salary,'eligibility_text':raw.get('eligibilityText'),'source_id':source['id']}}
