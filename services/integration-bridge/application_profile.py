"""Application answer UI API, separate from resume facts and website credentials."""
from typing import Literal
from fastapi import APIRouter,HTTPException
from pydantic import BaseModel,Field
from services.application_engine import answer_store as store
from services.resume_engine.engine import VerifiedFactsStore

class AnswerInput(BaseModel):
    label:str=Field(min_length=1,max_length=500)
    value:str|bool|int|float|None=None
    scope:Literal['global','site','application']='global'
    url:str=Field(default='',max_length=2048)
    aliases:list[str]=Field(default_factory=list,max_length=15)
    skip:bool=False
    question_id:str|None=None
    kind:Literal['text','checkbox','select','radio']='text'

COMMON=[('Full name','Contact & links',['Full legal name','Candidate name','Your name'],'full_name'),('Email address','Contact & links',['Email','Candidate email'],'email'),('Phone number','Contact & links',['Mobile number','Contact number','Phone'],'phone'),('Current location','Contact & links',['Current city','Location'],'location'),('LinkedIn URL','Contact & links',['LinkedIn profile URL','LinkedIn'],'linkedin'),('GitHub URL','Contact & links',['GitHub profile','GitHub'],'github'),('Notice period','Availability & pay',[],None),('Expected salary','Availability & pay',[],None),('Current salary','Availability & pay',[],None),('Willing to relocate','Availability & pay',[],None),('Earliest start date','Availability & pay',[],None),('Highest qualification','Education & experience',[],None),('Years of relevant experience','Education & experience',[],None),('Work authorization in India','Eligibility',[],None),('Require visa sponsorship','Eligibility',[],None),('Portfolio URL','Contact & links',[],None)]
COMMON.extend([(label,group,[],None) for label,group in [('Address','Contact & links'),('Postal code','Contact & links'),('Country','Contact & links'),('University','Education & experience'),('Graduation year','Education & experience'),('CGPA','Education & experience'),('Current employer','Education & experience'),('Current job title','Education & experience')]])

def profile_router(runner):
    router=APIRouter()
    @router.get('/api/application-profile')
    def get_profile():
        facts=VerifiedFactsStore()
        with store.LOCK:answers=store.read(store.STORE);questions=store.read(store.QUESTIONS)
        pending=[]
        for q in questions:
            a=store.find_answer(q['label'],q['url'],q['kind'])
            if not store.usable(a,q):pending.append(q)
        active=runner.active
        return {'common_fields':[{'label':label,'group':group,'aliases':aliases,'suggested_value':getattr(facts,key,'') if key else ''} for label,group,aliases,key in COMMON],
                'answers':answers,'pending_questions':sorted(pending,key=lambda q:(not q['required'],q['first_seen_at'])),
                'session':{'application_id':active['id'],'waiting':active['waiting'],'submission_attempted':active['outcome'].get('submission_attempted',False),'message':active['outcome'].get('error'),'missing_fields':active['outcome'].get('missing_fields',[])} if active else None,
                'note':'Application answers are reused as you authorize. Resume facts and final submission approval remain separate.'}
    @router.post('/api/application-profile/answers')
    def save(body:AnswerInput):
        kind=body.kind;label=body.label;url=body.url
        if body.question_id:
            with store.LOCK:q=next((q for q in store.read(store.QUESTIONS) if q['id']==body.question_id),None)
            if not q:raise HTTPException(404,'Question not found.')
            label=q['label'];url=q['url'];kind=q['kind']
            if body.skip and q['required']:raise HTTPException(422,'Required fields cannot be left blank.')
            if kind in ['file','password','custom']:raise HTTPException(422,'Complete this control directly in the application browser.')
            if q.get('options') and not body.skip and str(body.value) not in [str(o['value']) for o in q['options']]:raise HTTPException(422,'Choose an option shown on the form.')
            if kind=='checkbox' and not isinstance(body.value,bool):raise HTTPException(422,'Choose Yes or No for this checkbox.')
        if any(len(a)>500 for a in body.aliases) or len(str(body.value))>10000:raise HTTPException(422,'Answer or alias is too long.')
        try:return store.save_answer(label,body.value,body.scope,url,body.aliases,body.skip,kind)
        except ValueError as exc:raise HTTPException(422,str(exc))
    @router.delete('/api/application-profile/answers/{identity}')
    def delete(identity:str):
        if not store.delete_answer(identity):raise HTTPException(404,'Answer not found.')
        return {'status':'Deleted'}
    return router
