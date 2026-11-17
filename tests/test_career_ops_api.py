"""Isolated API/cache tests; collectors and availability checks are mocked."""
import os,sys,tempfile,time,unittest,json
from pathlib import Path
from unittest.mock import patch
from datetime import datetime,timezone
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
TEMP=tempfile.TemporaryDirectory();ROOT=Path(TEMP.name)
os.environ['JOB_HUNTER_DATABASE']=str(ROOT/'test.db')
from fastapi.testclient import TestClient
from services.integration_bridge.api import app,engine,SessionLocal,application_sessions
from services.integration_bridge.models import Job,JobVerification,Application,ApplicationState
from services.job_collector import career_ops

class CareerOpsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.client=TestClient(app)
    @classmethod
    def tearDownClass(cls):cls.client.close();engine.dispose();TEMP.cleanup()
    def setUp(self):
        for key,value in [('CUSTOM',ROOT/(self._testMethodName+'.json')),('DATA',ROOT/self._testMethodName)]:
            p=patch.object(career_ops,key,value);p.start();self.addCleanup(p.stop)
        p=patch.object(career_ops,'status',return_value={'ready':True,'version':'fixture','node':'test','commit':'fixture123','repository':'https://example.com'});p.start();self.addCleanup(p.stop)
    def wait(self):
        for _ in range(150):
            result=self.client.get('/api/collection/status').json()
            if result['status']!='Running':return result
            time.sleep(.02)
        self.fail('Fixture task did not complete')
    def test_source_validation_and_health(self):
        self.assertEqual(len(self.client.get('/api/career-ops').json()['providers']),8)
        with patch.object(career_ops,'run_bridge',return_value={'supported':True}):
            r=self.client.post('/api/career-ops/sources',json={'name':'Fixture employer','provider':'lever','url':'https://jobs.lever.co/fixture'});self.assertEqual(r.status_code,200)
            self.assertEqual(self.client.post('/api/career-ops/sources',json={'name':'Again','provider':'lever','url':'https://jobs.lever.co/fixture'}).status_code,422)
        self.assertEqual(self.client.post('/api/career-ops/sources',json={'name':'Unsafe','provider':'local-parser','url':'https://example.com'}).status_code,422)
    def test_ingest_deduplicates_and_preserves_dates_attribution_and_state(self):
        with SessionLocal() as db:
            job=Job(title='Junior Embedded Engineer',company_name='Fixture',source='manual',canonical_url='https://jobs.lever.co/fixture/abc/apply',status=ApplicationState.SUBMITTED)
            db.add(job);db.commit();jid=job.id
        raw={'title':'Junior Embedded Engineer','company':'Fixture','url':'https://jobs.lever.co/fixture/abc','location':'Bengaluru','description':'0-2 years experience. ESP32.'}
        other={**raw,'url':'https://jobs.lever.co/fixture/xyz','postedAt':1794844800000,'salary':{'min':600000,'max':900000,'currency':'INR'}}
        with patch.object(career_ops,'collect_source',return_value={'jobs':[raw,other], 'fetched':2,'collected_at':datetime.now(timezone.utc).isoformat()}):
            self.assertEqual(self.client.post('/api/career-ops/scan',json={'source_ids':['dozee']}).status_code,200)
            result=self.wait();self.assertEqual(result['new_jobs'],1);self.assertEqual(result['results'][0]['duplicates'],1)
        with SessionLocal() as db:
            self.assertEqual(db.get(Job,jid).status,ApplicationState.SUBMITTED)
            self.assertEqual(db.get(JobVerification,jid).source_name,'Dozee')
            j=db.query(Job).filter_by(canonical_url=other['url']).one();self.assertEqual(j.salary_min,600000);self.assertIsNotNone(j.posting_date)
    def test_invalid_sources_and_batch_limits(self):
        for payload in [{'source_ids':['bad']},{'campaign_ids':['bad']},{'max_jobs_per_source':101}]:self.assertEqual(self.client.post('/api/career-ops/scan',json=payload).status_code,422)
        self.assertEqual(self.client.post('/api/career-ops/check',json={'job_ids':[1,2,3,4,5,6]}).status_code,422)
    def test_failures_are_not_empty_successes(self):
        with patch.object(career_ops,'collect_source',side_effect=ValueError('Fixture blocked')):
            self.client.post('/api/career-ops/scan',json={'source_ids':['dozee']});r=self.wait()
        self.assertEqual(r['status'],'Completed with warnings');self.assertEqual(r['new_jobs'],0);self.assertIn('Fixture blocked',r['results'][0]['error'])
    def test_expired_guard_and_inconclusive_recheck(self):
        with SessionLocal() as db:
            j=Job(title='Expired fixture',company_name='Fixture',source='manual',canonical_url='https://example.com/expired-fixture');db.add(j);db.flush()
            a=Application(job_id=j.id,state=ApplicationState.PENDING_APPROVAL,idempotency_key='expired_fixture');db.add(a);db.flush();jid=j.id;aid=a.id;db.commit()
        for verdict in ['expired','uncertain','active']:
            with patch.object(career_ops,'run_bridge',return_value={'result':verdict,'reason':'Fixture result'}):
                self.client.post('/api/career-ops/check',json={'job_ids':[jid]});self.wait()
            with SessionLocal() as db:self.assertEqual(db.get(JobVerification,jid).availability,'expired' if verdict=='uncertain' else verdict)
            if verdict!='active':
                with self.assertRaisesRegex(ValueError,'expired'):application_sessions.start(aid,approved=True)
    def test_remote_feed_keeps_publisher_url_and_needs_country_review(self):
        s={'id':'himalayas','name':'Himalayas','provider':'himalayas'}
        row=career_ops.normalize_job({'title':'Junior Python Engineer','url':'https://himalayas.app/jobs/example','location':'Worldwide','description':'Python developer'},s)
        self.assertEqual(row['canonical_url'],'https://himalayas.app/jobs/example');self.assertEqual(row['screening']['status'],'needs_review')
    def test_cache_spaces_remote_requests(self):
        s=next(s for s in career_ops.sources() if s['id']=='remotive')
        with patch.object(career_ops,'run_bridge',return_value={'jobs':[],'fetched':0}) as bridge:
            self.assertFalse(career_ops.collect_source(s)['cached']);self.assertTrue(career_ops.collect_source(s)['cached']);self.assertEqual(bridge.call_count,1)
    def test_external_origin_cannot_start_collection(self):
        self.assertEqual(self.client.post('/api/career-ops/scan',json={},headers={'Origin':'https://untrusted.example'}).status_code,403)

if __name__=='__main__':unittest.main()
