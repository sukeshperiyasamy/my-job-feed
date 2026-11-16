import os
import re
import subprocess
import shutil
from pathlib import Path
from typing import Dict, Any, List, Optional
import docx
from docx.shared import Pt, RGBColor, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH

TEMPLATE_DIR = Path("C:/sukesh/job/template")
DOCX_TEMPLATE_PATH = TEMPLATE_DIR / "Resume_Template.docx"
TEX_TEMPLATE_PATH = TEMPLATE_DIR / "Resume_Template.tex"

DO_NOT_CLAIM_SKILLS = {
    "fastapi", "django", "flask", "llamaindex", "pinecone", "kubernetes", "iso standards"
}

def generate_resume_filename(candidate_name: str, job_title: str, company_name: Optional[str] = None, ext: str = "pdf") -> str:
    """
    Standardized Professional ATS Resume Naming Convention:
    Format: First_Last_RoleTitle_CompanyName_Resume.ext
    Example: Sukesh_Periyasamy_AI_ML_Engineer_MarLabs_Resume.pdf
    """
    clean_name = re.sub(r'[^a-zA-Z0-9]+', '_', candidate_name).strip('_')

    # If title has pipes/dashes or complex prefixes like 'Manager | React Native | ...', pick the core role
    raw_title = job_title
    if '|' in raw_title:
        parts = [p.strip() for p in raw_title.split('|')]
        # Pick the most descriptive part (e.g. 'React Native') or the first part
        raw_title = parts[1] if len(parts) > 1 and len(parts[1]) > 3 else parts[0]
    elif '-' in raw_title:
        raw_title = raw_title.split('-')[0].strip()

    clean_title = re.sub(r'[^a-zA-Z0-9]+', '_', raw_title).strip('_')
    clean_title = clean_title[:35].rstrip('_')

    if company_name:
        clean_company = re.sub(r'[^a-zA-Z0-9]+', '_', company_name).strip('_')[:20].rstrip('_')
        return f"{clean_name}_{clean_title}_{clean_company}_Resume.{ext}"
    return f"{clean_name}_{clean_title}_Resume.{ext}"

def clean_latex(text: str) -> str:
    """Escape special LaTeX characters."""
    if not text:
        return ""
    text = text.replace("&", r"\&")
    text = text.replace("%", r"\%")
    text = text.replace("$", r"\$")
    text = text.replace("#", r"\#")
    text = text.replace("_", r"\_")
    return text

