import tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from datetime import datetime,timezone
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from services.integration_bridge.models import Base,Job,JobVerification,ApplicationState
from services.integration_bridge.extended_search import extended_router
from services.integration_bridge.freelancing import freelance_router
from services.job_collector import extended_search as source

class IntegrationTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name)
        self.engine=create_engine('sqlite:///'+str(self.root/'test.db'),connect_args={'check_same_thread':False})
        Base.metadata.create_all(self.engine);self.db=sessionmaker(bind=self.engine)
        def start(kind,work,metadata=None):
            task={'kind':kind,'new_jobs':0,'results':[],**(metadata or {})};work(task);task['status']='Completed';return task
        app=FastAPI();app.include_router(extended_router(self.db,start));app.include_router(freelance_router(self.db));self.client=TestClient(app)
        self.addCleanup(self.temp.cleanup);self.addCleanup(self.engine.dispose);self.addCleanup(self.client.close)
    def raw(self,**kwargs):
        return {'title':'Junior Python Engineer','company':'Fixture','url':'https://jobs.lever.co/fixture/abc','location':'Bengaluru, India','description':'0-2 years experience with Python.','countries':['in'],'date':'2026-11-17','id':'fixture',**kwargs}
    def run_search(self,rows):
        with patch.object(source,'health',return_value={'ready':True}),patch.object(source,'choose_queries',return_value=['Python']),patch.object(source,'search',return_value={'results':rows,'meta':{'total':100},'cached':False,'collected_at':datetime.now(timezone.utc).isoformat()}):
            response=self.client.post('/api/extended-search/run',json={});self.assertEqual(response.status_code,200);return response.json()
    def test_cross_source_dedupe_preserves_application_state_and_availability(self):
        with self.db() as db:
            j=Job(title='Junior Python Engineer',company_name='Fixture',source='manual',canonical_url='https://jobs.lever.co/fixture/abc/apply',status=ApplicationState.SUBMITTED);db.add(j);db.flush()
            db.add(JobVerification(job_id=j.id,availability='expired',provider='lever',source_name='Original'));db.commit()
        result=self.run_search([self.raw()]);self.assertEqual(result['new_jobs'],0);self.assertEqual(result['results'][0]['duplicates'],1)
        with self.db() as db:
            self.assertEqual(db.query(Job).one().status,ApplicationState.SUBMITTED)
            self.assertEqual(db.query(JobVerification).one().availability,'expired')
            self.assertEqual(db.query(JobVerification).one().source_name,'Original')
    def test_filters_seniority_location_invalid_and_retains_uncertain(self):
        result=self.run_search([self.raw(),self.raw(title='Python Technical Lead',url='https://example.com/lead'),self.raw(location='United States',countries=['us'],url='https://example.com/us'),self.raw(url='javascript:alert(1)')])
        self.assertEqual(result['new_jobs'],1);r=result['results'][0];self.assertEqual(r['excluded'],2);self.assertEqual(r['invalid'],1)
        with self.db() as db:
            self.assertEqual(db.query(Job).one().posting_date.date().isoformat(),'2026-11-17')
            self.assertIsNone(db.query(Job).one().salary_currency)
            self.assertEqual(db.query(JobVerification).one().availability,'unchecked')
    def test_source_error_is_reported(self):
        with patch.object(source,'health',return_value={'ready':True}),patch.object(source,'choose_queries',return_value=['Python']),patch.object(source,'search',side_effect=ValueError('429 source rate limited')):
            data=self.client.post('/api/extended-search/run',json={}).json();self.assertIn('429',data['results'][0]['error']);self.assertEqual(data['new_jobs'],0)
    def test_conflicting_country_facets_and_senior_titles_do_not_pass(self):
        result=self.run_search([self.raw(location='Taguig, NCR, Philippines',countries=['in']),self.raw(title='Software Engineer III'),self.raw(title='AI Engineer Lead')])
        self.assertEqual(result['new_jobs'],0);self.assertEqual(result['results'][0]['excluded'],3)
    def test_request_limits_and_unknown_lanes(self):
        for body in [{'max_searches':9},{'days':0},{'campaign_ids':['unknown']},{'results_per_search':500}]:
            self.assertEqual(self.client.post('/api/extended-search/run',json=body).status_code,422)
    def test_cache_and_rotation_avoid_duplicate_requests(self):
        with patch.object(source,'DATA',self.root/'data'),patch.object(source,'bridge',return_value={'results':[]}) as bridge:
            self.assertFalse(source.search('Python',30,False,25)['cached'])
            self.assertTrue(source.search('Python',30,False,25)['cached']);self.assertEqual(bridge.call_count,1)
            self.assertNotEqual(source.choose_queries([],2),source.choose_queries([],2))
    def test_freelance_save_duplicate_draft_and_persistence(self):
        body={'title':'Python report automation','url':'https://www.freelancer.com/projects/fixture?utm_source=test','description':'Convert CSV inputs into a report.','budget':'USD 200 fixed'}
        response=self.client.post('/api/freelancing/leads',json=body);self.assertEqual(response.status_code,201);lead=response.json()
        self.assertEqual(self.client.post('/api/freelancing/leads',json=body).status_code,409)
        draft=self.client.post(f"/api/freelancing/leads/{lead['id']}/draft").json()['proposal'];self.assertIn('acceptance criteria',draft)
        self.client.patch(f"/api/freelancing/leads/{lead['id']}",json={'status':'Drafting','proposal':draft})
        saved=self.client.get('/api/freelancing').json()['leads'][0];self.assertEqual(saved['proposal'],draft);self.assertEqual(saved['status'],'Drafting');self.assertEqual(saved['budget'],'USD 200 fixed')
        self.assertEqual(self.client.patch(f"/api/freelancing/leads/{lead['id']}",json={'status':'Fake'}).status_code,422)
    def test_freelance_validation(self):
        for url in ['javascript:alert(1)','https://name:password@example.com/job']:
            self.assertEqual(self.client.post('/api/freelancing/leads',json={'title':'Fixture','url':url}).status_code,422)
        self.assertEqual(self.client.post('/api/freelancing/leads',json={'title':'  ','url':'https://example.com/job'}).status_code,422)
        self.assertEqual(self.client.post('/api/freelancing/leads/999/draft').status_code,404)
if __name__=='__main__':unittest.main()
