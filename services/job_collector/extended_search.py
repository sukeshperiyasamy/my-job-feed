"""FreeHire discovery through the borrowed AI Job Search parser/search implementation."""
import hashlib,json,os,shutil,subprocess,threading
from datetime import datetime,timezone,timedelta
from pathlib import Path
from services.job_collector.career_ops import normalize_job,posting_key
from services.job_collector.matching import campaign_config,search_plan

ROOT=Path(__file__).resolve().parents[2]
DATA=ROOT/'data'/'extended-search'
LOCK=threading.Lock()
def bridge(payload):
    node=shutil.which('node')
    if not node:raise ValueError('Node 24 or newer is required for extended discovery.')
    result=subprocess.run([node,str(ROOT/'scripts/ai_job_search_bridge.mjs')],input=json.dumps(payload),capture_output=True,text=True,encoding='utf-8',timeout=40,cwd=ROOT,env={**os.environ,'NODE_OPTIONS':''},creationflags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0)
    if result.returncode:
        error=result.stderr.strip().splitlines()
        try:message=json.loads(error[-1]).get('error')
        except (ValueError,IndexError):message='The source could not be reached or parsed.'
        raise ValueError(message)
    data=json.loads(result.stdout)
    if payload['operation']=='search' and not isinstance(data.get('results'),list):raise ValueError('Invalid source response; no jobs imported.')
    return data
def health():
    try:return bridge({'operation':'health'})
    except (ValueError,OSError,subprocess.SubprocessError) as e:return {'ready':False,'error':str(e)}
def choose_queries(campaign_ids,limit):
    plan=search_plan(campaign_config(),campaign_ids)
    # FreeHire searches India as a country: repeated city variants would duplicate requests.
    unique=list(dict.fromkeys(p['search_term'] for p in plan))
    with LOCK:
        path=DATA/'rotation.json';state=json.loads(path.read_text()) if path.exists() else {}
        key='|'.join(sorted(campaign_ids));cursor=state.get(key,0)
        queries=[unique[(cursor+i)%len(unique)] for i in range(min(limit,len(unique)))]
        state[key]=(cursor+len(queries))%len(unique)
        DATA.mkdir(parents=True,exist_ok=True);temp=path.with_suffix('.tmp');temp.write_text(json.dumps(state));temp.replace(path)
    return queries
def search(query,days,remote,limit):
    payload={'operation':'search','query':query,'days':days,'remote':remote,'limit':limit}
    key=hashlib.sha256(json.dumps(payload,sort_keys=True).encode()).hexdigest()
    path=DATA/'cache'/(key+'.json');now=datetime.now(timezone.utc)
    if path.exists():
        saved=json.loads(path.read_text(encoding='utf-8'))
        if now-datetime.fromisoformat(saved['collected_at'])<timedelta(minutes=15):return {**saved,'cached':True}
    data=bridge(payload);data.update(collected_at=now.isoformat(),cached=False)
    path.parent.mkdir(parents=True,exist_ok=True);temp=path.with_suffix('.tmp');temp.write_text(json.dumps(data),encoding='utf-8');temp.replace(path)
    return data
def normalize(raw,campaigns):
    countries=[str(c).lower() for c in raw.get('countries',[])]
    row=normalize_job({'title':raw.get('title'),'company':raw.get('company'),'url':raw.get('url'),'location':raw.get('location'),'description':raw.get('description') or '', 'country':'IN' if 'in' in countries else '', 'workplaceType':raw.get('work_mode'),'externalId':raw.get('id'),'eligibilityText':('Source country facets: '+', '.join(countries)) if countries else None}, {'id':'freehire','provider':'freehire','name':'FreeHire'},campaigns)
    if row:
        row['source']='ai_job_search:freehire'
        row['provenance'].update(countries=countries,aggregator_id=raw.get('id'),aggregator_posted_date=raw.get('date'),skills=raw.get('skills',[]))
        if raw.get('date'):
            try:row['posting_date']=datetime.fromisoformat(raw['date']).replace(tzinfo=timezone.utc)
            except ValueError:pass
    return row
