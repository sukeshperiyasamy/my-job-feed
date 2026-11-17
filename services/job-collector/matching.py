"""Conservative text screening, not an employer eligibility decision.

Every restriction includes source text. Missing or ambiguous requirements stay
under review; a relevant keyword never proves degree equivalence or eligibility.
"""
import json
import re
from pathlib import Path
from bs4 import BeautifulSoup

CONFIG=Path(__file__).resolve().parents[2]/'config'/'search-campaigns.json'

def campaign_config():
    return json.loads(CONFIG.read_text(encoding='utf-8'))

def search_plan(config, campaign_ids=None):
    selected=set(campaign_ids or [c['id'] for c in config['campaigns']])
    unknown=selected-{c['id'] for c in config['campaigns']}
    if unknown:raise ValueError('Unknown search campaign: '+', '.join(sorted(unknown)))
    # Interleave lanes so small batches cover multiple technical interests.
    groups=[]
    for c in config['campaigns']:
        if c['id'] in selected:
            groups.append([{'campaign_id':c['id'],'campaign':c['name'],'search_term':q,'location':loc}
                           for loc in c.get('locations',config['locations']) for q in c['queries']])
    return [g[i] for i in range(max(map(len,groups),default=0)) for g in groups if i<len(g)]

def assess_job(title, description='', location='', config=None):
    config=config or campaign_config()
    title=BeautifulSoup(title or '', 'html.parser').get_text(' ',strip=True)
    description=BeautifulSoup(description or '', 'html.parser').get_text('\n',strip=True)
    text=title+'\n'+description
    lower=text.lower()
    lanes=[c for c in config['campaigns'] if any(re.search(r'(?<!\w)'+re.escape(k)+r'(?!\w)',lower) for k in c['keywords'])]
    flags=[]
    def flag(kind,severity,evidence,message):
        flags.append({'kind':kind,'severity':severity,'evidence':evidence[:350],'message':message})
    max_years=config['applicant']['max_experience_years']
    # Aggregator country facets can conflict with the visible job location.
    foreign=r'\b(?:philippines|singapore|united states|usa|united kingdom|canada|germany|australia|netherlands|poland|japan|china|france|ireland|brazil|mexico)\b'
    if re.search(foreign,location or '',re.I) and not re.search(r'\bindia\b|bengaluru|bangalore|chennai|coimbatore|hyderabad|pune|delhi',location or '',re.I):
        flag('location','review' if re.search(r'remote|global|worldwide|anywhere',location or '',re.I) else 'exclude',location,'Visible location is outside India; aggregator country tags do not establish India eligibility.')
    experience=[]
    # Restrict parsing to explicit years-of-experience phrases, not degree length.
    pattern=r'(?P<min>\d+(?:\.\d+)?)\s*(?:[-–—]|to)\s*(?P<max>\d+(?:\.\d+)?)\s*years?\s*(?:of\s+)?(?:(?:relevant|professional|industry|work|hands[- ]on|related|prior)\s+){0,3}experience|(?:(?P<prefix>minimum|at least)\s+)?(?P<single>\d+(?:\.\d+)?)\s*(?P<plus>\+)?\s*years?\s*(?:of\s+)?(?:(?:relevant|professional|industry|work|hands[- ]on|related|prior)\s+){0,3}experience'
    pattern+=r'|experience\s*[:\-]?\s*(?P<emin>\d+(?:\.\d+)?)\s*(?:[-–—]|to)\s*(?P<emax>\d+(?:\.\d+)?)\s*years?'
    for match in re.finditer(pattern,lower):
        lo=float(match['min'] or match['single'] or match['emin'])
        hi=float(match['max'] or match['emax']) if match['max'] or match['emax'] else None
        context=lower[max(0,match.start()-90):min(len(lower),match.end()+100)]
        preferred=bool(re.search(r'prefer(?:red|able)?|desirable|optional|nice to have',context))
        negated=bool(re.search(r'not required|not mandatory|no minimum',context))
        experience.append({'minimum':lo,'maximum':hi,'evidence':match.group(),'preferred':preferred or negated})
        if lo>max_years:
            flag('experience','review' if preferred or negated else 'exclude',match.group(),f'{lo:g}+ years stated; target is 0–{max_years} years.' if not preferred else 'Higher experience is preferred; verify flexibility.')
    if re.search(r'\b(senior|sr\.?|principal|staff(?:\s+\w+){0,2}\s+engineer|lead|engineer\s*(?:iii|iv|v|[3-9])|(?:engineering|quality|regulatory|technical|operations) manager|director)\b',title,re.I):
        flag('seniority','exclude',title,'Title indicates a role above the entry-level search target.')
    if re.search(r'creator program|talent (?:pool|community)|general application',title,re.I):
        flag('posting_type','exclude',title,'Programme/talent-pool entry rather than a specific target job vacancy.')
    entry=bool(re.search(r'\b(fresher|freshers|entry[- ]level|graduate trainee|graduate engineer|junior|intern(?:ship)?|trainee|engineer i|associate engineer)\b',title,re.I)) or any(e['minimum']<=max_years and not e['preferred'] for e in experience)
    # Parse local clauses so a waiver elsewhere never cancels a mandatory exam.
    clauses=[s.strip() for s in re.split(r'[\n;!?]+|\.(?=\s+[A-Z])',description) if s.strip()]
    held={x.upper() for x in config['applicant'].get('exams_held',[])}
    for clause in clauses:
        exams={x.upper() for x in re.findall(r'(?<![.\w])(GATE|CEED|NET|CSIR[- ]NET|UGC[- ]NET)\b',clause,re.I)}-held
        if not exams:continue
        waived=bool(re.search(r'not (?:required|mandatory)|without (?:a )?(?:gate|net|ceed)|waiv|exempt|\bor\b.{0,40}(?:m\.?tech|master|project.fund)',clause,re.I))
        mandatory=bool(re.search(r'mandatory|must|essential|required|shall|only.*(?:qualified|valid)|(?:qualified|valid).*(?:only|essential)',clause,re.I))
        funding=bool(re.search(r'assistantship|institute (?:fund|fellowship)|stipend|fellowship|higher.*(?:pay|rate)',clause,re.I))
        severity='review' if waived or funding or not mandatory else 'exclude'
        flag('exam',severity,clause,('Exam waiver/project-funded eligibility needs confirmation.' if waived else 'Exam condition may restrict funding; project-funded admission must be checked separately.' if funding else 'Required exam is not in your verified qualifications.' if mandatory else 'Exam mentioned; verify whether it is mandatory.'))
    for clause in clauses:
        if re.search(r'\b(?:b\.?tech|b\.?e\.?|m\.?tech|mca|degree|bachelor|master|ph\.?d)\b',clause,re.I) and re.search(r'eligib|qualif|require|must|only|essential',clause,re.I):
            flag('degree','review',clause,'Verify exact degree/discipline eligibility. M.Tech Medical Technology or MCA equivalence is not assumed.')
        if re.search(r'currently enrolled|current student|graduat(?:ing|ion|ed).{0,35}20\d{2}|20\d{2}.{0,25}(?:batch|graduates)',clause,re.I):
            flag('student_status','review',clause,'Check enrollment and graduation-year restrictions against your profile.')
        if re.search(r'(?:only|must|restricted|based|resident|reside|authorized|authorised|eligible).{0,55}(?:united states|usa|u\.?s\.?|canada|united kingdom|uk|europe|eu\b)|(?:us|usa|uk|eu|canada)[- ]only|(?:citizen|citizenship|work authorization|work authorisation)',clause,re.I):
            flag('country','review',clause,'Country, residency or work-authorization restriction needs verification; India eligibility is not assumed.')
    remote=bool(re.search(r'\bremote\b',str(location)+' '+text,re.I))
    if remote:
        flag('remote','review',str(location) or 'Remote listing','Remote does not prove hiring from India. Verify the employer’s country policy.')
    if not experience and not entry:
        flag('experience','review','Experience requirement not explicitly found','Check required experience in the original listing.')
    relevant=bool([c for c in lanes if c['id']!='internships'])
    if not relevant:
        flag('discipline','review',title,'No clear technical/research lane match found; inspect the role before tailoring.')
    excluded=any(f['severity']=='exclude' for f in flags)
    status='outside_target' if excluded else 'needs_review' if flags or not description else 'potential_match'
    return {'status':status,'label':{'outside_target':'Outside target','needs_review':'Needs review','potential_match':'Potential match'}[status],
            'entry_level_signal':entry,'campaigns':[{'id':c['id'],'name':c['name']} for c in lanes],
            'recommended_resume':next((c['resume'] for c in lanes if c['id']!='internships'),'Review discipline first'),
            'experience':experience,'flags':flags,'note':'Text screening only; confirm the current original listing. Not an admission or eligibility guarantee.'}
