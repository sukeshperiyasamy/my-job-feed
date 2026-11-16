import os
import json
import re
import subprocess
import requests
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
import pypdf

LM_STUDIO_URL = os.getenv("LM_STUDIO_URL", "http://127.0.0.1:1234/v1")
AGY_EXE = os.getenv("AGY_EXE", r"C:\Users\LOKIKENDE\AppData\Local\agy\bin\agy.exe")
CODEX_EXE = os.getenv("CODEX_EXE", r"C:\Users\LOKIKENDE\AppData\Local\Programs\OpenAI\Codex\bin\codex.exe")
PROFILE_JSON_PATH = "C:/sukesh/job/config/profile.json"

DO_NOT_CLAIM_SKILLS = {
    "fastapi", "django", "flask", "llamaindex", "pinecone", "kubernetes", "iso standards"
}

class VerifiedFactsStore:
    """
    Strict verified facts store for Sukesh Periyasamy.
    Never invents degrees, dates, companies, or unverified skills.
    Explicitly filters out forbidden claims (FastAPI, Django, Flask, LlamaIndex, Pinecone, Kubernetes, ISO).
    """
    def __init__(self, raw_facts: Optional[Dict[str, Any]] = None):
        if raw_facts is None and os.path.exists(PROFILE_JSON_PATH):
            with open(PROFILE_JSON_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
                personal = data.get("personal", {})
                self.full_name = personal.get("full_name", "Sukesh Periyasamy")
                self.email = personal.get("email", "sukeshperiyasamy@gmail.com")
                self.phone = personal.get("mobile", "+91 9943969595")
                self.location = f"{personal.get('city', 'Karur')}, Tamil Nadu, India"
                self.linkedin = personal.get("linkedin", "https://linkedin.com/in/sukeshperiyasamy")
                self.github = personal.get("github", "https://github.com/sukeshperiyasamy")
                self.summary = data.get("summary", "")
                
                # Combine verified skills and strictly exclude do-not-claim
                raw_skills = data.get("skills", {})
                combined = []
                for cat in ["software", "ai_ml", "hardware_embedded", "research_lab"]:
                    combined.extend(raw_skills.get(cat, []))
                
                self.skills = [s for s in combined if s.lower() not in DO_NOT_CLAIM_SKILLS]
                self.experience = data.get("experience", [])
                self.education = data.get("education", [])
                self.projects = data.get("projects", [])
                self.certificates = data.get("certificates", [])
        else:
            raw = raw_facts or {}
            self.full_name = raw.get("full_name", "Sukesh Periyasamy")
            self.email = raw.get("email", "sukeshperiyasamy@gmail.com")
            self.phone = raw.get("phone", "+91 9943969595")
            self.location = raw.get("location", "Karur, Tamil Nadu, India")
            self.linkedin = raw.get("linkedin", "https://linkedin.com/in/sukeshperiyasamy")
            self.github = raw.get("github", "https://github.com/sukeshperiyasamy")
            self.summary = raw.get("summary", "")
            self.skills = [s for s in raw.get("skills", []) if s.lower() not in DO_NOT_CLAIM_SKILLS]
            self.experience = raw.get("experience", [])
            self.education = raw.get("education", [])
            self.projects = raw.get("projects", [])
            self.certificates = raw.get("certificates", [])

    def to_dict(self) -> Dict[str, Any]:
        return {
            "full_name": self.full_name,
            "email": self.email,
            "phone": self.phone,
            "location": self.location,
            "linkedin": self.linkedin,
            "github": self.github,
            "summary": self.summary,
            "skills": self.skills,
            "experience": self.experience,
            "education": self.education,
            "projects": self.projects,
            "certificates": self.certificates
        }

def match_job_with_llm(job_title: str, job_description: str, facts: VerifiedFactsStore) -> Dict[str, Any]:
    """
    AI-powered job matching & resume tailoring.
    Priority 1: Antigravity CLI (agy)
    Priority 2: Local LM Studio (port 1234)
    Priority 3: Deterministic ATS scoring
    Strictly forbids claiming FastAPI, Django, Flask, LlamaIndex, Pinecone, Kubernetes, ISO standards.
    """
    prompt = f"""You are an expert ATS recruiter. Analyze the job against candidate verified facts.
Do NOT invent any facts, experience, degrees, or employers.
CRITICAL CONSTRAINT: You MUST NEVER claim or add: FastAPI, Django, Flask, LlamaIndex, Pinecone, Kubernetes, or ISO standards.

JOB TITLE: {job_title}
JOB DESCRIPTION: {job_description[:1500]}

CANDIDATE PROFILE:
Name: {facts.full_name}
Degree: M.Tech Medical Technology (IIT Jodhpur / AIIMS Jodhpur), MCA, B.Sc. IT
Core Skills: {', '.join(facts.skills)}
Key Experience: Junior Research Fellow (SERS Biosensor, Raman Spectroscopy, Python) at IIT Jodhpur; IITJ One app creator (React Native, Next.js, Node.js, MongoDB, Redis, Docker); Doc-RAG (GraphRAG, Ollama, LightRAG).

Output raw JSON only with keys:
- "match_score": integer between 1 and 100
- "match_reason": 2-sentence summary
- "emphasized_skills": list of candidate's verified skills most relevant to this job (only from candidate's verified list!)
- "tailored_summary": 2-3 sentence professional summary highlighting candidate's verified skills for this position.
"""
    # 1. Primary AI Engine: Codex CLI (OpenAI GPT-4/GPT-5/gpt-6.1-sol via local CLI)
    if os.path.exists(CODEX_EXE):
        try:
            p = subprocess.Popen(
                [CODEX_EXE, "exec", prompt, "--ephemeral", "--skip-git-repo-check"],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            out, _ = p.communicate(input="", timeout=40)
            match = re.search(r"\{.*\}", out, re.DOTALL)
            if match:
                data = json.loads(match.group(0))
                data["emphasized_skills"] = [
                    s for s in data.get("emphasized_skills", [])
                    if s.lower() not in DO_NOT_CLAIM_SKILLS and s in facts.skills
                ]
                print(f"[+] Scored via OpenAI Codex CLI: Score = {data.get('match_score')}%")
                return data
        except Exception as e:
            print(f"[!] Codex CLI fallback: {e}")

    # 2. Secondary AI Engine: Antigravity CLI (agy)
    if os.path.exists(AGY_EXE):
        try:
            res = subprocess.run(
                [AGY_EXE, "-p", prompt, "--disable-slash-commands"],
                capture_output=True,
                text=True,
                timeout=30
            )
            raw = res.stdout.strip()
            match = re.search(r"\{.*\}", raw, re.DOTALL)
            if match:
                data = json.loads(match.group(0))
                data["emphasized_skills"] = [
                    s for s in data.get("emphasized_skills", [])
                    if s.lower() not in DO_NOT_CLAIM_SKILLS and s in facts.skills
                ]
                print(f"[+] Scored via Antigravity CLI (agy): Score = {data.get('match_score')}%")
                return data
        except Exception as e:
            print(f"[!] Antigravity CLI fallback: {e}")

    # 3. Tertiary: Try Local LM Studio
    try:
        resp = requests.post(
            f"{LM_STUDIO_URL}/chat/completions",
            json={
                "model": "mistral-small-3.1-draft-0.5b",
                "messages": [
                    {"role": "system", "content": "You are a precise ATS job-fit engine that only outputs JSON."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.2,
                "response_format": {"type": "json_object"}
            },
            timeout=10
        )
        if resp.status_code == 200:
            content = resp.json()["choices"][0]["message"]["content"]
            print("[+] Scored via local LM Studio")
            data = json.loads(content)
            data["emphasized_skills"] = [
                s for s in data.get("emphasized_skills", [])
                if s.lower() not in DO_NOT_CLAIM_SKILLS and s in facts.skills
            ]
            return data
    except Exception as e:
        print(f"[!] Local LM Studio fallback: {e}")

    # 3. Tertiary: High-performance deterministic fallback
    desc_lower = job_description.lower()
    matched_skills = [s for s in facts.skills if s.lower() in desc_lower and s.lower() not in DO_NOT_CLAIM_SKILLS]
    score = min(95, max(60, int((len(matched_skills) / max(1, min(len(facts.skills), 8))) * 100)))
    return {
        "match_score": score,
        "match_reason": f"Matched {len(matched_skills)} core technical competencies directly mentioned in description.",
        "emphasized_skills": matched_skills if matched_skills else facts.skills[:6],
        "tailored_summary": f"M.Tech graduate from IIT Jodhpur offering hands-on expertise in {', '.join((matched_skills or facts.skills)[:4])} to engineer reliable, scalable systems."
    }

def generate_ats_pdf(facts: VerifiedFactsStore, tailored_data: Dict[str, Any], output_path: str) -> str:
    """
    Generates a clean, single-column ATS-compliant PDF for Sukesh Periyasamy using
    the exact LaTeX template from C:/sukesh/job/template/Resume_Template.tex.
    Falls back gracefully to ReportLab if LaTeX compiler is unavailable.
    """
    out_dir = Path(output_path).parent
    out_dir.mkdir(parents=True, exist_ok=True)

    # 1. Primary: Use official LaTeX template
    try:
        from services.resume_engine.template_builder import build_latex_content, compile_latex_to_pdf
        tex_path = Path(output_path).with_suffix(".tex")
        target_role = tailored_data.get("target_role", "Medical Device / Embedded / Software Engineer")
        summary = tailored_data.get("tailored_summary", "")
        tex_code = build_latex_content(target_role=target_role, tailored_summary=summary)
        with open(tex_path, "w", encoding="utf-8") as f:
            f.write(tex_code)
        compile_latex_to_pdf(str(tex_path), output_path)
        print(f"[+] Successfully generated ATS resume via LaTeX template: {output_path}")
        return output_path
    except Exception as e:
        print(f"[!] LaTeX template generation fallback to ReportLab: {e}")

    doc = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        leftMargin=36,
        rightMargin=36,
        topMargin=36,
        bottomMargin=36
    )

    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontSize=18,
        leading=22,
        textColor=colors.HexColor("#0F172A"),
        alignment=1, # Center
        spaceAfter=3
    )
    
    contact_style = ParagraphStyle(
        'ContactLine',
        parent=styles['Normal'],
        fontSize=8.5,
        leading=11.5,
        textColor=colors.HexColor("#475569"),
        alignment=1,
        spaceAfter=10
    )
    
    h2_style = ParagraphStyle(
        'SectionH2',
        parent=styles['Heading2'],
        fontSize=11,
        leading=14,
        textColor=colors.HexColor("#1E3A8A"),
        spaceBefore=7,
        spaceAfter=3
    )
    
    body_style = ParagraphStyle(
        'Body',
        parent=styles['Normal'],
        fontSize=9,
        leading=12.5,
        textColor=colors.HexColor("#1E293B"),
        spaceAfter=3
    )
    
    bullet_style = ParagraphStyle(
        'Bullet',
        parent=body_style,
        leftIndent=12,
        firstLineIndent=-8,
        spaceAfter=2
    )

    story = []

    # 1. Header
    story.append(Paragraph(facts.full_name, title_style))
    contact_str = f"{facts.location} &bull; {facts.phone} &bull; {facts.email} &bull; <a href='{facts.linkedin}'>LinkedIn</a> &bull; <a href='{facts.github}'>GitHub</a>"
    story.append(Paragraph(contact_str, contact_style))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#CBD5E1"), spaceAfter=6))

    # 2. Professional Summary
    summary_text = tailored_data.get("tailored_summary") or facts.summary
    if summary_text:
        story.append(Paragraph("PROFESSIONAL SUMMARY", h2_style))
        story.append(Paragraph(summary_text, body_style))
        story.append(Spacer(1, 4))

    # 3. Technical Skills
    emphasized = tailored_data.get("emphasized_skills", facts.skills[:6])
    other_skills = [s for s in facts.skills if s not in emphasized]
    story.append(Paragraph("TECHNICAL SKILLS", h2_style))
    skills_text = f"<b>Core Competencies:</b> {', '.join(emphasized)}<br/><b>Technologies & Runtimes:</b> {', '.join(other_skills[:12])}"
    story.append(Paragraph(skills_text, body_style))
    story.append(Spacer(1, 4))

    # 4. Experience & Research
    if facts.experience:
        story.append(Paragraph("WORK & RESEARCH EXPERIENCE", h2_style))
        for exp in facts.experience:
            org = exp.get('organization', exp.get('company', ''))
            role = exp.get('role', '')
            period = exp.get('period', f"{exp.get('start', '')} - {exp.get('end', '')}")
            header = f"<b>{role}</b> | {org} &mdash; <i>{period}</i>"
            story.append(Paragraph(header, body_style))
            for bullet in exp.get("bullets", []):
                story.append(Paragraph(f"&bull; {bullet}", bullet_style))
            story.append(Spacer(1, 3))

    # 5. Production & Engineering Projects
    if facts.projects:
        story.append(Paragraph("FEATURED PROJECTS", h2_style))
        for proj in facts.projects[:4]: # Top 4 featured
            name = proj.get('name', '')
            stack = proj.get('tech_stack', '')
            p_hdr = f"<b>{name}</b> [<i>{stack}</i>]"
            story.append(Paragraph(p_hdr, body_style))
            for bullet in proj.get("bullets", []):
                story.append(Paragraph(f"&bull; {bullet}", bullet_style))
            story.append(Spacer(1, 3))

    # 6. Education
    if facts.education:
        story.append(Paragraph("EDUCATION", h2_style))
        for edu in facts.education[:3]: # M.Tech, MCA, B.Sc
            e_text = f"<b>{edu.get('degree', '')}</b> &mdash; {edu.get('institution', '')} (<i>{edu.get('period', edu.get('year', ''))}</i>) &bull; <b>{edu.get('score', '')}</b>"
            story.append(Paragraph(e_text, body_style))
        story.append(Spacer(1, 4))

    # 7. Certificates & Honors
    if facts.certificates:
        story.append(Paragraph("CERTIFICATES & HONORS", h2_style))
        for cert in facts.certificates[:4]:
            story.append(Paragraph(f"&bull; {cert}", bullet_style))

    doc.build(story)
    print(f"[+] ATS PDF generated: {output_path}")

    # Validate Text Extractability with pypdf
    reader = pypdf.PdfReader(output_path)
    total_pages = len(reader.pages)
    extracted_text = "".join([page.extract_text() for page in reader.pages])
    assert len(extracted_text) > 100, "Generated PDF must contain extractable text!"
    print(f"[+] PDF Validation Passed: {total_pages} page(s), {len(extracted_text)} characters extracted successfully.")

    return output_path
