"""Public career-page monitoring. Only identifiable job records become jobs."""
import hashlib
import json
import re
from urllib.parse import urljoin, urlsplit, urlunsplit, parse_qsl, urlencode
import requests
from bs4 import BeautifulSoup

def canonical_url(url):
    p=urlsplit(url.strip())
    if p.scheme not in ['http','https'] or not p.hostname:
        raise ValueError('Use an HTTP or HTTPS URL.')
    query=urlencode(sorted((k,v) for k,v in parse_qsl(p.query) if not k.lower().startswith('utm_') and k.lower() not in ['trk','trackingid','refid']))
    return urlunsplit((p.scheme.lower(),p.netloc.lower(),p.path.rstrip('/') or '/',query,p.fragment if p.fragment.startswith('/') else ''))

def fetch(url):
    response=requests.get(url,timeout=(8,20),headers={'User-Agent':'JobHunterCareerMonitor/1.0 (personal career-page monitoring)'})
    response.raise_for_status()
    if 'html' not in response.headers.get('content-type','').lower() and 'json' not in response.headers.get('content-type','').lower():
        raise ValueError('This page needs manual review (not HTML/JSON).')
    return response

def _location(item):
    loc=item.get('jobLocation') or []
    if isinstance(loc,dict):loc=[loc]
    parts=[]
    for entry in loc:
        address=entry.get('address',{}) if isinstance(entry,dict) else {}
        if isinstance(address,str): parts.append(address)
        else: parts.append(', '.join(str(address.get(k,'')) for k in ['addressLocality','addressRegion','addressCountry'] if address.get(k)))
    return '; '.join(filter(None,parts)) or ('Remote' if item.get('jobLocationType')=='TELECOMMUTE' else 'Location not stated')

def structured_jobs(soup,url,company):
    jobs=[]
    def visit(node):
        if isinstance(node,list):
            for n in node:visit(n)
        elif isinstance(node,dict):
            kind=node.get('@type',[])
            if kind=='JobPosting' or (isinstance(kind,list) and 'JobPosting' in kind):
                title=node.get('title')
                target=node.get('url') or url
                if title:
                    org=node.get('hiringOrganization') or {}
                    jobs.append({'title':str(title),'company_name':org.get('name',company) if isinstance(org,dict) else company,'canonical_url':canonical_url(urljoin(url,str(target))),'location':_location(node),'description':BeautifulSoup(node.get('description',''),'html.parser').get_text(' ',strip=True),'source':'company_careers'})
            for key,value in node.items():
                if isinstance(value,(dict,list)):visit(value)
    for tag in soup.select('script[type="application/ld+json"]'):
        try:visit(json.loads(tag.string or tag.get_text()))
        except (ValueError,TypeError):pass
    return jobs

def collect_careers(company):
    url=company['careers_url']
    response=fetch(url)
    soup=BeautifulSoup(response.text,'html.parser')
    visible=BeautifulSoup(response.text,'html.parser')
    for el in visible.select('script,style,nav,footer,header'):el.decompose()
    text=visible.get_text(' ',strip=True)
    if re.search(r'verify you are human|checking your browser|access denied',text,re.I):
        raise ValueError('Site requires a browser/security check; open the careers page manually.')
    fingerprint=hashlib.sha256(text.encode()).hexdigest()
    links=[]
    for anchor in soup.select('a[href]'):
        target=urljoin(response.url,anchor['href'])
        if urlsplit(target).scheme not in ['http','https']:continue
        if re.search(r'career|/jobs?/|opening|recruit|lever\.co|greenhouse\.io|ashbyhq|notification',target,re.I):
            entry={'title':anchor.get_text(' ',strip=True)[:180] or 'Career link','url':target}
            if entry not in links and target!=response.url:links.append(entry)
    jobs=structured_jobs(soup,response.url,company['name'])
    # Lever's public postings feed is linked by the official Dozee careers page.
    host=urlsplit(response.url).hostname or ''
    path=urlsplit(response.url).path.strip('/').split('/')
    if host=='jobs.lever.co' and len(path)==1:
        feed=fetch(f'https://api.lever.co/v0/postings/{path[0]}?mode=json').json()
        for item in feed:
            jobs.append({'title':item['text'],'company_name':company['name'],'canonical_url':canonical_url(item.get('applyUrl') or item['hostedUrl']),'location':item.get('categories',{}).get('location') or 'Location not stated','description':item.get('descriptionPlain',''),'source':'company_careers'})
    # Follow a bounded number of individual career links, not arbitrary whole-site crawling.
    ownhost=urlsplit(response.url).hostname
    if not jobs:
        candidates=[l for l in links if urlsplit(l['url']).hostname==ownhost and re.search(r'/(job|jobs|career|careers)/[^/#?]+',urlsplit(l['url']).path)]
        for entry in candidates[:6]:
            try:
                detail=fetch(entry['url'])
                jobs.extend(structured_jobs(BeautifulSoup(detail.text,'html.parser'),detail.url,company['name']))
            except Exception:pass
    unique={j['canonical_url']:j for j in jobs}
    return {'jobs':list(unique.values()),'content_hash':fingerprint,'links':links[:25],'page_title':soup.title.get_text(strip=True) if soup.title else '', 'status':'Jobs collected' if jobs else 'Page monitored · manual review', 'note':None if jobs else 'No structured job records found. Page changes and career links are tracked; no placeholder jobs are created.'}
