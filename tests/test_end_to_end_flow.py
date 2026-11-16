"""Isolated API and browser acceptance checks; never writes sample jobs to the live DB."""
import subprocess
import sys
from pathlib import Path

def run_e2e_verification():
    root=Path(__file__).resolve().parents[1]
    for script in ['test_form_worker.py','test_operations_api.py','test_dashboard_ui.py']:
        subprocess.run([sys.executable,str(root/'tests'/script)],cwd=root,check=True)
    print('Application worker, isolated API, and dashboard workflow checks passed.')

if __name__ == '__main__':
    run_e2e_verification()
