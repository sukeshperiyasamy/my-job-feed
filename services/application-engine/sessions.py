"""One browser thread owns Playwright for the entire resumable application session."""
import json
import queue
import threading
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit
from services.application_engine.engine import ApplicationEngine
from services.application_engine.form_worker import load_json
from services.application_engine.portals import portal_for_url
from services.integration_bridge.models import Application, ApplicationAttempt, ApplicationState, ExecutionLog
from services.resume_engine.engine import VerifiedFactsStore

class ApplicationSessions:
    def __init__(self, session_factory):
        self.db = session_factory
        self.lock = threading.RLock()
        self.active = None

    def status(self, application_id):
        with self.lock:
            if self.active and self.active['id']==application_id:
                return {**self.active['outcome'], 'active':True, 'waiting':self.active['waiting']}
        with self.db() as db:
            log=db.query(ExecutionLog).filter(ExecutionLog.service=='application',ExecutionLog.details['application_id'].as_integer()==application_id).order_by(ExecutionLog.id.desc()).first()
            if log:
                return {**log.details['outcome'],'active':False,'waiting':False}
        return {'active':False,'waiting':False}

    def _save(self, application_id, outcome, final=False):
        with self.db() as db:
            record=db.get(Application,application_id)
            if not record:
                return
            state=next((s for s in ApplicationState if s.value==outcome['status']),ApplicationState.FAILED)
            record.state=state
            if state==ApplicationState.SUBMITTED:
                record.submitted_at=datetime.now(timezone.utc)
                record.job.status=ApplicationState.SUBMITTED
            db.add(ExecutionLog(service='application',level='ERROR' if state==ApplicationState.FAILED else 'INFO',message=outcome.get('error') or outcome['status'],details={'application_id':application_id,'outcome':outcome}))
            if final:
                db.add(ApplicationAttempt(application_id=application_id,worker_id='resumable-browser',attempt_number=len(record.attempts)+1,status=outcome['status'],is_dry_run=not outcome.get('submission_attempted',False),screenshot_path=outcome.get('screenshot'),error_message=outcome.get('error')))
            db.commit()

    def start(self, application_id, approved=False, use_saved_portal_resume=False):
        with self.lock:
            if self.active:
                if self.active['id']==application_id and approved and self.active['waiting']:
                    return self.command(application_id,'approve_saved' if use_saved_portal_resume else 'approve')
                raise ValueError('An application browser is already open. Continue or close that session first.')
            with self.db() as db:
                record=db.get(Application,application_id)
                if not record:
                    raise ValueError('Application not found.')
                if record.state==ApplicationState.SUBMITTED:
                    raise ValueError('This application is already submitted. Duplicate prevented.')
                if record.state not in [ApplicationState.PENDING_APPROVAL,ApplicationState.FAILED,ApplicationState.MANUAL_ACTION_REQUIRED]:
                    raise ValueError('Application is not ready. A stale Applying state must be reviewed before retrying.')
                previous=self.status(application_id)
                if previous.get('submission_attempted'):
                    raise ValueError('A previous submission may have reached the portal. Verify it manually; automatic retry is blocked.')
                portal=portal_for_url(record.job.canonical_url)
                if portal['application'] in ['employer_link','manual']:
                    raise ValueError(portal['note'])
                pdf=Path(f'C:/sukesh/job/data/generated-pdfs/job_{record.job_id}_tailored.pdf')
                if not pdf.exists():
                    raise ValueError('Tailored resume missing. Tailor this role before applying.')
                day=datetime.now(timezone.utc).replace(hour=0,minute=0,second=0,microsecond=0)
                used=db.query(ApplicationAttempt).filter(ApplicationAttempt.is_dry_run==False,ApplicationAttempt.attempted_at>=day).count()
                policy=load_json('application-policy.json',{})
                auto_allowed=(urlsplit(record.job.canonical_url).hostname or '').lower() in policy.get('auto_submit_domains',[])
                if (approved or auto_allowed) and used>=policy.get('daily_submission_limit',15):
                    raise ValueError('Daily application limit reached.')
                payload={'url':record.job.canonical_url,'pdf':str(pdf),'profile':portal['id']+'_session','cover_letter':''}
                letter=pdf.with_suffix('.txt')
                if letter.exists(): payload['cover_letter']=letter.read_text(encoding='utf-8')
                record.state=ApplicationState.APPLYING
                db.commit()
            state={'id':application_id,'commands':queue.Queue(),'waiting':False,'outcome':{'status':'Applying','error':None,'submission_attempted':False}}
            self.active=state
            threading.Thread(target=self._run,args=(state,payload,approved,use_saved_portal_resume),daemon=True).start()
            return {'status':'Applying','application_id':application_id}

    def command(self, application_id, command):
        with self.lock:
            if not self.active or self.active['id']!=application_id:
                raise ValueError('No live browser session. Start a new preparation session if no submission was attempted.')
            if not self.active['waiting']:
                raise ValueError('Browser is still working. Wait for it to pause.')
            if command not in ['resume','approve','approve_saved','cancel']:
                raise ValueError('Unsupported session command.')
            if command in ['approve','approve_saved']:
                day=datetime.now(timezone.utc).replace(hour=0,minute=0,second=0,microsecond=0)
                with self.db() as db:
                    used=db.query(ApplicationAttempt).filter(ApplicationAttempt.is_dry_run==False,ApplicationAttempt.attempted_at>=day).count()
                if used>=load_json('application-policy.json',{}).get('daily_submission_limit',15):
                    raise ValueError('Daily application limit reached.')
            self.active['waiting']=False
            self.active['commands'].put(command)
            return {'status':'Applying' if command!='cancel' else 'Closing','application_id':application_id}

    def _run(self,state,payload,approved,use_saved):
        def submission_checkpoint(outcome):
            with self.lock:
                state['outcome']=outcome
            self._save(state['id'],{**outcome,'status':'Applying'})
        def pause(outcome):
            self._save(state['id'],outcome)
            with self.lock:
                state.update(outcome=outcome,waiting=True)
            timeout=load_json('application-policy.json',{}).get('session_timeout_minutes',20)*60
            try:
                command=state['commands'].get(timeout=timeout)
            except queue.Empty:
                return 'timeout'
            if command!='cancel':
                self._save(state['id'],{'status':'Applying','error':None,**{'submission_attempted':outcome.get('submission_attempted',False)}})
            return command
        try:
            worker=ApplicationEngine(mode='approval_required',browser_profile=payload['profile'],headless=False,shared_browser=True)
            outcome=worker.run_application(payload['url'],VerifiedFactsStore(),payload['pdf'],payload['cover_letter'],explicit_approval=approved,pause=pause,use_saved_portal_resume=use_saved,on_submission=submission_checkpoint)
        except Exception as exc:
            attempted=state['outcome'].get('submission_attempted',False)
            outcome={**state['outcome'],'status':'Manual Action Required' if attempted else 'Failed','error':str(exc),'submission_attempted':attempted}
        try:
            self._save(state['id'],outcome,final=True)
        finally:
            with self.lock:
                self.active=None
