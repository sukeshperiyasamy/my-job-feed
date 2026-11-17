"""Deterministic applicant screening; no network or personal account access."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from services.job_collector.matching import assess_job,campaign_config,search_plan

class MatchingTests(unittest.TestCase):
    def test_plan_covers_all_lanes_and_locations(self):
        config=campaign_config();plan=search_plan(config)
        self.assertEqual(len({p['campaign_id'] for p in plan[:7]}),7)
        self.assertTrue({'Bengaluru','Chennai','Coimbatore','Mysuru','Visakhapatnam','Remote','India'}<={p['location'] for p in plan})
        self.assertTrue(all(p['campaign_id']=='research' for p in search_plan(config,['research'])))
        with self.assertRaises(ValueError):search_plan(config,['unknown'])
    def test_entry_level_positive_is_not_eligibility_guarantee(self):
        result=assess_job('Junior Embedded Engineer','0–2 years of relevant experience. Python and ESP32.','Chennai')
        self.assertEqual(result['status'],'potential_match')
        self.assertTrue(result['entry_level_signal'])
        self.assertIn('embedded',[x['id'] for x in result['campaigns']])
    def test_required_high_experience_and_senior_titles(self):
        for title,desc in [('Software Engineer','Minimum 4 years of industry experience required.'),('Senior Embedded Engineer','Firmware development'),('Python Engineer','Experience: 3-5 years'),('Lead Software Engineer','Python'),('Staff Software Engineer','Python'),('Design Quality Manager','Medical devices')]:
            self.assertEqual(assess_job(title,desc)['status'],'outside_target')
    def test_dotnet_is_not_an_exam_requirement(self):
        result=assess_job('Junior Software Engineer','.NET required. Python preferred.')
        self.assertFalse(any(f['kind']=='exam' for f in result['flags']))
    def test_preferred_experience_stays_visible(self):
        result=assess_job('Python Developer','3–5 years experience preferred; freshers may apply.')
        self.assertEqual(result['status'],'needs_review')
    def test_degree_duration_not_treated_as_work_experience(self):
        result=assess_job('Junior Software Engineer','Four-year degree or 3 years MCA course.')
        self.assertEqual(result['experience'],[])
        self.assertNotEqual(result['status'],'outside_target')
    def test_mandatory_exam_and_funding_condition_are_separate(self):
        result=assess_job('JRF Biosensors','GATE or NET is mandatory. Raman spectroscopy.')
        self.assertEqual(result['status'],'outside_target')
        result=assess_job('JRF Biosensors','GATE required for institute assistantship; project-funded positions subject to separate eligibility.')
        self.assertEqual(result['status'],'needs_review')
        self.assertIn('funding',result['flags'][0]['message'])
    def test_exam_waiver_or_alternative_is_not_automatic_eligibility(self):
        for desc in ['GATE is not required for M.Tech candidates.','NET required or M.Tech degree accepted.']:
            self.assertEqual(assess_job('Research Assistant Biosensor',desc)['status'],'needs_review')
    def test_degree_and_student_restrictions_are_reviewed(self):
        result=assess_job('Software Intern','Eligibility: B.Tech ECE only; currently enrolled students graduating in 2027.')
        kinds={f['kind'] for f in result['flags']}
        self.assertTrue({'degree','student_status'}<=kinds)
        self.assertEqual(result['status'],'needs_review')
    def test_remote_does_not_assume_india_eligibility(self):
        result=assess_job('Junior AI Engineer','Applicants must be based in the United States.','Remote')
        self.assertTrue({'country','remote'}<={f['kind'] for f in result['flags']})
        self.assertEqual(result['status'],'needs_review')
    def test_missing_description_and_unrelated_internship_need_review(self):
        self.assertEqual(assess_job('Python Engineer')['status'],'needs_review')
        self.assertEqual(assess_job('Sales Intern','Freshers welcome')['status'],'needs_review')

if __name__=='__main__':unittest.main()
