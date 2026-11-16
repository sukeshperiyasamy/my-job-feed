import subprocess
import json
import re

def call_antigravity_cli(prompt: str) -> dict:
    agy_exe = r"C:\Users\LOKIKENDE\AppData\Local\agy\bin\agy.exe"
    result = subprocess.run(
        [agy_exe, "-p", prompt, "--disable-slash-commands"],
        capture_output=True,
        text=True,
        timeout=30
    )
    raw_output = result.stdout.strip()
    # Extract JSON block if wrapped in markdown
    match = re.search(r"\{.*\}", raw_output, re.DOTALL)
    if match:
        return json.loads(match.group(0))
    raise ValueError(f"No JSON found in response: {raw_output}")

if __name__ == "__main__":
    prompt = """You are an ATS resume scoring engine. Compare this candidate with the job description.
Candidate skills: Python, Docker, Playwright, FastAPI.
Job title: Senior Automation Engineer.
Job description: Looking for Senior Automation Engineer with Python and Playwright experience.
Output raw JSON only with keys:
- "match_score": integer (1-100)
- "match_reason": string
- "emphasized_skills": list of candidate skills relevant to this job
- "tailored_summary": 2-sentence summary
"""
    print("[*] Calling Antigravity CLI...")
    data = call_antigravity_cli(prompt)
    print("[+] Successfully received response from Antigravity CLI:")
    print(json.dumps(data, indent=2))
