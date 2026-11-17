from datetime import datetime,timezone
from urllib.parse import urlsplit
from fastapi import APIRouter,HTTPException
from pydantic import BaseModel,Field
from sqlalchemy import func,null
from services.job_collector import extended_search as source
from services.job_collector.matching import campaign_config
from services.integration_bridge.models import Job,JobVerification,ApplicationState,ExecutionLog

class SearchInput(BaseModel):
    campaign_ids:list[str]=Field(default_factory=list,max_length=7)
    max_searches:int=Field(default=6,ge=1,le=8)
    results_per_search:int=Field(default=25,ge=1,le=50)
    days:int=Field(default=30,ge=1,le=90)
    remote:bool=False

def extended_router(db_factory,start_task):
    router=APIRouter(prefix='/api/extended-search')
    @router.get('')
    def info():
        with db_factory() as db:
            counts=[{'source':s,'saved':n} for s,n in db.query(Job.source,func.count(Job.id)).group_by(Job.source).all()]
            latest=None
            for log in db.query(ExecutionLog).filter(ExecutionLog.service=='collection').order_by(ExecutionLog.id.desc()).limit(100):
                if (log.details or {}).get('kind')=='extended_search':latest=log.details;break
        return {'integration':source.health(),'campaigns':campaign_config()['campaigns'],'counts':counts,'latest':latest,'sources':[
            {'name':'FreeHire','mode':'API discovery','url':'https://freehire.me','note':'Borrowed search/parser from ai-job-search. Each scan is bounded, cached and screened; employer availability remains unchecked.'},
            {'name':'LinkedIn','mode':'Manual search','url':'https://www.linkedin.com/jobs/search/?keywords=junior%20software%20engineer&location=Bengaluru%2C%20India','note':'No scheduled scraper or automated applications. Aggregated FreeHire results may link to LinkedIn.'},
            {'name':'Jobindex / Jobnet / Jobbank / Jobdanmark','mode':'Not enabled','url':'https://github.com/ai-job-search-dev/ai-job-search','note':'The four remaining tools target Denmark and do not improve the current India search.'}]}
    @router.post('/run')
    def run(body:SearchInput):
        if set(body.campaign_ids)-{c['id'] for c in campaign_config()['campaigns']}:raise HTTPException(422,'Unknown career lane.')
        if not source.health().get('ready'):raise HTTPException(409,'Extended discovery runtime needs setup.')
        queries=source.choose_queries(body.campaign_ids,body.max_searches)
        def work(task):
            for query in queries:
                try:
                    data=source.search(query,body.days,body.remote,body.results_per_search)
                    counts={'fetched':len(data['results']),'new_jobs':0,'duplicates':0,'excluded':0,'invalid':0,'needs_review':0,'potential_matches':0,'manual_links':0,'possible_duplicates':0}
                    with db_factory() as db:
                        existing={source.posting_key(j.canonical_url):j for j in db.query(Job).all()}
                        pairs={(j.company_name.strip().lower(),j.title.strip().lower()) for j in existing.values()}
                        for raw in data['results']:
                            try:row=source.normalize(raw,body.campaign_ids)
                            except (ValueError,TypeError):counts['invalid']+=1;continue
                            if row is None or row['screening']['status']=='outside_target':counts['excluded']+=1;continue
                            key=source.posting_key(row['canonical_url']);job=existing.get(key)
                            if job:counts['duplicates']+=1
                            else:
                                pair=(row['company_name'].strip().lower(),row['title'].strip().lower())
                                possible=pair in pairs
                                row['provenance']['possible_duplicate']=possible
                                counts['possible_duplicates']+=int(possible)
                                job=Job(**{k:v for k,v in row.items() if k not in ['screening','provenance']},status=ApplicationState.DISCOVERED)
                                if not row.get('salary_currency'):job.salary_currency=null()
                                db.add(job);db.flush();existing[key]=job;pairs.add(pair);counts['new_jobs']+=1
                            counts['needs_review' if row['screening']['status']=='needs_review' else 'potential_matches']+=1
                            manual=urlsplit(job.canonical_url).hostname in ['linkedin.com','www.linkedin.com']
                            counts['manual_links']+=int(manual)
                            evidence=db.get(JobVerification,job.id)
                            if evidence is None:evidence=JobVerification(job_id=job.id,availability='unchecked');db.add(evidence)
                            # Preserve original publisher attribution if another collector saved it first.
                            if not evidence.provider:
                                evidence.provider='freehire';evidence.source_name='FreeHire';evidence.source_url=job.canonical_url
                            evidence.collected_at=datetime.fromisoformat(data['collected_at'])
                            evidence.details={**(evidence.details or {}),'freehire':row['provenance'],'discovery_query':query,'manual_source_link':manual}
                        db.commit()
                    task['new_jobs']+=counts['new_jobs']
                    task['results'].append({'name':query,'status':'Search completed',**counts,'cached':data['cached'],'collected_at':data['collected_at'],'total_reported':data.get('meta',{}).get('total'),'partial':True})
                except Exception as e:task['results'].append({'name':query,'error':str(e)})
        return start_task('extended_search',work,{'coverage':'Global remote' if body.remote else 'India','queries':queries})
    return router
