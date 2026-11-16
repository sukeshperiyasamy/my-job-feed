"""Run local collection, optional tailoring, and the explicitly allowlisted queue.

No login credentials are accepted here. Browser blockers appear in the dashboard.
"""
import argparse
import json
import time
import requests

BASE='http://127.0.0.1:8000'

def request(method,path,body=None,timeout=240):
    response=requests.request(method,BASE+path,json=body,timeout=timeout)
    response.raise_for_status()
    return response.json()

def wait_collection():
    for _ in range(180):
        state=request('GET','/api/collection/status')
        if state.get('status')!='Running':return state
        time.sleep(2)
    raise RuntimeError('Collection still running after six minutes; inspect the dashboard.')

def cycle(score_new=False):
    summary={'watchlist':None,'discovery':[],'tailored':[],'application_queue':None}
    request('GET','/health')
    previous=request('GET','/api/collection/status')
    if previous.get('status')=='Running':wait_collection()
    request('POST','/api/watchlist/check')
    summary['watchlist']=wait_collection()
    for location in ['Chennai','Bengaluru','Visakhapatnam']:
        request('POST','/api/discovery/run',{'search_term':'Biomedical Engineer','location':location,'sites':['naukri'],'results_wanted':10})
        summary['discovery'].append({'location':location,**wait_collection()})
    if score_new:
        jobs=request('GET','/api/jobs?limit=1000')
        # Prioritize technical titles relevant to the verified profile. Scoring is not an application approval.
        keywords=['biomedical','medical device','firmware','embedded','software','python','research','sensor','validation','rag','full stack','react native']
        candidates=[j for j in jobs if j.get('match_score') is None and any(k in j['title'].lower() for k in keywords)]
        for job in candidates[:3]:
            try:
                outcome=request('POST',f"/api/jobs/{job['id']}/score")
                summary['tailored'].append({'id':job['id'],'title':job['title'],'score':outcome.get('match_score')})
            except Exception as exc:summary['tailored'].append({'id':job['id'],'error':str(exc)})
    summary['application_queue']=[]
    for _ in range(3):
        started=request('POST','/api/applications/run-approved')
        summary['application_queue'].append(started)
        if started.get('status')=='No eligible applications':break
        application_id=started.get('application_id')
        for _ in range(90):
            rows=request('GET','/api/applications')
            current=next((a for a in rows if a['id']==application_id),None)
            if not current:break
            run=current.get('automation',{})
            if run.get('waiting'):
                summary['application_queue'].append({'id':application_id,'status':current['state'],'needs_user':run.get('error')})
                return summary
            if not run.get('active'):
                summary['application_queue'].append({'id':application_id,'status':current['state'],'result':run.get('confirmation_text') or run.get('error')})
                break
            time.sleep(2)
        else:
            summary['application_queue'].append({'id':application_id,'status':'Still working; inspect dashboard'})
            break
    return summary

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--score-new',action='store_true',help='Tailor up to three new technical roles. This does not approve submissions.')
    args=parser.parse_args()
    print(json.dumps(cycle(args.score_new),indent=2))
