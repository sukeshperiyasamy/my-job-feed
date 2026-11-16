"""Uses an isolated SQLite database and mocked collectors/workers."""
import os
import sys
import tempfile
import unittest
import threading
import time
from pathlib import Path
from unittest.mock import patch, MagicMock
TEMP=tempfile.TemporaryDirectory()
os.environ['JOB_HUNTER_DATABASE']=str(Path(TEMP.name)/'tests.db')
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from fastapi.testclient import TestClient
from services.integration_bridge.api import app,SessionLocal,application_sessions,engine
from services.integration_bridge.models import Job,Application,ApplicationState
from services.job_collector.careers import canonical_url,structured_jobs
from bs4 import BeautifulSoup

class OperationsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.client=TestClient(app)
    @classmethod
    def tearDownClass(cls):
        cls.client.close()
        engine.dispose()
        TEMP.cleanup()
    def test_watchlist_seed_regions(self):
        rows=self.client.get('/api/watchlist').json()
        self.assertEqual({r['region'] for r in rows},{'Tamil Nadu','Bengaluru','Andhra Pradesh'})
        self.assertGreaterEqual(len(rows),12)
    def test_portal_capabilities_are_honest(self):
        rows={r['id']:r for r in self.client.get('/api/portals').json()}
        self.assertTrue(rows['naukri']['search_available'])
        self.assertFalse(rows['hirepro']['search_available'])
        self.assertEqual(rows['linkedin']['application'],'employer_link')
        self.assertEqual(self.client.post('/api/discovery/run',json={'search_term':'Biomedical','sites':['hirepro']}).status_code,422)
    def test_canonical_url_duplicate_prevention(self):
        data={'title':'Test Engineer','company_name':'Test Company','source':'manual','canonical_url':'https://company.example/jobs/123/?utm_source=test'}
        first=self.client.post('/api/jobs',json=data)
        self.assertEqual(first.status_code,200)
        data['canonical_url']='https://company.example/jobs/123'
        second=self.client.post('/api/jobs',json=data).json()
        self.assertEqual(second['status'],'exists')
        self.assertEqual(second['job_id'],first.json()['job_id'])
    def test_non_web_url_rejected(self):
        response=self.client.post('/api/jobs',json={'title':'Bad','company_name':'Bad','source':'manual','canonical_url':'javascript:alert(1)'})
        self.assertEqual(response.status_code,422)
    def test_invalid_watchlist_url_returns_validation_error(self):
        response=self.client.post('/api/watchlist',json={'name':'Invalid','careers_url':'javascript:alert(1)','region':'Tamil Nadu'})
        self.assertEqual(response.status_code,422)
    def test_overview_counts_actual_active_worker(self):
        self.assertEqual(self.client.get('/api/overview').json()['active_workers'],0)
    def test_submitted_document_cannot_be_overwritten(self):
        with SessionLocal() as db:
            job=Job(title='Submitted document fixture',company_name='Test',source='manual',canonical_url='https://example.com/submitted-doc',status=ApplicationState.SUBMITTED)
            db.add(job);db.flush()
            record=Application(job_id=job.id,state=ApplicationState.SUBMITTED,idempotency_key='fixture_submitted_doc')
            db.add(record);db.commit();jid=job.id
        with patch('services.integration_bridge.api.match_job_with_llm') as matcher:
            self.assertEqual(self.client.post(f'/api/jobs/{jid}/score').status_code,409)
            matcher.assert_not_called()
        with SessionLocal() as db:self.assertEqual(db.get(Job,jid).status,ApplicationState.SUBMITTED)
    def test_missing_resume_does_not_leave_applying(self):
        with SessionLocal() as db:
            job=Job(id=99881,title='Test',company_name='Test',source='manual',canonical_url='https://example.com/99881')
            db.add(job);db.flush()
            record=Application(job_id=job.id,state=ApplicationState.PENDING_APPROVAL,idempotency_key='fixture_99881')
            db.add(record);db.commit();aid=record.id
        response=self.client.post('/api/applications/decide',json={'application_id':aid,'decision':'approve'})
        self.assertEqual(response.status_code,409)
        with SessionLocal() as db:self.assertEqual(db.get(Application,aid).state,ApplicationState.PENDING_APPROVAL)
    def test_submitted_cannot_be_reapplied(self):
        with SessionLocal() as db:
            job=Job(title='Done',company_name='Test',source='manual',canonical_url='https://example.com/done')
            db.add(job);db.flush()
            record=Application(job_id=job.id,state=ApplicationState.SUBMITTED,idempotency_key='fixture_done')
            db.add(record);db.commit();aid=record.id
        for decision in ['approve','prepare','reject','reset_after_check']:
            self.assertEqual(self.client.post('/api/applications/decide',json={'application_id':aid,'decision':decision}).status_code,409)
    def test_invalid_decision_rejected(self):
        self.assertEqual(self.client.post('/api/applications/decide',json={'application_id':1,'decision':'banana'}).status_code,422)
    def test_external_browser_origin_cannot_trigger_application(self):
        response=self.client.post('/api/applications/decide',headers={'Origin':'https://untrusted.example'},json={'application_id':1,'decision':'approve'})
        self.assertEqual(response.status_code,403)
    def test_background_session_persists_result_and_blocks_parallel_start(self):
        with SessionLocal() as db:
            job=Job(title='Async fixture',company_name='Test',source='manual',canonical_url='https://example.com/async-fixture')
            db.add(job);db.flush()
            record=Application(job_id=job.id,state=ApplicationState.PENDING_APPROVAL,idempotency_key='fixture_async')
            db.add(record);db.commit();aid=record.id
        release=threading.Event()
        def fake_run(*args,**kwargs):
            release.wait(3)
            return {'status':'Submitted','submission_attempted':True,'confirmation_text':'Application received: FIXTURE-123'}
        pdf=MagicMock();pdf.exists.return_value=True;pdf.with_suffix.return_value.exists.return_value=False
        try:
            with patch('services.application_engine.sessions.Path',return_value=pdf),patch('services.application_engine.sessions.ApplicationEngine') as worker:
                worker.return_value.run_application.side_effect=fake_run
                result=application_sessions.start(aid,approved=True)
                self.assertEqual(result['status'],'Applying')
                with self.assertRaises(ValueError):application_sessions.start(aid)
                release.set()
                for _ in range(100):
                    if not application_sessions.active:break
                    time.sleep(.02)
                self.assertFalse(application_sessions.active)
            state=application_sessions.status(aid)
            self.assertEqual(state['status'],'Submitted')
            self.assertIn('FIXTURE-123',state['confirmation_text'])
            self.assertFalse(state['active'])
        finally:release.set()
    def test_worker_exception_after_checkpoint_blocks_retry(self):
        with SessionLocal() as db:
            job=Job(title='Uncertain fixture',company_name='Test',source='manual',canonical_url='https://example.com/uncertain-fixture')
            db.add(job);db.flush()
            record=Application(job_id=job.id,state=ApplicationState.PENDING_APPROVAL,idempotency_key='fixture_uncertain')
            db.add(record);db.commit();aid=record.id
        def fake_run(*args,**kwargs):
            kwargs['on_submission']({'status':'Applying','submission_attempted':True})
            raise RuntimeError('Worker disconnected after submit')
        pdf=MagicMock();pdf.exists.return_value=True;pdf.with_suffix.return_value.exists.return_value=False
        with patch('services.application_engine.sessions.Path',return_value=pdf),patch('services.application_engine.sessions.ApplicationEngine') as worker:
            worker.return_value.run_application.side_effect=fake_run
            application_sessions.start(aid,approved=True)
            for _ in range(100):
                if not application_sessions.active:break
                time.sleep(.02)
            self.assertIsNone(application_sessions.active)
            state=application_sessions.status(aid)
            self.assertEqual(state['status'],'Manual Action Required')
            self.assertTrue(state['submission_attempted'])
            with self.assertRaisesRegex(ValueError,'previous submission'):
                application_sessions.start(aid,approved=True)
    def test_structured_opening_has_real_location(self):
        soup=BeautifulSoup('<script type="application/ld+json">{"@type":"JobPosting","title":"Biomedical Engineer","jobLocation":{"address":{"addressLocality":"Chennai"}},"url":"/jobs/one"}</script>','html.parser')
        jobs=structured_jobs(soup,'https://example.com/careers','Example')
        self.assertEqual(jobs[0]['location'],'Chennai')
        self.assertEqual(jobs[0]['canonical_url'],'https://example.com/jobs/one')
    def test_unstructured_page_is_not_a_fake_job(self):
        self.assertEqual(structured_jobs(BeautifulSoup('<h1>Careers</h1><p>We are always hiring</p>','html.parser'),'https://example.com','Example'),[])

if __name__=='__main__':unittest.main()
