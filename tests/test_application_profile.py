"""Isolated answer-bank API checks; no account access or real form submission."""
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
TEMP=tempfile.TemporaryDirectory();ROOT=Path(TEMP.name)
os.environ['JOB_HUNTER_DATABASE']=str(ROOT/'api.db')
from fastapi.testclient import TestClient
from services.integration_bridge.api import app,engine
from services.application_engine import answer_store as store

class ApplicationProfileTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.client=TestClient(app)
    @classmethod
    def tearDownClass(cls):cls.client.close();engine.dispose();TEMP.cleanup()
    def setUp(self):
        for key in ['STORE','QUESTIONS']:
            p=patch.object(store,key,ROOT/(self._testMethodName+'-'+key+'.json'));p.start();self.addCleanup(p.stop)
    def save(self,**kw):return self.client.post('/api/application-profile/answers',json={'label':'Notice period','value':'30 days',**kw})
    def test_contact_schema_without_invented_answers(self):
        data=self.client.get('/api/application-profile').json()
        self.assertEqual(data['answers'],[])
        self.assertEqual(next(f for f in data['common_fields'] if f['label']=='Expected salary')['suggested_value'],'')
    def test_scoped_answers_precedence_and_shared_ats_employer_isolation(self):
        self.save(value='60 days')
        self.save(value='30 days',scope='site',url='https://jobs.lever.co/employer-a/job1')
        self.save(value='15 days',scope='application',url='https://jobs.lever.co/employer-a/job1')
        self.assertEqual(store.find_answer('Notice period','https://jobs.lever.co/employer-a/job1')['value'],'15 days')
        self.assertEqual(store.find_answer('Notice period','https://jobs.lever.co/employer-a/job2')['value'],'30 days')
        self.assertEqual(store.find_answer('Notice period','https://jobs.lever.co/employer-b/job2')['value'],'60 days')
    def test_new_question_answer_then_delete_reappears(self):
        q=store.record_question('Expected salary in INR','https://example.com/job/1',required=True)
        self.assertEqual(len(self.client.get('/api/application-profile').json()['pending_questions']),1)
        response=self.save(question_id=q['id'],label='Ignored injected label',value='800000',scope='application',url='https://wrong.example.com')
        self.assertEqual(response.status_code,200)
        self.assertEqual(response.json()['label'],q['label'])
        self.assertEqual(self.client.get('/api/application-profile').json()['pending_questions'],[])
        self.assertEqual(self.client.delete('/api/application-profile/answers/'+response.json()['id']).status_code,200)
        self.assertEqual(len(self.client.get('/api/application-profile').json()['pending_questions']),1)
    def test_checkbox_false_is_saved_and_consent_cannot_be_global(self):
        q=store.record_question('I accept privacy terms','https://example.com/job/1','checkbox',True)
        self.assertEqual(self.save(question_id=q['id'],scope='global',value=True).status_code,422)
        self.assertEqual(self.save(question_id=q['id'],scope='application',value=False).status_code,200)
        self.assertIs(store.find_answer(q['label'],q['url'],'checkbox')['value'],False)
        self.assertIsNone(store.find_answer(q['label'],'https://example.com/job/2','checkbox'))
    def test_optional_skip_required_and_choice_validation(self):
        q=store.record_question('Preferred interview time','https://example.com/job/1',required=False)
        self.assertEqual(self.save(question_id=q['id'],scope='application',skip=True,value=None).status_code,200)
        self.assertEqual(self.client.get('/api/application-profile').json()['pending_questions'],[])
        q=store.record_question('Working arrangement','https://example.com/job/1','select',True,[{'value':'onsite','text':'On site'}])
        self.assertEqual(self.save(question_id=q['id'],scope='application',skip=True).status_code,422)
        self.assertEqual(self.save(question_id=q['id'],scope='application',value='remote').status_code,422)
        self.assertEqual(self.save(question_id=q['id'],scope='application',value='onsite').status_code,200)
    def test_secrets_are_not_queued_or_saved(self):
        for label in ['Password','OTP verification','Aadhaar number','Bank account number']:
            self.assertIsNone(store.record_question(label,'https://example.com/job/1'))
            self.assertEqual(self.save(label=label,value='do-not-store').status_code,422)
    def test_aliases_conflicts_and_language_symbols(self):
        self.assertEqual(self.save(aliases=['Availability notice']).status_code,200)
        self.assertEqual(store.find_answer('Availability notice *','https://example.com/job/1')['value'],'30 days')
        self.assertEqual(self.save(label='Other question',aliases=['Notice period']).status_code,422)
        self.save(label='C++ experience',value='1 year')
        self.assertIsNone(store.find_answer('C# experience','https://example.com/job/1'))
    def test_external_origin_blocked(self):
        self.assertEqual(self.client.post('/api/application-profile/answers',headers={'Origin':'https://untrusted.example'},json={'label':'Test','value':'x'}).status_code,403)

if __name__=='__main__':unittest.main()
