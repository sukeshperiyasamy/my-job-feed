"""Local-only account-state fixtures; no real account cookies/passwords read."""
import sys
import socket
import tempfile
import threading
import time
import unittest
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
from unittest.mock import patch
from playwright.sync_api import sync_playwright
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from services.browser_manager.project_browser import ProjectBrowser
from services.browser_manager.browser import DedicatedBrowserManager

def free_port():
    with socket.socket() as s:
        s.bind(('127.0.0.1',0));return s.getsockname()[1]

class FixtureHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200);self.send_header('Content-Type','text/html');self.end_headers();self.wfile.write(b'<h1>Local project-browser fixture</h1>')
    def log_message(self,*args):pass

class ProjectBrowserTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp=tempfile.TemporaryDirectory();cls.root=Path(cls.temp.name)
        cls.server=ThreadingHTTPServer(('127.0.0.1',0),FixtureHandler)
        threading.Thread(target=cls.server.serve_forever,daemon=True).start()
        cls.url=f'http://127.0.0.1:{cls.server.server_port}/'
        cls.browser=ProjectBrowser(cls.root/'fixture-profile',cls.root/'state.json',port=free_port(),headless=True)
    @classmethod
    def close_fixture_browser(cls):
        if not cls.browser.running():return
        with sync_playwright() as p:
            b=p.chromium.connect_over_cdp(cls.browser.endpoint)
            try:b.new_browser_cdp_session().send('Browser.close')
            except Exception:pass
        for _ in range(50):
            if not cls.browser._owner():break
            time.sleep(.1)
        if cls.browser._process:cls.browser._process.poll()
    @classmethod
    def tearDownClass(cls):
        cls.close_fixture_browser();cls.server.shutdown();cls.server.server_close();time.sleep(.3);cls.temp.cleanup()
    def test_foreign_listener_is_never_attached(self):
        foreign=ProjectBrowser(self.root/'foreign-profile',self.root/'foreign.json',port=self.server.server_port,headless=True)
        with self.assertRaisesRegex(RuntimeError,'another process'):foreign.ensure_running()
    def test_shared_worker_keeps_user_tabs_and_saved_state(self):
        browser=self.browser
        browser.open_url(self.url)
        self.assertTrue(browser.running())
        with sync_playwright() as p:
            attached=p.chromium.connect_over_cdp(browser.endpoint)
            context=attached.contexts[0]
            context.add_cookies([{'name':'fixture-persistent-state','value':'local-test-only','url':self.url,'expires':time.time()+86400}])
            user=context.new_page();user.goto(self.url+'user-account')
        with patch('services.browser_manager.project_browser.project_browser',browser):
            manager=DedicatedBrowserManager(profile_name='fixture-shared',shared_project=True)
            try:
                manager.start();manager.navigate(self.url+'application')
                other=manager._context.new_page();other.goto(self.url+'unrelated-account')
                self.assertEqual(len(manager.application_pages()),1)
                self.assertTrue(manager.application_pages()[0].url.endswith('/application'))
            finally:manager.close()
        self.assertTrue(browser.running())
        with sync_playwright() as p:
            attached=p.chromium.connect_over_cdp(browser.endpoint)
            context=attached.contexts[0]
            urls=[page.url for page in context.pages]
            self.assertIn(self.url+'user-account',urls)
            self.assertIn(self.url+'unrelated-account',urls)
            self.assertNotIn(self.url+'application',urls)
            self.assertTrue(any(c['name']=='fixture-persistent-state' for c in context.cookies(self.url)))
        # A fresh client can reconnect; worker cleanup did not shut down the browser.
        self.assertTrue(browser.running())
        self.close_fixture_browser()
        browser.ensure_running()
        with sync_playwright() as p:
            attached=p.chromium.connect_over_cdp(browser.endpoint)
            cookies=attached.contexts[0].cookies(self.url)
            self.assertTrue(any(c['name']=='fixture-persistent-state' for c in cookies))

if __name__=='__main__':unittest.main()
