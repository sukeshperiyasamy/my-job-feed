"""Publish a durable baseline/diff; verification comes from reviewed source records."""
import hashlib
import json
import sys
from datetime import datetime,timezone
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from services.integration_bridge.opportunities import read_catalog,effective_status

ROOT=Path(__file__).resolve().parents[1]
def publish():
    rows=read_catalog()
    folder=ROOT/'data'/'opportunities'/'reports';folder.mkdir(parents=True,exist_ok=True)
    latest=folder/'latest.json'
    previous=json.loads(latest.read_text(encoding='utf-8')) if latest.exists() else None
    baseline=previous is None or 'record_hashes' not in previous
    record_hashes={}
    hashes={}
    new,changed=[],[]
    for r in rows:
        key=r['application_url'].rstrip('/').removesuffix('/apply')
        meaningful={k:r.get(k) for k in ['title','organization','location','deadline','deadline_date','deadline_note','details']}
        meaningful['status']=effective_status(r)
        fingerprint=hashlib.sha256(json.dumps(meaningful,sort_keys=True).encode()).hexdigest()
        hashes[key]=fingerprint
        record_hashes[r['id']]=fingerprint
        if not baseline:
            if r['id'] not in previous.get('record_hashes',{}):new.append(r['id'])
            elif previous['record_hashes'][r['id']]!=fingerprint:changed.append(r['id'])
    now=datetime.now(timezone.utc)
    stamp=now.strftime('%Y-%m-%dT%H-%M-%SZ')
    filename=stamp+'.md'
    lines=['# Career and research source review', '', 'Checked: '+now.isoformat(), '', 'Initial baseline; no earlier comparable report.' if baseline else 'Changes compared with '+previous['generated_at'], '']
    for category in ['internship','job','research','remote']:
        group=[r for r in rows if r['category']==category]
        verified=[r for r in group if effective_status(r)=='Verified open']
        added=[r for r in verified if r['id'] in new]
        lines.extend(['## '+category.title(),''])
        if baseline:lines.append(f'Baseline: {len(verified)} verified-open records; no claim that these were newly posted.')
        elif not added:lines.append('No new verified openings.')
        else:lines.append(f'{len(added)} new verified openings since the previous report.')
        for r in group:
            d=r.get('details',{})
            deadline=r.get('deadline') or r.get('deadline_note','Not published')
            lines.extend(['',f"- **{r['organization']} — {r['title']}** · {effective_status(r)}",f"  Location: {r['location']}. Deadline: {deadline}.",f"  Pay/funding: {d.get('pay') or d.get('funding') or 'Undisclosed'}.",f"  Fit/next action: {d.get('fit','Check the original requirements.')}",f"  [Original source]({r['source_url']}) · [Application/posting]({r['application_url']})"])
        lines.append('')
    sources=sorted({r['source_url'] for r in rows})
    lines.extend(['## Coverage and limits','','This is a partial initial review, not an exhaustive search of all IITs, NITs or employers. The directory contains nationwide and company watch targets, which are not verified vacancies. Search-index-only leads are marked unverified. No salary, degree equivalence or funding waiver is inferred.','',f'{len(sources)} source URLs represented in this review.',''])
    lines.extend('- '+s for s in sources)
    lines.extend(['','## Three-month preparation','','Month 1: C/C++, Python tests and signal processing. Month 2: a documented ESP32 sensing project with verification/traceability practice and introductory IEC 62304/ISO 14971 study. Month 3: polished SERS/software portfolios, written-test practice and targeted research statements. Do not list standards study or ComfyUI/media automation as medical regulatory experience.'])
    (folder/filename).write_text('\n'.join(lines),encoding='utf-8')
    meta={'generated_at':now.isoformat(),'is_baseline':baseline,'new_ids':new,'changed_ids':changed,'hashes':hashes,'record_hashes':record_hashes,'source_urls':sources,'report_filename':filename,'coverage_note':'Partial source review; nationwide/company directory coverage is not a claim that all targets were checked.'}
    latest.write_text(json.dumps(meta,indent=2),encoding='utf-8')
    return meta
if __name__=='__main__':print(json.dumps(publish(),indent=2))