def build_latex_content(
    target_role: str = "Medical Device / Embedded / Software Engineer",
    tailored_summary: Optional[str] = None,
    emphasized_skills: Optional[List[str]] = None
) -> str:
    """
    Builds the LaTeX resume strictly matching C:/sukesh/job/template/Resume_Template.tex
    using Sukesh Periyasamy's verified facts.
    """
    if not tailored_summary:
        tailored_summary = (
            "M.Tech in Medical Technology from IIT Jodhpur (CGPA 8.53/10) with hands-on expertise in biosensors, "
            "Raman spectroscopy, and embedded systems (ESP32). Proven record building and publishing production applications "
            "including the live IITJ One mobile platform and NeoBridge neonatal IoT monitor."
        )

    skills_cat1 = "React Native (Expo), TypeScript, Node.js, Next.js, Python, MongoDB, Redis, Docker, Git"
    skills_cat2 = "ESP32, Arduino, Raspberry Pi, Circuit Design, Sensor Integration, EMG Acquisition, Signal Processing"
    skills_cat3 = "SERS Chips, Raman Spectroscopy, Nanofabrication (Ag/Au coating), Cleanroom protocols, Calibration"

    tex_content = rf"""% One-page resume template for Sukesh Periyasamy
\documentclass[9.2pt,a4paper]{{article}}
\usepackage[margin=0.48in,top=0.32in,bottom=0.32in]{{geometry}}
\usepackage[T1]{{fontenc}}
\usepackage{{helvet}}\renewcommand{{\familydefault}}{{\sfdefault}}
\usepackage{{enumitem}}
\usepackage{{titlesec}}
\usepackage[hidelinks]{{hyperref}}
\usepackage{{xcolor}}
\definecolor{{accent}}{{HTML}}{{1F3A5F}}
\pagestyle{{empty}}
\setlength{{\parindent}}{{0pt}}
\titleformat{{\section}}{{\bfseries\large\color{{accent}}}}{{}}{{0em}}{{\MakeUppercase}}[\vspace{{-0.65em}}\color{{accent}}\rule{{\linewidth}}{{0.5pt}}]
\titlespacing*{{\section}}{{0pt}}{{3.5pt}}{{1.5pt}}
\setlist[itemize]{{leftmargin=1.1em,itemsep=0pt,topsep=0.5pt,parsep=0pt}}
\newcommand{{\role}}[3]{{\textbf{{#1}}\hfill\textit{{#2}}\\[-2pt]\textit{{\small #3}}\par}}

\begin{{document}}

\begin{{center}}
{{\huge\bfseries SUKESH PERIYASAMY}}\\[1.5pt]
{{\large\bfseries\color{{accent}} {clean_latex(target_role)}}}\\[1.5pt]
\small sukeshperiyasamy@gmail.com \,|\, +91 9943969595 \,|\, \href{{https://linkedin.com/in/sukeshperiyasamy}}{{linkedin.com/in/sukeshperiyasamy}} \,|\, \href{{https://github.com/sukeshperiyasamy}}{{github.com/sukeshperiyasamy}}\\
Karur, Tamil Nadu \,|\, Available immediately \,|\, Open to relocation
\end{{center}}

\section{{Profile Summary}}
{clean_latex(tailored_summary)}

\section{{Skills}}
\textbf{{Software \& Mobile:}} {clean_latex(skills_cat1)}\\
\textbf{{Embedded \& Hardware:}} {clean_latex(skills_cat2)}\\
\textbf{{Sensors \& Instrumentation:}} {clean_latex(skills_cat3)}

\section{{Projects}}
\role{{IITJ One --- Campus Mobile Platform}}{{\href{{https://iitjone.in}}{{iitjone.in}} \,|\, \href{{https://github.com/Godevs04/IITJ_One}}{{GitHub}}}}{{Stack: React Native (Expo), TypeScript, Express, Next.js, Redis, MongoDB, Docker}}
\begin{{itemize}}
  \item Architected and published official campus mobile app live on Google Play and Apple App Store serving 2,000+ active students and faculty.
  \item Engineered high-performance backend with Redis caching and Socket.IO real-time notifications, containerized using Docker.
\end{{itemize}}

\role{{NeoBridge --- Neonatal Kangaroo-Care Monitor}}{{\href{{https://neobridge.vercel.app}}{{Live App}} \,|\, \href{{https://github.com/sukeshperiyasamy/NeoBridge}}{{GitHub}}}}{{Stack: ESP32 Firmware, BLE, React Native, Hono, Neon Postgres}}
\begin{{itemize}}
  \item Developed custom ESP32 wearable band firmware and Bluetooth Low Energy telemetry for continuous newborn temperature monitoring.
  \item Built cross-platform mobile companion app providing temperature trend tracking, maternal alerts, and demo-mode clinical AI insights.
\end{{itemize}}

\role{{Doc-RAG --- Local GraphRAG Scientific QA}}{{\href{{https://github.com/sukeshperiyasamy}}{{GitHub}}}}{{Stack: Python, Ollama (qwen2.5:3b), LightRAG, NetworkX, FastEmbed}}
\begin{{itemize}}
  \item Constructed knowledge graph extracting 15,199 entities and 7,252 relationships across 1,438 scientific document chunks.
  \item Benchmarked question-answering accuracy achieving 100\% Recall@5 and 90\% Recall@3 without external cloud API dependencies.
\end{{itemize}}

\section{{Experience}}
\role{{Junior Research Fellow (SERS Biosensor for Sepsis)}}{{May 2026 -- Nov 2026}}{{IIT Jodhpur \& AIIMS Jodhpur (TCS Project), Jodhpur}}
\begin{{itemize}}
  \item Fabricated SERS silicon chips via metal-assisted chemical etching with Ag/Au nanocoatings in cleanroom facilities for bacterial marker detection (LPS, peptidoglycans).
  \item Executed Python-based Raman spectroscopic analysis across 120--150 spectra per run, establishing calibration curves and standard operating protocols.
\end{{itemize}}

\role{{Technical Workshop Instructor}}{{2026}}{{KEC College, Tamil Nadu}}
\begin{{itemize}}
  \item Delivered 4-day intensive technical training on IoT, embedded systems (ESP32/Arduino), Linux, and hardware debugging for 35+ students.
\end{{itemize}}

\role{{Software Testing Intern}}{{Oct 2022 -- Nov 2022}}{{Atos Syntel, Remote}}
\begin{{itemize}}
  \item Executed functional, regression, and integration testing within an Agile SDLC; authored defect reports and test suites.
\end{{itemize}}

\section{{Education}}
\role{{M.Tech, Medical Technology (CGPA 8.53 / 10, First Class)}}{{2024 -- 2026}}{{IIT Jodhpur (Joint Program with AIIMS Jodhpur)}}
\role{{Master of Computer Applications --- MCA (CGPA 7.20 / 10, First Class)}}{{2022 -- 2024}}{{Erode Sengunthar Engineering College}}
\role{{B.Sc., Information Technology (CGPA 6.90 / 10, First Class)}}{{2019 -- 2022}}{{Kongu Arts and Science College}}

\section{{Achievements and Certifications}}
TCS-Funded JRF Fellowship Award (IIT Jodhpur) \,|\, Published IITJ One on Google Play \& iOS App Store \,|\, KEC IoT Workshop Lead

\end{{document}}
"""
    return tex_content

