"""Portal capabilities are explicit; a listing source is not a submission adapter."""
from urllib.parse import urlsplit

PORTALS = [
    {"id":"ai-work-accounts","name":"AI-training account platforms","domains":["mercor.com","turing.com","micro1.ai","outlier.ai"],"search":False,"application":"manual","note":"Use Connections for saved sign-in. Sign-up, identity checks, assessments and interviews remain manual."},
    {"id":"freelance-accounts","name":"Freelance marketplace accounts","domains":["upwork.com","fiverr.com","freelancer.com","peopleperhour.com"],"search":False,"application":"manual","note":"Use Connections for saved sign-in. Marketplace proposals and posting remain manual."},
    {"id":"canonical","name":"Canonical application policy","domains":["canonical.com"],"search":False,"application":"manual","note":"Review each role's application policy. The reviewed graduate form disallows AI-generated answers; use manual applications."},
    {"id": "naukri", "name": "Naukri", "domains": ["naukri.com"], "search": True, "login_url": "https://www.naukri.com/nlogin/login", "application": "assisted", "note": "Login required. One-click apply may use your saved portal resume; opt in separately."},
    {"id": "hirepro", "name": "HirePro", "domains": ["hirepro.in"], "search": False, "application": "assisted", "note": "Import an employer-specific registration or application URL. Assessments and identity checks remain manual."},
    {"id": "greenhouse", "name": "Greenhouse", "domains": ["greenhouse.io"], "search": False, "application": "form", "note": "Employer career links; supported labelled fields and resume uploads."},
    {"id": "lever", "name": "Lever", "domains": ["lever.co"], "search": False, "application": "form", "note": "Employer career links; supported labelled fields and resume uploads."},
    {"id": "ashby", "name": "Ashby", "domains": ["ashbyhq.com"], "search": False, "application": "form", "note": "Employer career links. Custom questions may need your input."},
    {"id": "workday", "name": "Workday", "domains": ["myworkdayjobs.com", "myworkdaysite.com"], "search": False, "application": "assisted", "note": "Employer account, custom controls, and complex steps may require manual completion."},
    {"id": "linkedin", "name": "LinkedIn", "domains": ["linkedin.com"], "search": True, "application": "employer_link", "note": "Discovery only. Import the employer's original application URL to apply."},
    {"id": "indeed", "name": "Indeed", "domains": ["indeed.com", "indeed.co.in"], "search": True, "application": "employer_link", "note": "Discovery only. Import the employer's original application URL to apply."},
    {"id": "glassdoor", "name": "Glassdoor", "domains": ["glassdoor.com", "glassdoor.co.in"], "search": True, "application": "employer_link", "note": "Discovery only; use an employer application link."},
    {"id": "zip_recruiter", "name": "ZipRecruiter", "domains": ["ziprecruiter.com"], "search": True, "application": "employer_link", "note": "Discovery only; coverage depends on country."},
    {"id": "bayt", "name": "Bayt", "domains": ["bayt.com"], "search": True, "application": "employer_link", "note": "Discovery, primarily Middle East; use the employer application link."},
    {"id": "bdjobs", "name": "BDJobs", "domains": ["bdjobs.com"], "search": True, "application": "employer_link", "note": "Bangladesh discovery; use the employer application link."},
    {"id": "hellowork", "name": "HelloWork", "domains": ["hellowork.com"], "search": True, "application": "employer_link", "note": "France discovery; use the employer application link."},
]

def portal_for_url(url):
    host = (urlsplit(url).hostname or '').lower()
    for portal in PORTALS:
        if any(host == d or host.endswith('.' + d) for d in portal['domains']):
            return portal
    return {"id": "employer", "name": "Employer careers", "application": "form", "note": "Generic labelled form support; custom controls may need manual input."}
