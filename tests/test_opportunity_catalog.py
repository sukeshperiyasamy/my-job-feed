"""Source, freshness and eligibility presentation regression checks."""
import os
import sys
import tempfile
import unittest
from datetime import datetime,timezone,timedelta
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from services.integration_bridge.opportunities import effective_status,read_catalog

class OpportunityStatusTests(unittest.TestCase):
    def setUp(self):self.now=datetime(2026,11,16,12,tzinfo=timezone.utc)
    def test_deadline_expiry_overrides_verified_open(self):
        self.assertEqual(effective_status({'status':'Verified open','deadline':'2026-11-15T23:59:00+05:30'},self.now),'Expired')
    def test_date_only_deadline_keeps_same_day_open(self):
        row={'status':'Verified open','deadline_date':'2026-11-16','verified_at':self.now.isoformat()}
        self.assertEqual(effective_status(row,self.now),'Verified open')
        self.assertEqual(effective_status(row,self.now+timedelta(days=1)),'Expired')
    def test_stale_verification_requires_recheck(self):
        self.assertEqual(effective_status({'status':'Verified open','verified_at':(self.now-timedelta(days=4)).isoformat()},self.now),'Needs recheck')
    def test_missing_or_future_check_not_verified(self):
        self.assertEqual(effective_status({'status':'Verified open'},self.now),'Unverified')
        self.assertEqual(effective_status({'status':'Verified open','verified_at':(self.now+timedelta(days=1)).isoformat()},self.now),'Unverified')
    def test_no_date_does_not_turn_lead_into_verified(self):
        self.assertEqual(effective_status({'status':'Unverified'},self.now),'Unverified')
    def test_seed_has_original_and_application_links(self):
        for row in read_catalog():
            self.assertTrue(row['source_url'].startswith('https://'))
            self.assertTrue(row['application_url'].startswith('https://'))
            self.assertTrue(row['evidence'])
            if row['status']=='Verified open':self.assertTrue(row.get('verified_at'))

class OpportunityAPITests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp=tempfile.TemporaryDirectory()
        os.environ['JOB_HUNTER_DATABASE']=str(Path(cls.temp.name)/'catalog-tests.db')
        from fastapi.testclient import TestClient
        from services.integration_bridge.api import app,engine
        cls.engine=engine;cls.client=TestClient(app)
    @classmethod
    def tearDownClass(cls):
        cls.client.close();cls.engine.dispose();cls.temp.cleanup()
    def test_internship_api_is_source_linked(self):
        response=self.client.get('/api/opportunities?category=internship')
        self.assertEqual(response.status_code,200)
        rows=response.json()
        self.assertTrue(rows)
        self.assertTrue(all(r['category']=='internship' for r in rows))
        self.assertTrue(all(r['source_name'] and r['source_url'] and r['application_url'] for r in rows))
    def test_no_claim_of_eligibility_from_deadline(self):
        rows=self.client.get('/api/opportunities?category=research').json()
        nitt=next(r for r in rows if r['organization']=='NIT Tiruchirappalli')
        self.assertEqual(nitt['deadline'],'2026-11-20T23:59:00+05:30')
        self.assertIn('BSc IT',nitt['details']['assistantship'])
    def test_verified_requires_dated_evidence(self):
        body={'category':'internship','title':'Test','organization':'Example','source_name':'Test','source_url':'https://example.com','application_url':'https://example.com/apply','status':'Verified open'}
        self.assertEqual(self.client.post('/api/opportunities',json=body).status_code,422)
    def test_report_path_is_bounded(self):
        self.assertEqual(self.client.get('/api/opportunity-reports/unapproved-name.md').status_code,404)
    def test_all_requested_company_and_national_targets_exist(self):
        rows=self.client.get('/api/opportunity-sources').json()
        self.assertEqual(len([r for r in rows if r['kind']=='Institute admission / project recruitment source']),54)
        names={r['name'] for r in rows}
        self.assertTrue({'BPL Medical Technologies','Smith+Nephew','Johnson & Johnson MedTech','NIT Tiruchirappalli','IIT Madras'}<=names)

if __name__=='__main__':unittest.main()
