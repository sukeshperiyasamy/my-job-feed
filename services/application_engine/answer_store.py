"""User-provided answers and durable unanswered form questions. No inferred answers."""
import hashlib
import json
import re
import threading
from datetime import datetime,timezone
from pathlib import Path
from urllib.parse import urlsplit

ROOT=Path(__file__).resolve().parents[2]
STORE=ROOT/'data'/'application-profile'/'answers.json'
QUESTIONS=ROOT/'data'/'application-profile'/'questions.json'
LOCK=threading.RLock()

def normalize(value):return re.sub(r'[^a-z0-9+#]+',' ',str(value).lower()).strip()
def now():return datetime.now(timezone.utc).isoformat()
def read(path):return json.loads(path.read_text(encoding='utf-8')) if path.exists() else []
def write(path,data):
    path.parent.mkdir(parents=True,exist_ok=True)
    temp=path.with_suffix('.tmp');temp.write_text(json.dumps(data,indent=2,ensure_ascii=False),encoding='utf-8');temp.replace(path)
def restricted(label):return bool(re.search(r'password|passcode|one.time.code|\botp\b|captcha|security.code|credit.card|bank.account|aadhaar|aadhar|passport.number|social.security',label,re.I))
def consent(label,kind=''):
    return kind=='checkbox' or bool(re.search(r'consent|agree|certify|declar|privacy|terms|attest|signature',label,re.I))
def scope_key(url):
    p=urlsplit(url)
    if p.scheme not in ['http','https'] or not p.hostname or p.username or p.password:raise ValueError('A valid application URL is required for scoped answers.')
    # Shared ATS hosts have separate employer boards.
    path=p.path.strip('/').split('/')
    board=('/'+path[0]) if p.hostname in ['jobs.lever.co','jobs.eu.lever.co','boards.greenhouse.io','boards.eu.greenhouse.io','job-boards.greenhouse.io','job-boards.eu.greenhouse.io','jobs.ashbyhq.com'] and path[0] else ''
    return p.hostname.lower()+board
def application_key(url):
    from services.job_collector.careers import canonical_url
    return canonical_url(url)
def find_answer(label,url,kind='text'):
    key=normalize(label)
    with LOCK:rows=read(STORE)
    for scope,target in [('application',application_key(url)),('site',scope_key(url)),('global','')]:
        if consent(label,kind) and scope!='application':continue
        for r in reversed(rows):
            if r['scope']==scope and r['target']==target and key in [normalize(x) for x in [r['label'],*r.get('aliases',[])]]:
                return r
    return None
def record_question(label,url,kind='text',required=False,options=None):
    if restricted(label) or not normalize(label):return None
    identity=hashlib.sha256((application_key(url)+'|'+normalize(label)+'|'+kind).encode()).hexdigest()[:24]
    with LOCK:
        rows=read(QUESTIONS);row=next((r for r in rows if r['id']==identity),None)
        if row is None:
            row={'id':identity,'label':label[:500],'url':application_key(url),'kind':kind,'first_seen_at':now()};rows.append(row)
        row.update(required=required,options=(options or [])[:100],last_seen_at=now())
        write(QUESTIONS,rows)
    return row
def usable(answer,question):
    if answer is None:return False
    if answer.get('skip'):return not question['required']
    value=answer.get('value')
    if question['kind']=='checkbox':return isinstance(value,bool)
    if question.get('options'):return str(value) in [str(o['value']) for o in question['options'] if str(o['value']).strip()]
    return value is not None and str(value).strip()!=''
def save_answer(label,value,scope='global',url='',aliases=None,skip=False,kind='text'):
    if restricted(label):raise ValueError('Enter passwords, verification codes and identity/payment documents directly on the official website.')
    if not normalize(label):raise ValueError('Enter the exact form question.')
    if consent(label,kind) and scope!='application':raise ValueError('Consent and declarations must be saved for this application only.')
    target=application_key(url) if scope=='application' else scope_key(url) if scope=='site' else ''
    aliases=aliases or []
    if any(restricted(a) or consent(a,kind) for a in aliases):raise ValueError('Sensitive/consent questions cannot be aliases.')
    if not skip and (value is None or isinstance(value,str) and not value.strip()):raise ValueError('Provide an answer or explicitly leave an optional field blank.')
    identity=hashlib.sha256((scope+'|'+target+'|'+normalize(label)).encode()).hexdigest()[:24]
    with LOCK:
        rows=read(STORE)
        # Do not allow conflicting aliases to silently override a different question.
        names={normalize(x) for x in [label,*aliases]}
        if any(r['id']!=identity and r['scope']==scope and r['target']==target and names.intersection(normalize(x) for x in [r['label'],*r.get('aliases',[])]) for r in rows):
            raise ValueError('This question/alias already belongs to another saved answer in the same scope.')
        row={'id':identity,'label':label.strip(),'value':value,'scope':scope,'target':target,'url':url,'aliases':aliases,'skip':skip,'kind':kind,'updated_at':now()}
        rows=[r for r in rows if r['id']!=identity];rows.append(row);write(STORE,rows)
    return row
def delete_answer(identity):
    with LOCK:
        rows=read(STORE);filtered=[r for r in rows if r['id']!=identity]
        if len(filtered)==len(rows):return False
        write(STORE,filtered);return True
