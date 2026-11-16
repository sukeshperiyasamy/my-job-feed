import sys
from pathlib import Path

sys.path.insert(0, "C:/sukesh/job")

from services.resume_engine.engine import VerifiedFactsStore, match_job_with_llm, generate_ats_pdf

def test_resume_generation():
    print("[*] Testing AI Resume Engine with verified synthetic facts...")
    
    # 1. Verified Facts (Synthetic test profile - no personal info required)
    facts = VerifiedFactsStore({
        "full_name": "Alex Mercer",
        "email": "alex.mercer.dev@example.com",
        "phone": "+91 98765 43210",
        "location": "Bengaluru, India",
        "linkedin": "linkedin.com/in/alexmercer-dev",
        "github": "github.com/alexmercer-dev",
        "summary": "Full Stack Engineer with 4+ years of experience building resilient distributed microservices, automated pipelines, and cloud native applications.",
        "skills": ["Python", "FastAPI", "Docker", "PostgreSQL", "React", "TypeScript", "Playwright", "Redis", "CI/CD"],
        "experience": [
            {
                "role": "Senior Software Engineer",
                "company": "CloudScale Innovations",
                "start": "2022",
                "end": "Present",
                "bullets": [
                    "Architected high-throughput FastAPI microservices processing 2M+ daily requests with 99.9% uptime.",
                    "Implemented autonomous Playwright browser automation test suites cutting regression time by 65%.",
                    "Optimized PostgreSQL queries and Redis caching layer, reducing p95 latency from 320ms to 48ms."
                ]
            },
            {
                "role": "Software Engineer",
                "company": "Apex NextGen Solutions",
                "start": "2020",
                "end": "2022",
                "bullets": [
                    "Developed React/TypeScript dashboards with real-time WebSocket state management.",
                    "Containerized multi-tier applications using Docker and orchestrated CI/CD delivery on Kubernetes."
                ]
            }
        ],
        "education": [
            {
                "degree": "B.Tech in Computer Science & Engineering",
                "institution": "National Institute of Technology",
                "year": "2020"
            }
        ],
        "projects": [
            {
                "name": "Automated Multi-Source Scraper",
                "tech_stack": "Python, Docker, PostgreSQL",
                "highlights": [
                    "Built resilient scraper engine extracting structured job data across 5 portals concurrently."
                ]
            }
        ]
    })

    job_title = "Senior Python / Automation Engineer"
    job_desc = "Seeking a Senior Python Engineer experienced in FastAPI, Playwright browser automation, Docker containerization, and PostgreSQL."

    # 2. Score & Tailor using Local AI / deterministic matching
    tailored = match_job_with_llm(job_title, job_desc, facts)
    print(f"[+] Match Score: {tailored.get('match_score')}%")
    print(f"[+] Match Reason: {tailored.get('match_reason')}")
    print(f"[+] Emphasized Skills: {tailored.get('emphasized_skills')}")

    # 3. Generate ATS-Compliant PDF
    out_pdf = "C:/sukesh/job/data/generated-pdfs/alex_mercer_tailored.pdf"
    res = generate_ats_pdf(facts, tailored, out_pdf)
    assert Path(res).exists()
    print(f"[+] Generated ATS PDF verified successfully at: {res}")

if __name__ == "__main__":
    test_resume_generation()
