"""One user-owned project browser, independent of API/worker lifetimes.

The API never exports cookies or reads passwords. Only the matching project profile
and loopback debugging listener may be reused; a personal browser is never attached.
"""
import json
import os
import subprocess
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote, urlsplit
import psutil
import requests

ROOT=Path(__file__).resolve().parents[2]
PROFILE=ROOT/'browser-profiles'/'project-browser'
STATE=ROOT/'data'/'project-browser.json'
DEFAULT_PORT=9223

def executable_path():
    candidates=['C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe','C:/Program Files/Google/Chrome/Application/chrome.exe']
    for path in candidates:
        if Path(path).is_file():return path
    raise RuntimeError('Microsoft Edge or Google Chrome is required for the project browser.')

class ProjectBrowser:
    def __init__(self,profile_dir=PROFILE,state_file=STATE,port=DEFAULT_PORT,headless=False):
        self.profile=Path(profile_dir).resolve()
        self.state_file=Path(state_file)
        self.port=int(port)
        self.headless=headless
        self.lock=threading.RLock()
        self._process=None
        self.http=requests.Session();self.http.trust_env=False

    @property
    def endpoint(self):return f'http://127.0.0.1:{self.port}'

    def _owns(self,process):
        try:
            args=process.cmdline()
            profiles=[a.split('=',1)[1].strip('"') for a in args if a.startswith('--user-data-dir=')]
            return process.name().lower() in ['msedge.exe','chrome.exe'] and any(os.path.normcase(str(Path(p).resolve()))==os.path.normcase(str(self.profile)) for p in profiles) and f'--remote-debugging-port={self.port}' in args and '--type=renderer' not in args
        except (psutil.Error,OSError):return False

    def _owner(self):
        try:
            state=json.loads(self.state_file.read_text(encoding='utf-8'))
            process=psutil.Process(state['pid'])
            if self._owns(process):return process
        except (OSError,ValueError,KeyError,psutil.Error):pass
        for process in psutil.process_iter(['pid','name']):
            if (process.info['name'] or '').lower() in ['msedge.exe','chrome.exe'] and self._owns(process):return process
        return None

    def _listener_owner(self):
        for connection in psutil.net_connections(kind='tcp'):
            if connection.status==psutil.CONN_LISTEN and connection.laddr.port==self.port:
                if connection.laddr.ip not in ['127.0.0.1','::1']:
                    raise RuntimeError('Project browser listener must be restricted to this computer.')
                if not connection.pid or not self._owns(psutil.Process(connection.pid)):
                    raise RuntimeError('The browser port belongs to another process. No browser was attached.')
                return connection.pid
        return None

    def running(self):
        try:
            owner=self._owner()
            if not owner or self._listener_owner()!=owner.pid:return False
            response=self.http.get(self.endpoint+'/json/version',timeout=1)
            return response.ok and bool(response.json().get('webSocketDebuggerUrl'))
        except (requests.RequestException,ValueError,psutil.Error,RuntimeError):return False

    def ensure_running(self):
        with self.lock:
            # Check ownership before talking to a debugging listener at this port.
            listener=self._listener_owner()
            owner=self._owner()
            if listener and owner and listener==owner.pid and self.running():return self.endpoint
            if owner:
                for _ in range(30):
                    if self.running():return self.endpoint
                    time.sleep(.1)
                raise RuntimeError('Project browser is open but its connection is not ready. Close that project window and reopen it; saved data is retained.')
            self.profile.mkdir(parents=True,exist_ok=True)
            exe=executable_path()
            args=[exe,f'--user-data-dir={self.profile}',f'--remote-debugging-port={self.port}','--remote-debugging-address=127.0.0.1','--no-first-run','--no-default-browser-check','--restore-last-session','--new-window']
            if self.headless:args.append('--headless=new')
            args.append('about:blank' if self.headless else 'http://127.0.0.1:8000/project-browser')
            process=subprocess.Popen(args,stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,close_fds=True)
            self._process=process
            self.state_file.parent.mkdir(parents=True,exist_ok=True)
            self.state_file.write_text(json.dumps({'pid':process.pid,'profile':str(self.profile),'port':self.port,'started_at':datetime.now(timezone.utc).isoformat()},indent=2),encoding='utf-8')
            for _ in range(80):
                if self.running():return self.endpoint
                time.sleep(.1)
            raise RuntimeError('Project browser did not become ready. Your system/browser policy may restrict remote debugging. No personal browser was used.')

    def open_url(self,url):
        parsed=urlsplit(url)
        if parsed.scheme not in ['http','https'] or not parsed.hostname or parsed.username or parsed.password:
            raise ValueError('Use a normal HTTP or HTTPS website URL without embedded credentials.')
        self.ensure_running()
        response=self.http.put(self.endpoint+'/json/new?'+quote(url,safe=''),timeout=5)
        response.raise_for_status()
        tab_id=response.json()['id']
        self.http.get(self.endpoint+'/json/activate/'+tab_id,timeout=3).raise_for_status()
        return {'status':'Opened in project browser','browser_running':True}

    def status(self):
        return {'running':self.running(),'profile_exists':self.profile.is_dir(),'profile_name':'Job Hunter project browser','session_policy':'Saved browser data is reused. The website controls session expiry and verification.'}

project_browser=ProjectBrowser()