def build_docx_resume(
    output_docx_path: str,
    target_role: str = "Medical Device / Embedded / Software Engineer",
    tailored_summary: Optional[str] = None
):
    """
    Populates C:/sukesh/job/template/Resume_Template.docx with Sukesh's verified facts.
    """
    if not DOCX_TEMPLATE_PATH.exists():
        raise FileNotFoundError(f"Template not found at {DOCX_TEMPLATE_PATH}")

    doc = docx.Document(str(DOCX_TEMPLATE_PATH))

    if not tailored_summary:
        tailored_summary = (
            "M.Tech in Medical Technology from IIT Jodhpur (CGPA 8.53/10) with hands-on expertise in biosensors, "
            "Raman spectroscopy, and embedded systems (ESP32). Proven record building and publishing production applications "
            "including the live IITJ One mobile platform and NeoBridge neonatal IoT monitor."
        )

    # Replace placeholders in paragraphs
    replacements = {
        "YOUR NAME": "SUKESH PERIYASAMY",
        "Target Role Title": target_role,
        "email@example.com | +91 00000 00000 | linkedin.com/in/yourname | github.com/yourname": 
            "sukeshperiyasamy@gmail.com | +91 9943969595 | linkedin.com/in/sukeshperiyasamy | github.com/sukeshperiyasamy",
        "City, State | Available immediately | Open to relocation": 
            "Karur, Tamil Nadu | Available immediately | Open to relocation",
        "Two to three lines: your degree, your strongest proof (one shipped project or result), and the role you want. Match the wording to the job description.":
            tailored_summary,
        "Category one: skill, skill, skill, skill":
            "Software & Mobile: React Native (Expo), TypeScript, Node.js, Next.js, Python, MongoDB, Redis, Docker, Git",
        "Category two: skill, skill, skill, skill":
            "Embedded & Hardware: ESP32, Arduino, Raspberry Pi, Circuit Design, Sensor Integration, EMG Acquisition, Signal Processing",
        "Category three: skill, skill, skill, skill":
            "Sensors & Instrumentation: SERS Chips, Raman Spectroscopy, Nanofabrication (Ag/Au coating), Cleanroom Protocols, Calibration"
    }

    for p in doc.paragraphs:
        for k, v in replacements.items():
            if k in p.text:
                p.text = p.text.replace(k, v)

    Path(output_docx_path).parent.mkdir(parents=True, exist_ok=True)
    doc.save(str(output_docx_path))
    return str(output_docx_path)

def compile_latex_to_pdf(tex_path: str, output_pdf_path: str) -> str:
    """
    Compiles a .tex resume using pdflatex inside WSL2 to produce an ATS-grade PDF.
    """
    tex_file = Path(tex_path).resolve()
    pdf_dest = Path(output_pdf_path).resolve()
    pdf_dest.parent.mkdir(parents=True, exist_ok=True)

    tex_dir = tex_file.parent
    stem = tex_file.stem

    drive_letter = tex_dir.drive[0].lower()
    norm_path = str(tex_dir)[2:].replace('\\', '/')
    wsl_dir = f"/mnt/{drive_letter}{norm_path}"
    cmd = f'cd "{wsl_dir}" && pdflatex -interaction=nonstopmode "{tex_file.name}" && pdflatex -interaction=nonstopmode "{tex_file.name}"'

    res = subprocess.run(
        ["wsl", "-d", "Ubuntu-24.04", "bash", "-c", cmd],
        capture_output=True,
        text=True,
        timeout=30
    )

    generated_pdf = tex_dir / f"{stem}.pdf"
    if generated_pdf.exists():
        if generated_pdf != pdf_dest:
            shutil.copy2(str(generated_pdf), str(pdf_dest))
        # Clean auxiliary LaTeX build artifacts
        for ext in [".aux", ".log", ".out"]:
            aux = tex_dir / f"{stem}{ext}"
            if aux.exists():
                try:
                    aux.unlink()
                except Exception:
                    pass
        return str(pdf_dest)
    else:
        raise RuntimeError(f"LaTeX compilation failed:\n{res.stdout}\n{res.stderr}")

