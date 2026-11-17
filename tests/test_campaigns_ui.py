"""Read-only UI checks with fixture listings and mocked campaign start."""
import sys
import unittest
from pathlib import Path
from playwright.sync_api import sync_playwright
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from services.job_collector.matching import assess_job
ROOT=Path(__file__).resolve().parents[1]

class CampaignUITests(unittest.TestCase):
    def test_campaign_controls_filters_and_evidence(self):
        with sync_playwright() as p:
            browser=p.chromium.launch(executable_path='C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',headless=True)
            page=browser.new_page(viewport={'width':1440,'height':1050});errors=[];calls=[]
            page.on('pageerror',lambda e:errors.append(str(e)))
            rows=[]
            for i,(title,desc) in enumerate([('Junior Embedded Engineer','0-2 years experience. ESP32.'),('Senior Software Engineer','5 years experience required.'),('Research Assistant Biosensor','NET required for institute assistantship.')],1):
                rows.append({'id':i,'title':title,'description':desc,'company_name':'Fixture','location':'Chennai','canonical_url':'https://example.com/jobs/'+str(i),'source':'fixture','status':'Discovered','screening':assess_job(title,desc,'Chennai')})
            page.route('**/api/jobs?*',lambda r:r.fulfill(json=rows))
            def start(r):
                calls.append(r.request.post_data_json)
                r.fulfill(json={'id':'fixture-campaign','kind':'campaigns','status':'Completed','new_jobs':0,'results':[]})
            page.route('**/api/search-campaigns/run',start)
            page.goto('http://127.0.0.1:8000/#jobs')
            page.locator('#job-campaign option[value="research"]').wait_for(state='attached')
            page.locator('#jobs-table tbody tr').first.wait_for()
            self.assertEqual(page.locator('#jobs-table tbody tr').count(),3)
            page.locator('#job-eligibility').select_option('potential_match')
            self.assertEqual(page.locator('#jobs-table tbody tr').count(),1)
            page.locator('#jobs-table [data-detail="1"]').click()
            self.assertIn('Embedded',page.locator('#job-screening').inner_text())
            page.locator('#detail-dialog [data-close]').click()
            page.locator('#job-eligibility').select_option('')
            page.locator('#job-campaign').select_option('research')
            self.assertEqual(page.locator('#jobs-table tbody tr').count(),1)
            page.locator('#jobs-table [data-detail="3"]').click()
            self.assertIn('institute assistantship',page.locator('#job-screening').inner_text())
            page.locator('#detail-dialog [data-close]').click()
            page.locator('#open-campaigns').click()
            self.assertEqual(page.locator('#campaign-choices input:checked').count(),7)
            for checkbox in page.locator('#campaign-choices input').all():checkbox.uncheck()
            page.locator('#campaign-choices input[value="embedded"]').check()
            page.locator('#run-campaigns').click()
            page.wait_for_function("!document.getElementById('campaign-dialog').open")
            self.assertEqual(calls[0]['campaign_ids'],['embedded'])
            self.assertEqual(calls[0]['max_searches'],12)
            page.set_viewport_size({'width':390,'height':844})
            self.assertTrue(page.evaluate('document.documentElement.scrollWidth<=innerWidth'))
            page.screenshot(path=str(ROOT/'screenshots/campaigns-mobile.png'))
            page.locator('#open-campaigns').click()
            page.set_viewport_size({'width':1440,'height':1050})
            page.screenshot(path=str(ROOT/'screenshots/search-campaigns.png'))
            self.assertEqual(errors,[])
            browser.close()

if __name__=='__main__':unittest.main()
