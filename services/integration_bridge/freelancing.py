"""Local freelance lead tracker. No external submission or account automation."""
from typing import Literal
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.exc import IntegrityError
from services.integration_bridge.models import FreelanceLead
from services.job_collector.careers import canonical_url

SERVICES = [
    {'name':'Python & automation','scope':'Data cleanup, API integrations and repeatable file/report workflows.','proof':'Prepare a small automation demo with input/output examples.'},
    {'name':'AI / RAG','scope':'Document search prototypes, retrieval workflows and evaluation scripts.','proof':'Show a grounded Q&A demo with source citations.'},
    {'name':'Mobile development','scope':'React Native screens, API integration and bug fixes.','proof':'Show a short mobile demo and a clear feature scope.'},
    {'name':'Software QA','scope':'Test cases, regression testing and reproducible bug reports.','proof':'Share a sample test plan and bug report.'},
    {'name':'ComfyUI workflows','scope':'AI image/video/audio workflows and rendering or upload automation.','proof':'Show a reproducible workflow with sample outputs.'},
    {'name':'Sensors & prototypes','scope':'ESP32, Arduino or Raspberry Pi data capture and research prototypes.','proof':'Show a sensor-to-dashboard demo; define prototype limitations.'}
]
PLATFORMS = [
    {'name':'Upwork','url':'https://www.upwork.com/freelance-jobs/','note':'Browse project listings and review the client and scope before proposing.'},
    {'name':'Freelancer','url':'https://www.freelancer.com/jobs/python','note':'Python project discovery. Check each listing’s budget and requirements.'}
]
class LeadInput(BaseModel):
    title: str = Field(min_length=1,max_length=200)
    url: str = Field(max_length=2048)
    platform: str = Field(default='Direct client',max_length=120)
    service: str = Field(default='Python & automation',max_length=100)
    budget: str = Field(default='Undisclosed',max_length=200)
    description: str = Field(default='',max_length=20000)
    @field_validator('url')
    @classmethod
    def validate_url(cls,value): return canonical_url(value)
    @field_validator('title')
    @classmethod
    def validate_title(cls,value):
        if not value.strip(): raise ValueError('Enter a project title.')
        return value.strip()
class LeadUpdate(BaseModel):
    status: Literal['Saved','Drafting','Proposal sent','Interview','Won','Closed']
    proposal: str = Field(default='',max_length=20000)

def freelance_router(db_factory):
    router=APIRouter(prefix='/api/freelancing')
    def row(j):
        return {k:getattr(j,k) for k in ['id','title','url','platform','service','budget','description','proposal','status','created_at']}
    @router.get('')
    def info():
        with db_factory() as db:
            return {'services':SERVICES,'platforms':PLATFORMS,'source_checked_on':'2026-11-17','leads':[row(j) for j in db.query(FreelanceLead).order_by(FreelanceLead.id.desc()).all()]}
    @router.post('/leads',status_code=201)
    def add(body:LeadInput):
        with db_factory() as db:
            lead=FreelanceLead(**body.model_dump());db.add(lead)
            try: db.commit()
            except IntegrityError:
                db.rollback();raise HTTPException(409,'This project URL is already saved.')
            db.refresh(lead);return row(lead)
    @router.patch('/leads/{lead_id}')
    def update(lead_id:int,body:LeadUpdate):
        with db_factory() as db:
            lead=db.get(FreelanceLead,lead_id)
            if lead is None: raise HTTPException(404,'Project not found.')
            lead.status=body.status;lead.proposal=body.proposal;db.commit();db.refresh(lead);return row(lead)
    @router.post('/leads/{lead_id}/draft')
    def draft(lead_id:int):
        with db_factory() as db:
            lead=db.get(FreelanceLead,lead_id)
            if lead is None: raise HTTPException(404,'Project not found.')
            # Editable template only: never claim client work, certifications or results.
            return {'proposal':f'Hello,\n\nI’m interested in your project: {lead.title}. My relevant focus is {lead.service}.\n\nBefore proposing a delivery date and price, I would like to confirm your inputs, expected deliverables and acceptance criteria. I suggest starting with a small agreed milestone, followed by a review and handover.\n\n[Add a relevant portfolio link and explain your approach after reviewing the full brief.]\n\nCould you share the current setup and your highest-priority requirement?\n\nThank you,\nSukesh','note':'Editable template. Add a relevant work sample and confirm the scope before sending.'}
    return router
