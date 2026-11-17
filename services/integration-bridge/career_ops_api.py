"""Career Ops dashboard routes using the existing single collection queue."""
from datetime import datetime,timezone
from fastapi import APIRouter,HTTPException
from pydantic import BaseModel,Field
from services.integration_bridge.models import Job,JobVerification,ApplicationState
from services.job_collector import career_ops
from services.job_collector.matching import campaign_config

class SourceInput(BaseModel):
    name:str=Field(min_length=1,max_length=120)
    provider:str
    url:str=Field(max_length=2048)
class ScanInput(BaseModel):
    source_ids:list[str]=Field(default_factory=list,max_length=6)
    campaign_ids:list[str]=Field(default_factory=list,max_length=7)
    max_jobs_per_source:int=Field(default=50,ge=1,le=100)
    exclude_outside_target:bool=True
class CheckInput(BaseModel):
    job_ids:list[int]=Field(min_length=1,max_length=5)
    browser_fallback:bool=False

def create_career_ops_router(db_factory,start_task):
    router=APIRouter()
    @router.get('/api/career-ops')
    def info():return {'integration':career_ops.status(),'sources':career_ops.sources(),'providers':career_ops.PROVIDERS,
        'note':'Read-only public-source discovery. A listed job is not confirmed eligible. Availability checks do not approve or submit applications.'}
    @router.post('/api/career-ops/sources')
    def add_source(body:SourceInput):
        try:return career_ops.add_source(body.name,body.provider,body.url)
        except ValueError as exc:raise HTTPException(422,str(exc))
    @router.post('/api/career-ops/scan')
    def scan(body:ScanInput):
        all_sources=career_ops.sources();ids=list(dict.fromkeys(body.source_ids or [s['id'] for s in all_sources if s.get('default')]))
        selected=[s for s in all_sources if s['id'] in ids]
        if not ids or set(ids)-{s['id'] for s in all_sources}:raise HTTPException(422,'Choose connected Career Ops sources.')
        if set(body.campaign_ids)-{c['id'] for c in campaign_config()['campaigns']}:raise HTTPException(422,'Unknown career lane.')
        if not career_ops.status().get('ready'):raise HTTPException(409,'Career Ops is not ready. Inspect integration status.')
        def collect(task):
            for source in selected:
                try:
                    result=career_ops.collect_source(source);created=duplicates=filtered=kept=0
                    with db_factory() as db:
                        existing={career_ops.posting_key(j.canonical_url):j.id for j in db.query(Job).all()}
                        for raw in result['jobs']:
                            try:row=career_ops.normalize_job(raw,source,body.campaign_ids)
                            except (ValueError,TypeError):filtered+=1;continue
                            if row is None or body.exclude_outside_target and row['screening']['status']=='outside_target':filtered+=1;continue
                            if kept>=body.max_jobs_per_source:break
                            key=career_ops.posting_key(row['canonical_url']);job=db.get(Job,existing[key]) if key in existing else None
                            if job is None:
                                job=Job(**{k:v for k,v in row.items() if k not in ['screening','provenance']},status=ApplicationState.DISCOVERED)
                                db.add(job);db.flush();existing[key]=job.id;created+=1
                            else:
                                duplicates+=1
                                if not job.description:job.description=row['description']
                            evidence=db.get(JobVerification,job.id)
                            if evidence is None:evidence=JobVerification(job_id=job.id,availability='unchecked');db.add(evidence)
                            evidence.provider=source['provider'];evidence.source_name=source['name']
                            evidence.source_url=row['canonical_url'] if source['provider'] in ['himalayas','remotive','weworkremotely'] else source['url']
                            evidence.collected_at=datetime.fromisoformat(result['collected_at']);evidence.details={**(evidence.details or {}),**row['provenance']}
                            kept+=1
                        db.commit()
                    task['new_jobs']+=created
                    task['results'].append({'name':source['name'],'status':'Imported relevant leads','found':result['fetched'],'kept':kept,'new_jobs':created,'duplicates':duplicates,'filtered':filtered,'partial':result.get('partial',False) or kept>=body.max_jobs_per_source,'cached':result.get('cached',False),'collected_at':result['collected_at'],'note':result.get('note')})
                except Exception as exc:task['results'].append({'name':source['name'],'error':str(exc)})
        return start_task('career_ops',collect)
    @router.post('/api/career-ops/check')
    def check(body:CheckInput):
        with db_factory() as db:
            jobs=[{'id':j.id,'title':j.title,'url':j.canonical_url} for j in db.query(Job).filter(Job.id.in_(body.job_ids)).all()]
        if len(jobs)!=len(set(body.job_ids)):raise HTTPException(404,'One or more jobs were not found.')
        if not career_ops.status().get('ready'):raise HTTPException(409,'Career Ops is not ready.')
        def work(task):
            for job in jobs:
                try:
                    result=career_ops.run_bridge({'operation':'verify','url':job['url'],'browser_fallback':body.browser_fallback},timeout=85)
                    if result.get('result') not in ['active','expired','uncertain']:raise ValueError('Invalid availability verdict.')
                except Exception as exc:result={'result':'uncertain','reason':str(exc),'code':'check_failed','method':'adapter'}
                with db_factory() as db:
                    record=db.get(JobVerification,job['id'])
                    if record is None:record=JobVerification(job_id=job['id']);db.add(record)
                    if record.availability=='expired' and result['result']=='uncertain':
                        record.reason='Last definitive check reported expired. Recheck uncertain: '+str(result.get('reason',''))
                    else:
                        record.availability=result['result'];record.checked_at=datetime.now(timezone.utc);record.reason=result.get('reason')
                    record.details={**(record.details or {}),'check_code':result.get('code'),'check_method':result.get('method'),'last_check_result':result['result'],'last_check_at':datetime.now(timezone.utc).isoformat()};db.commit()
                task['results'].append({'name':job['title'],'job_id':job['id'],'status':result['result'],'reason':result.get('reason')})
        return start_task('career_ops_check',work)
    return router
