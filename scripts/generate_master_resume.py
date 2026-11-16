import sys
from pathlib import Path

sys.path.insert(0, "C:/sukesh/job")

from services.resume_engine.engine import VerifiedFactsStore, generate_ats_pdf

def build_master_resume():
    print("[*] Generating Sukesh Periyasamy's Master ATS PDF Resume...")
    facts = VerifiedFactsStore() # Loads directly from config/profile.json
    
    tailored_data = {
        "tailored_summary": facts.summary,
        "emphasized_skills": [
            "React Native (Expo)",
            "Next.js",
            "TypeScript",
            "Python",
            "RAG & GraphRAG",
            "Node.js",
            "MongoDB",
            "PostgreSQL",
            "Docker"
        ]
    }

    out_path = "C:/sukesh/job/data/resumes/Sukesh_Periyasamy_Resume.pdf"
    res = generate_ats_pdf(facts, tailored_data, out_path)
    print(f"[+] Master Resume successfully created: {res}")

if __name__ == "__main__":
    build_master_resume()
