import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))

class ConnectionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp=tempfile.TemporaryDirectory();cls.root=Path(cls.temp.name)
        os.environ['JOB_HUNTER_DATABASE']=str(cls.root/'test.db')
        from services.integration_bridge.api import app,engine
        from fastapi.testclient import TestClient
        cls.engine=engine;cls.client=TestClient(app)
    @classmethod
    def tearDownClass(cls):cls.client.close();cls.engine.dispose();cls.temp.cleanup()
    def setUp(self):
        self.state=patch('services.integration_bridge.connections.SAVED',self.root/('connections-'+self._testMethodName+'.json'));self.state.start();self.addCleanup(self.state.stop)
        self.browser=patch('services.integration_bridge.connections.project_browser');self.mock=self.browser.start();self.addCleanup(self.browser.stop)
        self.mock.status.return_value={'running':False,'profile_exists':False}
        self.mock.open_url.return_value={'status':'Opened in project browser'}
    def test_signin_confirmation_is_metadata_only(self):
        self.assertEqual(self.client.post('/api/connections/naukri/confirm').status_code,409)
        self.assertEqual(self.client.post('/api/connections/naukri/open',json={}).status_code,200)
        self.assertEqual(self.client.post('/api/connections/naukri/confirm').status_code,200)
        rows=self.client.get('/api/connections').json()['connections']
        naukri=next(r for r in rows if r['id']=='naukri')
        self.assertTrue(naukri['confirmed_at'])
        import services.integration_bridge.connections as module
        stored=module.read_saved()['naukri']
        self.assertEqual(set(stored),{'url','last_opened_at','confirmed_at'})
        self.assertEqual(self.client.post('/api/connections/naukri/mark-reconnect').status_code,200)
        self.assertNotIn('confirmed_at',module.read_saved()['naukri'])
    def test_get_link_does_not_launch_browser(self):
        self.assertEqual(self.client.get('/connect/naukri').status_code,200)
        self.mock.open_url.assert_not_called()
    def test_requested_job_boards_have_project_browser_links(self):
        rows={r['id']:r for r in self.client.get('/api/connections').json()['connections']}
        expected={'hiringcafe','wellfound','himalayas','ycombinator','weworkremotely','welcome-to-the-jungle','zip_recruiter'}
        self.assertTrue(expected<=set(rows))
        for key in expected:
            self.assertEqual(rows[key]['group'],'Job portals')
            self.assertEqual(self.client.get('/connect/'+key).status_code,200)
            self.assertEqual(self.client.post('/api/connections/'+key+'/open',json={}).status_code,200)
            self.mock.open_url.assert_called_with(rows[key]['url'])
        portals={r['id']:r for r in self.client.get('/api/portals').json()}
        self.assertTrue(portals['zip_recruiter']['search_available'])
        self.assertTrue(all(not portals[key]['search_available'] for key in expected-{'zip_recruiter'}))
    def test_employer_account_needs_specific_url(self):
        self.assertEqual(self.client.post('/api/connections/hirepro/open',json={}).status_code,422)
        created=self.client.post('/api/connections',json={'name':'Example employer','url':'https://example.com/candidate','group':'Employer accounts'}).json()
        self.assertEqual(self.client.post('/api/connections/'+created['id']+'/open',json={}).status_code,200)
        self.mock.open_url.assert_called_once_with('https://example.com/candidate')
    def test_url_credentials_and_executable_schemes_rejected(self):
        for url in ['javascript:alert(1)','file:///C:/Windows','https://name:password@example.com','http://localhost:9223','https://example.com:notaport']:
            self.assertEqual(self.client.post('/api/connections',json={'name':'Invalid','url':url}).status_code,422)
        self.assertEqual(self.client.post('/api/connections',json={'name':'   ','url':'https://example.com'}).status_code,422)
    def test_alternate_url_cannot_launch_before_validation(self):
        self.assertEqual(self.client.post('/api/connections/naukri/open',json={'url':'https://another.example.com'}).status_code,409)
        self.mock.open_url.assert_not_called()
    def test_external_origin_cannot_open_browser(self):
        self.assertEqual(self.client.post('/api/project-browser/open',headers={'Origin':'https://untrusted.example'}).status_code,403)
        self.mock.open_url.assert_not_called()

if __name__=='__main__':unittest.main()
