"""Profile form workflow with mocked personal data and writes."""
import unittest
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]

class ProfileUITests(unittest.TestCase):
    def test_new_question_options_save_and_continue(self):
        with sync_playwright() as p:
            browser=p.chromium.launch(executable_path='C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',headless=True)
            page=browser.new_page(viewport={'width':1440,'height':1100});errors=[];writes=[];commands=[]
            page.on('pageerror',lambda e:errors.append(str(e)))
            data={'common_fields':[{'label':'Full name','group':'Contact & links','suggested_value':'Fixture Candidate','aliases':['Candidate name']},{'label':'Expected salary','group':'Availability & pay','suggested_value':'','aliases':[]}],'answers':[],'pending_questions':[{'id':'question-1','label':'Notice period','url':'https://example.com/jobs/1','kind':'select','required':True,'first_seen_at':'2026-11-17','options':[{'value':'15','text':'15 days'},{'value':'30','text':'30 days'}]},{'id':'question-2','label':'I agree to privacy terms','url':'https://example.com/jobs/1','kind':'checkbox','required':True,'first_seen_at':'2026-11-17','options':[]}],'session':{'application_id':99,'waiting':True,'submission_attempted':False}}
            def route(r):
                if r.request.method=='GET':r.fulfill(json=data)
                else:
                    body=r.request.post_data_json;writes.append(body)
                    row={**body,'id':'answer-'+str(len(writes)),'target':body['url'],'updated_at':'2026-11-17'}
                    data['answers'].append(row);data['pending_questions']=[q for q in data['pending_questions'] if q['id']!=body.get('question_id')]
                    r.fulfill(json=row)
            page.route('**/api/application-profile**',route)
            page.route('**/api/applications/decide',lambda r:(commands.append(r.request.post_data_json),r.fulfill(json={'status':'Applying'})))
            page.goto('http://127.0.0.1:8000/#profile')
            page.locator('[data-answer-question="question-1"]').wait_for()
            self.assertTrue(page.locator('#view-profile').is_visible())
            page.locator('[data-answer-question="question-1"]').click()
            self.assertTrue(page.locator('#profile-label').is_disabled()==False)
            page.locator('#profile-choice').select_option('30')
            page.locator('#save-profile-answer').click()
            page.wait_for_function("!document.getElementById('profile-answer-dialog').open")
            self.assertEqual(writes[-1]['value'],'30');self.assertEqual(writes[-1]['scope'],'application')
            page.locator('[data-answer-question="question-2"]').click()
            self.assertTrue(page.locator('#profile-scope option[value="global"]').is_disabled())
            page.locator('#profile-choice').select_option('false');page.locator('#save-profile-answer').click()
            page.wait_for_function("!document.getElementById('profile-answer-dialog').open")
            self.assertIs(writes[-1]['value'],False)
            page.locator('#continue-profile-session').click()
            page.wait_for_timeout(100)
            self.assertEqual(commands[-1],{'application_id':99,'decision':'resume'})
            page.locator('[data-common-answer="0"]').click();page.locator('#profile-value').fill('Updated Candidate');page.locator('#save-profile-answer').click()
            page.wait_for_function("!document.getElementById('profile-answer-dialog').open")
            self.assertEqual(writes[-1]['aliases'],['Candidate name']);self.assertEqual(writes[-1]['scope'],'global')
            page.screenshot(path=str(ROOT/'screenshots/application-profile-desktop.png'))
            page.set_viewport_size({'width':390,'height':844})
            self.assertTrue(page.evaluate('document.documentElement.scrollWidth<=innerWidth'))
            page.screenshot(path=str(ROOT/'screenshots/application-profile-mobile.png'))
            self.assertEqual(errors,[])
            browser.close()

if __name__=='__main__':unittest.main()
