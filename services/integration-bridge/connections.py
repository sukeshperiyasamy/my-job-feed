"""Browser-session connections, not OAuth/API tokens or inferred login states."""
import json
import re
import threading
import uuid
from datetime import datetime,timezone
from pathlib import Path
from urllib.parse import urlsplit
from fastapi import APIRouter,HTTPException
from fastapi.responses import FileResponse,HTMLResponse
from pydantic import BaseModel,Field
from services.browser_manager.project_browser import project_browser

ROOT=Path(__file__).resolve().parents[2]
SAVED=ROOT/'data'/'connections'/'accounts.json'
LOCK=threading.RLock()

class ConnectionCreate(BaseModel):
    name:str=Field(min_length=1,max_length=100)
    url:str
    group:str='Employer accounts'

class OpenConnection(BaseModel):
    url:str|None=None

def valid_url(url):
    p=urlsplit(url.strip())
    if p.scheme not in ['http','https'] or not p.hostname or p.username or p.password:
        raise ValueError('Use the website URL without embedded usernames or passwords.')
    if p.hostname in ['localhost','127.0.0.1','::1']:
        raise ValueError('Choose an external account website, not a local service.')
    return url.strip()

def read_saved():
    return json.loads(SAVED.read_text(encoding='utf-8')) if SAVED.exists() else {}

def write_saved(data):
    SAVED.parent.mkdir(parents=True,exist_ok=True)
    temp=SAVED.with_suffix('.tmp');temp.write_text(json.dumps(data,indent=2),encoding='utf-8');temp.replace(SAVED)

def connection_list():
    defaults=json.loads((ROOT/'config'/'browser-connections.json').read_text(encoding='utf-8'))
    with LOCK:saved=read_saved()
    rows=[]
    for row in defaults:
        entry={**row,**saved.get(row['id'],{})}
        entry['session_status']='Sign-in saved · you confirmed' if entry.get('confirmed_at') else 'Not confirmed'
        rows.append(entry)
    known={r['id'] for r in defaults}
    for key,row in saved.items():
        if key not in known:rows.append({**row,'id':key,'session_status':'Sign-in saved · you confirmed' if row.get('confirmed_at') else 'Not confirmed'})
    return rows

def create_connections_router():
    router=APIRouter()

    @router.get('/api/connections')
    def connections():return {'browser':project_browser.status(),'connections':connection_list()}

    @router.post('/api/project-browser/open')
    def open_browser():
        try:return project_browser.open_url('http://127.0.0.1:8000/project-browser')
        except Exception as exc:raise HTTPException(409,str(exc))

    @router.post('/api/connections')
    def add_connection(body:ConnectionCreate):
        try:url=valid_url(body.url)
        except ValueError as exc:raise HTTPException(422,str(exc))
        key='custom-'+uuid.uuid4().hex[:12]
        with LOCK:
            saved=read_saved()
            saved[key]={'id':key,'name':body.name.strip(),'url':url,'group':body.group[:100],'usage':'Browser session · application support depends on the website','note':'You control account setup. Saving a login does not approve an application or enable unsupported automated posting.'}
            write_saved(saved)
        return {'id':key,'status':'Connection added'}

    @router.post('/api/connections/{connection_id}/open')
    def open_connection(connection_id:str,body:OpenConnection):
        row=next((r for r in connection_list() if r['id']==connection_id),None)
        if not row:raise HTTPException(404,'Connection not found.')
        try:url=valid_url(body.url or row.get('url') or '')
        except ValueError as exc:raise HTTPException(422,'Paste an employer-specific account/application URL. '+str(exc))
        if row.get('url') and url!=row['url']:
            raise HTTPException(409,'Add a separate employer connection for a different URL.')
        try:result=project_browser.open_url(url)
        except Exception as exc:raise HTTPException(409,str(exc))
        with LOCK:
            saved=read_saved();entry=saved.setdefault(connection_id,{})
            # Saving an alternate employer URL creates a distinct connection instead of replacing another employer's account.
            entry.update(url=url,last_opened_at=datetime.now(timezone.utc).isoformat())
            write_saved(saved)
        return result

    @router.post('/api/connections/{connection_id}/confirm')
    def confirm_connection(connection_id:str):
        row=next((r for r in connection_list() if r['id']==connection_id),None)
        if not row:raise HTTPException(404,'Connection not found.')
        if not row.get('last_opened_at'):raise HTTPException(409,'Open the account in the project browser and sign in first.')
        with LOCK:
            saved=read_saved();saved.setdefault(connection_id,{})['confirmed_at']=datetime.now(timezone.utc).isoformat();write_saved(saved)
        return {'status':'Sign-in saved (confirmed by you)','note':'Browser cookies/local storage stay in the project profile. The site may request sign-in again.'}

    @router.post('/api/connections/{connection_id}/mark-reconnect')
    def reconnect(connection_id:str):
        if not any(r['id']==connection_id for r in connection_list()):raise HTTPException(404,'Connection not found.')
        with LOCK:
            saved=read_saved();saved.setdefault(connection_id,{}).pop('confirmed_at',None);write_saved(saved)
        return {'status':'Marked for reconnect','note':'This does not delete browser data or log you out.'}

    @router.get('/project-browser')
    def project_browser_home():return FileResponse(ROOT/'dashboard'/'project-browser.html',media_type='text/html')

    @router.get('/connect/{connection_id}',response_class=HTMLResponse)
    def connection_link(connection_id:str):
        if not re.fullmatch(r'[a-z0-9-]+',connection_id) or not any(r['id']==connection_id for r in connection_list()):raise HTTPException(404,'Connection not found.')
        # A normal GET/link preview never launches a browser; the user's button sends the action.
        return f'''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Open project account</title><link rel="stylesheet" href="/dashboard-assets/app.css"><body><div class="content" style="max-width:650px;margin:70px auto"><div class="panel"><div class="aside-body"><div class="eyebrow">JOB HUNTER PROJECT BROWSER</div><h1>Open your saved account.</h1><p>This opens the website in the browser profile reserved for this project.</p><button class="btn primary" id="open">Open in project browser</button><p id="result" role="status"></p><a href="/#connections">Manage connections →</a></div></div></div><script>document.getElementById('open').onclick=async function(){{this.disabled=true;try{{let r=await fetch('/api/connections/{connection_id}/open',{{method:'POST',headers:{{'Content-Type':'application/json'}},body:'{{}}'}});let d=await r.json();document.getElementById('result').textContent=d.detail||d.status;}}catch(e){{document.getElementById('result').textContent=e.message;}}finally{{this.disabled=false;}}}};</script></body></html>'''
    return router
