"""Dashboard actions mocked; no external collection or application submission."""
import unittest
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
class CareerOpsUITests(unittest.TestCase):
    def test_scan_check_filters_and_source_attribution(self):
        with sync_playwright() as p:
            browser=p.chromium.launch(executable_path='C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',headless=True)
            page=browser.new_page(viewport={'width':1440,'height':1100});errors=[];calls=[]
            page.on('pageerror',lambda e:errors.append(str(e)))
            rows=[{'id':99771,'title':'Junior Python Engineer','company_name':'Fixture','location':'India','canonical_url':'https://remotive.com/jobs/fixture','source':'career_ops:remotive','status':'Discovered','availability':{'status':'unchecked'},'source_attribution':{'name':'Remotive','url':'https://remotive.com/jobs/fixture','provider':'remotive'}}]
            page.route('**/api/jobs?*',lambda r:r.fulfill(json=rows))
            page.route('**/api/career-ops',lambda r:r.fulfill(json={'integration':{'ready':True,'version':'1.40.0','node':'v24','commit':'fixture123','repository':'https://github.com/career-ops-hq/career-ops'},'providers':['lever','greenhouse'],'sources':[{'id':'fixture','name':'Fixture employer','provider':'lever','url':'https://jobs.lever.co/fixture','default':True}]}))
            def action(r):
                calls.append((r.request.url,r.request.post_data_json))
                r.fulfill(json={'id':'fixture-task','kind':'career_ops','status':'Completed','new_jobs':0,'results':[{'name':'Fixture employer','status':'Imported relevant leads','found':1,'kept':1,'duplicates':1}]})
            page.route('**/api/career-ops/scan',action);page.route('**/api/career-ops/check',action)
            page.goto('http://127.0.0.1:8000/#careerops');page.locator('[name="career-source"]').wait_for()
            self.assertTrue(page.locator('#view-careerops').is_visible())
            page.locator('#career-scan').click();page.wait_for_timeout(100)
            self.assertEqual(calls[-1][1]['source_ids'],['fixture'])
            self.assertIn('already saved',page.locator('#career-run-results').inner_text())
            page.locator('[name="career-check-job"]').check();page.locator('#career-check-selected').click();page.wait_for_timeout(100)
            self.assertEqual(calls[-1][1],{'job_ids':[99771],'browser_fallback':False})
            page.locator('#nav [data-tab="jobs"]').click()
            self.assertEqual(page.locator('#jobs-table a[href="https://remotive.com/jobs/fixture"]').count(),1)
            page.locator('#jobs-table [data-detail="99771"]').click()
            self.assertIn('Availability: unchecked',page.locator('#detail-body').inner_text())
            page.locator('#detail-dialog [data-close]').click()
            page.locator('#job-availability').select_option('expired')
            self.assertEqual(page.locator('#jobs-table tbody tr').count(),0)
            page.locator('#nav [data-tab="careerops"]').click();page.screenshot(path=str(ROOT/'screenshots/career-ops-desktop.png'))
            page.set_viewport_size({'width':390,'height':844})
            self.assertTrue(page.evaluate('document.documentElement.scrollWidth<=innerWidth'))
            page.screenshot(path=str(ROOT/'screenshots/career-ops-mobile.png'))
            self.assertEqual(errors,[]);browser.close()
if __name__=='__main__':unittest.main()
