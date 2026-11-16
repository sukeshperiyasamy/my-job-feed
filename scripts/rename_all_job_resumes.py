import sys
import sqlite3
import shutil
from pathlib import Path

sys.path.insert(0, "C:/sukesh/job")

from services.resume_engine.template_builder import (
    generate_resume_filename,
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

print(f"[*] Standardizing resume filenames for {len(jobs)} jobs...")

for job_id, title, desc, company in jobs:
    clean_pdf_name = generate_resume_filename("Sukesh Periyasamy", title, company, "pdf")
    clean_docx_name = generate_resume_filename("Sukesh Periyasamy", title, company, "docx")
    clean_tex_name = generate_resume_filename("Sukesh Periyasamy", title, company, "tex")

    pdf_out = PDF_DIR / clean_pdf_name
    docx_out = PDF_DIR / clean_docx_name
    tex_out = PDF_DIR / clean_tex_name
    compat_pdf = PDF_DIR / f"job_{job_id}_tailored.pdf"

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
        # Keep compat copy
        shutil.copy2(str(pdf_out), str(compat_pdf))
        print(f"    [+] #{job_id:2d} -> {clean_pdf_name}")
    except Exception as e:
        print(f"    [!] Error #{job_id}: {e}")

conn.close()
print("\n[*] All resumes standardized with proper ATS naming convention!")
