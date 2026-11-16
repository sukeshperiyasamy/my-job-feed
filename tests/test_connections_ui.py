"""Dashboard interactions mock actions; no real account is opened or changed."""
import unittest
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]

class ConnectionUITests(unittest.TestCase):
    def test_connection_page_and_open_actions(self):
        with sync_playwright() as p:
            browser=p.chromium.launch(executable_path='C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',headless=True)
            page=browser.new_page(viewport={'width':1440,'height':1000});errors=[];calls=[]
            page.on('pageerror',lambda e:errors.append(str(e)))
            def route(r):
                if r.request.method!='POST':r.continue_();return
                calls.append(r.request.url)
                r.fulfill(json={'id':'custom-fixture','status':'Opened in project browser'})
            page.route('**/api/connections**',route)
            page.route('**/api/project-browser/open',lambda r:(calls.append(r.request.url),r.fulfill(json={'status':'Opened in project browser'})))
            page.goto('http://127.0.0.1:8000/#connections')
            page.locator('#connection-cards .company-card').first.wait_for()
            self.assertGreaterEqual(page.locator('#connection-cards .company-card').count(),18)
            for name in ['HiringCafe','Wellfound','Himalayas','Y Combinator Jobs','We Work Remotely','Welcome to the Jungle','ZipRecruiter']:
                self.assertIn(name,page.locator('#connection-cards').inner_text())
            page.locator('#open-project-browser').click()
            self.assertTrue(any(url.endswith('/api/project-browser/open') for url in calls))
            page.locator('[data-open-connection="naukri"]').click()
            self.assertTrue(any(url.endswith('/naukri/open') for url in calls))
            page.locator('[data-open-connection="workday"]').click()
            self.assertTrue(page.locator('#connection-dialog').is_visible())
            page.locator('#connection-form [name="name"]').fill('Example employer · Workday')
            page.locator('#connection-form [name="url"]').fill('https://example.com/candidate')
            page.locator('#save-open-connection').click()
            page.wait_for_function("!document.getElementById('connection-dialog').open")
            self.assertTrue(any(url.endswith('/api/connections/custom-fixture/open') for url in calls))
            page.locator('#connection-search').fill('naukri')
            self.assertEqual(page.locator('#connection-cards .company-card').count(),1)
            self.assertEqual(page.locator('#view-connections input[type="password"]').count(),0)
            page.locator('#connection-search').fill('')
            page.locator('#toasts').evaluate('e=>e.replaceChildren()')
            page.evaluate('window.scrollTo(0,0)')
            page.screenshot(path=str(ROOT/'screenshots/connections-desktop.png'))
            page.set_viewport_size({'width':390,'height':844});page.evaluate('window.scrollTo(0,0)');page.wait_for_timeout(250)
            self.assertTrue(page.evaluate('document.documentElement.scrollWidth<=innerWidth'))
            page.screenshot(path=str(ROOT/'screenshots/connections-mobile.png'))
            self.assertEqual(errors,[])
            browser.close()

if __name__=='__main__':unittest.main()
