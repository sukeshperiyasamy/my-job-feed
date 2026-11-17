"""Browser checks using mocked actions; never submits a real application."""
import json
import unittest
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]

class DashboardTest(unittest.TestCase):
    def test_internship_sources_details_and_research_tabs(self):
        with sync_playwright() as p:
            browser=p.chromium.launch(executable_path='C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',headless=True)
            page=browser.new_page(viewport={'width':1440,'height':1050})
            errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
            page.goto('http://127.0.0.1:8000/#internships')
            page.locator('#internships-cards .opportunity-card').first.wait_for()
            self.assertTrue(page.locator('#view-internships').is_visible())
            self.assertIn('Found on',page.locator('#internships-cards').inner_text())
            self.assertTrue(page.locator('#internships-cards .source-link').first.get_attribute('href').startswith('https://'))
            page.locator('[data-opportunity-detail="dozee-biomedical-intern"]').click()
            self.assertIn('Jaipur',page.locator('#opportunity-detail').inner_text())
            self.assertIn('0–2 years',page.locator('#opportunity-detail').inner_text())
            self.assertIn('Direct application / posting URL',page.locator('#opportunity-detail').inner_text())
            self.assertTrue(page.locator('#opportunity-detail a[href*="81a2044f"]').count())
            page.locator('#opportunity-dialog [data-close]').click()
            page.screenshot(path=str(ROOT/'screenshots/internships-desktop.png'))
            page.locator('#internships-status').select_option('Unverified')
            for text in page.locator('#internships-cards .opportunity-card').all_inner_texts():self.assertIn('Unverified',text)
            page.locator('#nav [data-tab="research"]').click()
            self.assertIn('IIT Madras',page.locator('#research-cards').inner_text())
            page.locator('[data-opportunity-detail="nitt-phd-jan2027"]').click()
            self.assertIn('BSc IT',page.locator('#opportunity-detail').inner_text())
            self.assertIn('11:59 pm IST',page.locator('#opportunity-detail').inner_text())
            page.locator('#opportunity-dialog [data-close]').click()
            page.locator('#nav [data-tab="remote"]').click()
            page.locator('[data-opportunity-detail="canonical-graduate-software"]').click()
            self.assertIn('2022',page.locator('#opportunity-detail').inner_text())
            self.assertIn('Manual only',page.locator('#opportunity-detail').inner_text())
            page.locator('#opportunity-dialog [data-close]').click()
            page.set_viewport_size({'width':390,'height':844})
            page.goto('http://127.0.0.1:8000/#internships')
            page.locator('#internships-cards .opportunity-card').first.wait_for()
            page.wait_for_timeout(250)
            page.locator('#internships-status').select_option('')
            page.evaluate('window.scrollTo(0,0)')
            self.assertTrue(page.evaluate('document.documentElement.scrollWidth<=innerWidth'))
            page.screenshot(path=str(ROOT/'screenshots/internships-mobile.png'))
            self.assertEqual(errors,[])
            browser.close()
    def test_live_catalog_views_read_only(self):
        with sync_playwright() as p:
            browser=p.chromium.launch(executable_path='C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',headless=True)
            page=browser.new_page(viewport={'width':1440,'height':1000})
            errors=[]
            page.on('pageerror',lambda e:errors.append(str(e)))
            page.goto('http://127.0.0.1:8000/#watchlist')
            page.locator('#watchlist-grid .company-card').first.wait_for()
            self.assertGreaterEqual(page.locator('#watchlist-grid .company-card').count(),12)
            self.assertTrue(page.locator('#view-watchlist').is_visible())
            self.assertGreater(page.locator('#watchlist-grid .company-card').nth(1).bounding_box()['x'],page.locator('#watchlist-grid .company-card').nth(0).bounding_box()['x'])
            page.screenshot(path=str(ROOT/'screenshots/medtech-watchlist-desktop.png'))
            page.locator('#company-region').select_option('Andhra Pradesh')
            for text in page.locator('#watchlist-grid .company-card').all_inner_texts():self.assertIn('Andhra Pradesh',text)
            page.locator('#nav [data-tab="portals"]').click()
            page.locator('#portal-grid .company-card').first.wait_for()
            self.assertIn('HirePro',page.locator('#portal-grid').inner_text())
            page.locator('[data-search-portal="naukri"]').click()
            self.assertTrue(page.locator('#discovery-dialog').is_visible())
            self.assertTrue(page.locator('[name="site"][value="naukri"]').is_checked())
            page.locator('#discovery-dialog [data-close]').first.click()
            page.locator('.sidebar [data-tab="settings"]').click()
            self.assertTrue(page.locator('#answers-editor').is_visible())
            self.assertTrue(page.locator('#policy-domains').is_visible())
            page.set_viewport_size({'width':390,'height':844})
            page.goto('http://127.0.0.1:8000/#watchlist')
            page.locator('#watchlist-grid .company-card').first.wait_for()
            page.wait_for_timeout(250)
            self.assertTrue(page.evaluate('document.documentElement.scrollWidth<=innerWidth'))
            page.screenshot(path=str(ROOT/'screenshots/medtech-watchlist-mobile.png'))
            self.assertEqual(errors,[])
            browser.close()
    def test_dashboard_workflow(self):
        with sync_playwright() as p:
            browser = p.chromium.launch(executable_path='C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe', headless=True)
            page = browser.new_page(viewport={"width": 1440, "height": 1050})
            errors = []
            page.on('pageerror', lambda error: errors.append(str(error)))
            job = {"id": 1, "title": "Python Developer", "company_name": "Example Labs", "location": "Remote", "status": "Matched", "source": "manual", "match_score": 88, "description": '<script>bad()</script>', "match_reason": "Python experience aligns.", "canonical_url": "https://example.com/role", "pdf_url": "/pdfs/test.pdf"}
            app = {"id": 1, "job_id": 1, "job_title": job['title'], "company": job['company_name'], "state": "Pending Approval", "updated_at": "2026-11-16T10:00:00"}
            calls = []
            def route(r):
                path = r.request.url.split('8000')[-1].split('?')[0]
                calls.append((r.request.method, path))
                if path == '/api/overview': data = {"total_jobs_discovered": 1, "jobs_matched": 1, "pending_approvals": 1, "applications_submitted": 0}
                elif path == '/api/jobs' and r.request.method == 'GET': data = [job]
                elif path == '/api/applications': data = [app]
                elif path.endswith('/score'): data = {"state": "Pending Approval"}
                elif path == '/api/jobs': data = {"status": "created"}
                elif path == '/api/applications/decide': data = {"status": "rejected"}
                else: data = {}
                r.fulfill(json=data)
            page.route('**/api/**', route)
            page.goto('http://127.0.0.1:8000')
            page.get_by_text('Example Labs', exact=True).first.wait_for()
            page.screenshot(path=str(ROOT/'screenshots/dashboard-redesign-desktop.png'), full_page=True)
            page.locator('#nav [data-tab="jobs"]').click()
            self.assertTrue(page.locator('#nav [data-tab="jobs"]').evaluate("e=>e.classList.contains('active')"))
            page.locator('#job-search').fill('no such company')
            self.assertIn('No matching opportunities', page.locator('#jobs-table').inner_text())
            page.locator('#job-search').fill('')
            page.locator('#jobs-table [data-detail]').click()
            self.assertTrue(page.locator('#detail-dialog').is_visible())
            self.assertIn('<script>bad()</script>', page.locator('#detail-body').inner_text())
            self.assertEqual(page.locator('#detail-body script').count(), 0)
            page.locator('#detail-dialog [data-close]').click()
            page.locator('#jobs-table [data-score]').click()
            page.wait_for_timeout(150)
            self.assertIn(('POST','/api/jobs/1/score'), calls)
            page.locator('[data-add]').first.click()
            for key,value in {'title':'Research Engineer','company_name':'Research Co','canonical_url':'https://example.com/new-role','description':'Python research'}.items():
                page.locator(f'#job-form [name="{key}"]').fill(value)
            page.locator('#save-job').click()
            page.wait_for_function("!document.getElementById('add-dialog').open")
            self.assertIn(('POST','/api/jobs'), calls)
            page.locator('#nav [data-tab="applications"]').click()
            page.locator('[data-decide][data-choice="reject"]').click()
            self.assertNotIn(('POST','/api/applications/decide'), calls)
            page.locator('#confirm-decision').click()
            page.wait_for_function("!document.getElementById('decision-dialog').open")
            page.wait_for_timeout(150)
            self.assertIn(('POST','/api/applications/decide'), calls)
            page.set_viewport_size({"width":390,"height":844})
            page.goto('http://127.0.0.1:8000/#overview')
            page.get_by_text('Example Labs', exact=True).first.wait_for()
            page.wait_for_timeout(250)
            page.locator('#toasts').evaluate('e=>e.replaceChildren()')
            self.assertTrue(page.evaluate('document.documentElement.scrollWidth <= innerWidth'))
            page.screenshot(path=str(ROOT/'screenshots/dashboard-redesign-mobile.png'), full_page=True)
            page.locator('#menu').click()
            page.locator('#nav [data-tab="resumes"]').click()
            self.assertTrue(page.locator('#view-resumes').is_visible())
            self.assertFalse(page.locator('#sidebar').evaluate("e=>e.classList.contains('open')"))
            page.route('**/api/**', lambda r:r.fulfill(status=500,json={'detail':'Test server unavailable'}))
            page.locator('#refresh').click()
            page.locator('#error-banner:not(.hidden)').wait_for()
            self.assertIn('Test server unavailable',page.locator('#error-banner').inner_text())
            self.assertEqual(errors, [])
            browser.close()

if __name__ == '__main__':
    unittest.main()
