import sys
from pathlib import Path
sys.path.insert(0, "C:/sukesh/job")

from services.resume_engine.template_builder import (
    build_latex_content,
    compile_latex_to_pdf,
    build_docx_resume
)

output_dir = Path("C:/sukesh/job/data/resumes")
output_dir.mkdir(parents=True, exist_ok=True)

# 1. Generate master LaTeX resume
tex_path = output_dir / "Sukesh_Periyasamy_Resume.tex"
tex_content = build_latex_content(
    target_role="Medical Device / Embedded / Software Engineer",
    tailored_summary=(
        "M.Tech in Medical Technology from IIT Jodhpur (CGPA 8.53/10) with hands-on expertise in biosensors, "
        "Raman spectroscopy, and embedded systems (ESP32). Proven record building and publishing production applications "
        "including the live IITJ One mobile platform and NeoBridge neonatal IoT monitor."
    )
)
with open(tex_path, "w", encoding="utf-8") as f:
    f.write(tex_content)
print(f"[+] Wrote LaTeX to {tex_path}")

# 2. Compile to PDF using pdflatex
pdf_path = output_dir / "Sukesh_Periyasamy_Resume.pdf"
res_pdf = compile_latex_to_pdf(str(tex_path), str(pdf_path))
print(f"[+] Compiled LaTeX to PDF: {res_pdf}")

# 3. Generate Word docx from template
docx_path = output_dir / "Sukesh_Periyasamy_Resume.docx"
res_docx = build_docx_resume(
    output_docx_path=str(docx_path),
    target_role="Medical Device / Embedded / Software Engineer"
)
print(f"[+] Generated Word Document: {res_docx}")
