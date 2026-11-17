"""Exercise both new pages without writing fixture records into the live database."""
import unittest,requests
from playwright.sync_api import sync_playwright

class ExtendedUITests(unittest.TestCase):
    def test_discovery_actions_and_freelance_pipeline(self):
        base='http://127.0.0.1:8000'
        freelance=requests.get(base+'/api/freelancing').json();freelance['leads']=[]
        extended=requests.get(base+'/api/extended-search').json();extended['latest']=None
        calls=[]
        with sync_playwright() as p:
            browser=p.chromium.launch(channel='msedge',headless=True)
            page=browser.new_page(viewport={'width':1440,'height':1050});errors=[]
            page.on('pageerror',lambda e:errors.append(str(e)))
            def tracker(route):
                req=route.request;path=req.url.split('/api/freelancing')[1]
                if req.method=='GET':route.fulfill(json=freelance);return
                if path=='/leads':
                    lead={**req.post_data_json,'id':999,'status':'Saved','proposal':''};freelance['leads']=[lead];route.fulfill(status=201,json=lead)
                elif path.endswith('/draft'):route.fulfill(json={'proposal':'Hello, editable fixture proposal.'})
                else:
                    freelance['leads'][0].update(req.post_data_json);route.fulfill(json=freelance['leads'][0])
            page.route('**/api/freelancing**',tracker)
            page.route('**/api/extended-search',lambda r:r.fulfill(json=extended))
            def scan(route):
                calls.append(route.request.post_data_json)
                extended['latest']={'kind':'extended_search','status':'Completed','new_jobs':2,'results':[{'name':'Python','fetched':9,'new_jobs':2,'duplicates':3,'excluded':4,'invalid':0,'needs_review':1}]}
                route.fulfill(json=extended['latest'])
            page.route('**/api/extended-search/run',scan)
            page.goto(base+'/#discovery');page.locator('#extended-run').click()
            page.wait_for_function("document.getElementById('extended-results').textContent.includes('3 already saved')")
            self.assertEqual(calls[0]['max_searches'],6);self.assertFalse(calls[0]['remote'])
            page.locator('#nav [data-tab="freelancing"]').click();page.locator('#freelance-add').click()
            form=page.locator('#freelance-add-form')
            form.locator('[name="title"]').fill('Python CSV automation')
            form.locator('[name="url"]').fill('https://example.com/project/fixture')
            form.locator('[name="description"]').fill('<script>fake project text</script>')
            form.locator('button[type="submit"],button.btn.primary').click()
            page.locator('[data-freelance-edit="999"]').click();page.locator('#freelance-draft').click()
            page.wait_for_function("document.getElementById('freelance-proposal').value.includes('editable fixture')")
            page.locator('#freelance-proposal').fill('My edited proposal.')
            page.locator('#freelance-stage').select_option('Proposal sent')
            page.locator('#freelance-edit-form .modal-foot .primary').click()
            page.wait_for_function("document.getElementById('freelance-summary').textContent.includes('1 proposals sent')")
            page.reload();page.locator('[data-freelance-edit="999"]').click()
            self.assertEqual(page.locator('#freelance-proposal').input_value(),'My edited proposal.')
            self.assertEqual(page.locator('#freelance-brief script').count(),0)
            page.set_viewport_size({'width':390,'height':844})
            self.assertFalse(page.evaluate('document.documentElement.scrollWidth>innerWidth'))
            self.assertEqual(errors,[]);browser.close()
if __name__=='__main__':unittest.main()
