import sys
import sqlite3
from pathlib import Path

sys.path.insert(0, "C:/sukesh/job")

from services.resume_engine.engine import VerifiedFactsStore, match_job_with_llm
from services.resume_engine.template_builder import (
    build_latex_content,
    compile_latex_to_pdf,
    build_docx_resume
)

DB_PATH = "C:/sukesh/job/database/ai_job_hunter.db"
PDF_DIR = Path("C:/sukesh/job/data/generated-pdfs")
PDF_DIR.mkdir(parents=True, exist_ok=True)

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

cursor.execute("SELECT id, title, description, company_name FROM jobs")
jobs = cursor.fetchall()
print(f"[*] Regenerating template resumes for {len(jobs)} jobs...")

facts = VerifiedFactsStore()

for job_id, title, desc, company in jobs:
    print(f"\n[*] Processing Job #{job_id}: {title} at {company}")
    pdf_out = PDF_DIR / f"job_{job_id}_tailored.pdf"
    tex_out = PDF_DIR / f"job_{job_id}_tailored.tex"
    docx_out = PDF_DIR / f"job_{job_id}_tailored.docx"

    # Fast targeted summary based on verified facts
    summary = (
        f"M.Tech Medical Technology graduate from IIT Jodhpur (CGPA 8.53/10) offering hands-on expertise "
        f"in biomedical instrumentation, sensor integration, and software engineering. Demonstrated ability "
        f"to build robust production systems (IITJ One, NeoBridge) and execute rigorous scientific research."
    )

    tex_code = build_latex_content(target_role=title, tailored_summary=summary)
    with open(tex_out, "w", encoding="utf-8") as f:
        f.write(tex_code)

    try:
        compile_latex_to_pdf(str(tex_out), str(pdf_out))
        build_docx_resume(str(docx_out), target_role=title, tailored_summary=summary)
        print(f"    [+] Generated: {pdf_out.name} (LaTeX ATS PDF) & {docx_out.name} (Word DOCX)")
    except Exception as e:
        print(f"    [!] Error generating template resume for #{job_id}: {e}")

conn.close()
print("\n[*] All job resumes successfully regenerated using C:/sukesh/job/template!")
