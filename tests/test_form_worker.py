"""Offline fixture tests. No real application websites are contacted."""
import sys
import tempfile
import threading
import unittest
from functools import partial
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from services.application_engine.engine import ApplicationEngine
from services.application_engine.portals import portal_for_url
from services.resume_engine.engine import VerifiedFactsStore

FORM='''<h1>Job application</h1><form onsubmit="event.preventDefault();document.body.innerHTML='<h2>Application submitted successfully</h2><p>Reference: REAL-42</p>'"><label for="first">First name *</label><input id="first" required><label for="last">Last name *</label><input id="last" required><label for="mail">Email address *</label><input id="mail" type="email" required><label for="cv">Resume / CV *</label><input id="cv" type="file" required>{extra}<button>Submit application</button></form>'''

class FormWorkerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp=tempfile.TemporaryDirectory()
        cls.root=Path(cls.temp.name)
        cls.resume=cls.root/'resume.pdf';cls.resume.write_bytes(b'%PDF-1.4 test upload')
        cls.server=ThreadingHTTPServer(('127.0.0.1',0),partial(SimpleHTTPRequestHandler,directory=str(cls.root)))
        threading.Thread(target=cls.server.serve_forever,daemon=True).start()
        cls.base=f'http://127.0.0.1:{cls.server.server_port}/'
        cls.facts=VerifiedFactsStore({'full_name':'Test Candidate','email':'test@example.com','phone':'1234567890'})
    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown();cls.server.server_close();cls.temp.cleanup()
    def run_form(self,html,answers=None,**kwargs):
        (self.root/'form.html').write_text(html,encoding='utf-8')
        worker=ApplicationEngine(browser_profile='fixture_worker',headless=True)
        # Tests must never pull real saved answers from the personal workspace.
        with patch('services.application_engine.form_worker.load_json',return_value={'answers':answers or {}}):
            return worker.run_application(self.base+'form.html',self.facts,str(self.resume),**kwargs)
    def test_dry_run_stops_before_submit(self):
        out=self.run_form(FORM.format(extra=''))
        self.assertEqual(out['status'],'Pending Approval')
        self.assertFalse(out['submission_attempted'])
        self.assertTrue(out['resume_attached'])
        self.assertIn('First name *',out['filled_fields'])
    def test_approved_form_has_real_confirmation(self):
        out=self.run_form(FORM.format(extra=''),explicit_approval=True)
        self.assertEqual(out['status'],'Submitted')
        self.assertIn('REAL-42',out['confirmation_text'])
        self.assertIsNone(out['confirmation_code'])
    def test_unknown_experience_and_consent_not_guessed(self):
        extra='<label for="exp">Years of relevant experience</label><input id="exp" required><label for="consent">I agree to the terms</label><input id="consent" type="checkbox" required>'
        out=self.run_form(FORM.format(extra=extra),explicit_approval=True)
        self.assertEqual(out['status'],'Manual Action Required')
        self.assertIn('Years of relevant experience',out['missing_fields'])
        self.assertIn('I agree to the terms',out['missing_fields'])
        self.assertFalse(out['submission_attempted'])
    def test_login_handoff_resumes_same_browser(self):
        worker=ApplicationEngine(browser_profile='fixture_resume',headless=True)
        (self.root/'login.html').write_text('<label>Password<input type="password"></label>',encoding='utf-8')
        pauses=[]
        def pause(outcome):
            pauses.append(outcome)
            worker.browser_manager._page.set_content(FORM.format(extra=''))
            return 'resume'
        with patch('services.application_engine.form_worker.load_json',return_value={'answers':{}}):
            out=worker.run_application(self.base+'login.html',self.facts,str(self.resume),explicit_approval=True,pause=pause)
        self.assertEqual(len(pauses),1)
        self.assertIn('Login required',pauses[0]['error'])
        self.assertEqual(out['status'],'Submitted')
    def test_captcha_stops(self):
        out=self.run_form('<h1>Verify you are human</h1>',explicit_approval=True)
        self.assertEqual(out['status'],'Manual Action Required')
        self.assertFalse(out['submission_attempted'])
    def test_dry_run_does_not_click_ambiguous_apply_entry(self):
        out=self.run_form('<h1>Job opening</h1><button onclick="document.body.innerHTML=\'Application submitted successfully\'">Apply for this job</button>')
        self.assertEqual(out['status'],'Pending Approval')
        self.assertFalse(out['submission_attempted'])
    def test_exact_standard_answer_fills_radio_group(self):
        extra='<div class="application-question"><div class="application-label">Notice period</div><label><input type="radio" name="notice" value="15 days" required>15 days</label><label><input type="radio" name="notice" value="30 days" required>30 days</label></div>'
        out=self.run_form(FORM.format(extra=extra),answers={'Notice period':'30 days'})
        self.assertEqual(out['status'],'Pending Approval')
        self.assertEqual(out['missing_fields'],[])
    def test_startup_failure_reported(self):
        worker=ApplicationEngine(browser_profile='fixture_failure')
        with patch.object(worker.browser_manager,'start',side_effect=RuntimeError('Cannot launch browser')):
            out=worker.run_application(self.base,self.facts,str(self.resume))
        self.assertEqual(out['status'],'Failed')
        self.assertIn('Cannot launch',out['error'])
    def test_domain_suffix_is_exact(self):
        self.assertEqual(portal_for_url('https://careers.hirepro.in/company')['id'],'hirepro')
        self.assertEqual(portal_for_url('https://naukri.com.evil.test')['id'],'employer')
    def test_direct_linkedin_application_disabled(self):
        out=ApplicationEngine().run_application('https://www.linkedin.com/jobs/1',self.facts,str(self.resume),explicit_approval=True)
        self.assertEqual(out['status'],'Manual Action Required')
        self.assertFalse(out['submission_attempted'])

if __name__=='__main__':unittest.main()
