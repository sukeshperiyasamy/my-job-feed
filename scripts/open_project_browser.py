"""Native shortcut entry point: open/reuse the same project browser."""
import argparse
import sys
import subprocess
import time
import requests
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from services.browser_manager.project_browser import project_browser

ROOT=Path(__file__).resolve().parents[1]

def ensure_dashboard():
    try:
        response=requests.get('http://127.0.0.1:8000/health',timeout=2)
        if response.ok and response.json().get('project_root')=='C:\\sukesh\\job':return
        raise RuntimeError('Port 8000 is serving another application. Close the conflicting service first.')
    except requests.ConnectionError:pass
    python=ROOT/'.venv'/'Scripts'/'pythonw.exe'
    logs=ROOT/'logs';logs.mkdir(exist_ok=True)
    with (logs/'dashboard-shortcut.log').open('a',encoding='utf-8') as output:
        subprocess.Popen([str(python),'-m','uvicorn','services.integration_bridge.api:app','--app-dir',str(ROOT),'--host','127.0.0.1','--port','8000'],cwd=ROOT,stdin=subprocess.DEVNULL,stdout=output,stderr=output,creationflags=subprocess.CREATE_NO_WINDOW)
    for _ in range(40):
        try:
            if requests.get('http://127.0.0.1:8000/health',timeout=1).ok:return
        except requests.RequestException:pass
        time.sleep(.2)
    raise RuntimeError('Dashboard did not start. Check logs/dashboard-shortcut.log.')

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--url',default='http://127.0.0.1:8000/project-browser')
    args=parser.parse_args()
    try:
        ensure_dashboard()
        project_browser.open_url(args.url)
    except Exception as exc:
        # pythonw shortcuts have no terminal; show a useful failure without exposing credentials.
        import ctypes
        ctypes.windll.user32.MessageBoxW(0,str(exc),'Job Hunter project browser',0x10)
        raise SystemExit(1)
