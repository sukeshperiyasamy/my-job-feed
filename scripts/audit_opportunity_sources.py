"""Reachability/coverage audit only. Never promotes a directory page to a vacancy."""
import concurrent.futures
import json
from datetime import datetime,timezone
from pathlib import Path
import requests
ROOT=Path(__file__).resolve().parents[1]

def audit():
    path=ROOT/'config'/'opportunity-sources.json'
    rows=json.loads(path.read_text(encoding='utf-8'))
    def check(row):
        checked=datetime.now(timezone.utc).isoformat()
        try:
            r=requests.get(row['url'],timeout=(4,10),headers={'User-Agent':'JobHunterSourceAudit/1.0'},stream=True)
            status=r.status_code;r.close()
            return {**row,'source_checked_at':checked,'http_status':status,'coverage':f'Source-page HTTP {status}; this does not verify any vacancy or eligibility'}
        except Exception as exc:
            return {**row,'source_checked_at':checked,'http_status':None,'coverage':'Source could not be retrieved; individual opening remains unverified','source_error':type(exc).__name__}
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:results=list(pool.map(check,rows))
    path.write_text(json.dumps(results,indent=2,ensure_ascii=False),encoding='utf-8')
    folder=ROOT/'data'/'opportunities'/'reports';folder.mkdir(parents=True,exist_ok=True)
    dest=folder/('source-audit-'+datetime.now(timezone.utc).strftime('%Y-%m-%dT%H-%M-%SZ')+'.json')
    dest.write_text(json.dumps(results,indent=2,ensure_ascii=False),encoding='utf-8')
    return {'targets':len(results),'http_200':sum(r.get('http_status')==200 for r in results),'audit_file':str(dest),'note':'Reachability only; not a comprehensive vacancy/admission review.'}
if __name__=='__main__':print(json.dumps(audit(),indent=2))
