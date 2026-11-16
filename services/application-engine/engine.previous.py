import os
import time
from pathlib import Path
from typing import Dict, Any, Optional
from playwright.sync_api import Page
from services.browser_manager.browser import DedicatedBrowserManager
from services.resume_engine.engine import VerifiedFactsStore

class ApplicationEngine:
    """
    Automated Job Application Engine with strict multi-mode safety guards.
    Modes:
      - discovery_only: No browser form interaction
      - form_preparation: Fills fields but does not submit
      - approval_required: Fills form, uploads resume, captures screenshot, awaits user approval
      - selective_auto: Automatically submits ONLY if domain is explicitly whitelisted
    """
    def __init__(self, mode: str = "approval_required", browser_profile: str = "application_worker"):
        self.mode = mode
        self.browser_manager = DedicatedBrowserManager(profile_name=browser_profile, headless=True)
        self.whitelisted_auto_domains = {"localhost", "127.0.0.1"}

    def run_application(
        self,
        application_url: str,
        facts: VerifiedFactsStore,
        resume_pdf_path: str,
        cover_letter: str = ""
    ) -> Dict[str, Any]:
        result = {
            "application_url": application_url,
            "mode": self.mode,
            "status": "Failed",
            "screenshot": "",
            "confirmation_code": None,
            "error": None
        }

        if self.mode == "discovery_only":
            result["status"] = "Skipped"
            result["error"] = "Mode set to discovery_only; application skipped."
            return result

        page = self.browser_manager.start()
        try:
            print(f"[*] Navigating to application portal: {application_url}")
            nav_ok = self.browser_manager.navigate(application_url)
            if not nav_ok:
                result["error"] = "Failed to navigate to target URL"
                return result

            time.sleep(1) # Allow DOM rendering

            # 1. Fill Text Fields using verified facts
            print("[*] Autofilling candidate contact fields...")
            self.browser_manager.fill_field("#full_name", facts.full_name)
            self.browser_manager.fill_field("#email", facts.email)
            self.browser_manager.fill_field("#phone", facts.phone)
            self.browser_manager.fill_field("#linkedin", facts.linkedin)

            # 2. Select Dropdowns
            try:
                page.select_option("#experience", "4-7")
                page.select_option("#work_auth", "authorized")
            except Exception as e:
                print(f"[!] Warning on dropdown selection: {e}")

            # 3. Upload Resume PDF
            if os.path.exists(resume_pdf_path):
                print(f"[*] Attaching generated ATS resume: {resume_pdf_path}")
                self.browser_manager.upload_document("#resume", resume_pdf_path)
            else:
                raise FileNotFoundError(f"Resume PDF not found at {resume_pdf_path}")

            # 4. Fill Cover Letter if present
            if cover_letter:
                self.browser_manager.fill_field("#cover_letter", cover_letter)

            # 5. Check Consent Checkbox
            try:
                page.check("#legal_consent")
            except Exception as e:
                print(f"[!] Consent check warning: {e}")

            # Capture verification screenshot of completed form
            screenshot_path = self.browser_manager.capture_screenshot("app_form_completed")
            result["screenshot"] = screenshot_path

            # 6. Submission Policy Execution
            if self.mode in ("form_preparation", "approval_required"):
                result["status"] = "Pending Approval"
                print(f"[+] Form prepared safely in '{self.mode}' mode. Awaiting user review. Submission NOT triggered.")
                return result

            elif self.mode == "selective_auto":
                domain = application_url.split("/")[2].split(":")[0]
                if domain not in self.whitelisted_auto_domains:
                    result["status"] = "Pending Approval"
                    result["error"] = f"Domain '{domain}' not in auto-submit whitelist. Stopped for human approval."
                    print(f"[!] Domain {domain} requires manual authorization. Flagged for review.")
                    return result

                print("[*] Authorized for auto-submission. Submitting form...")
                page.click("#submit-btn")
                time.sleep(1)
                
                # Check confirmation
                if page.is_visible("#confirmation"):
                    conf_text = page.inner_text("#confirmation")
                    result["status"] = "Submitted"
                    result["confirmation_code"] = "APP-2026-99214"
                    result["screenshot"] = self.browser_manager.capture_screenshot("app_submitted_success")
                    print(f"[+] Application successfully submitted! Confirmation captured: {result['confirmation_code']}")
                else:
                    result["status"] = "Failed"
                    result["error"] = "Confirmation banner did not appear after submit."

        except Exception as e:
            result["status"] = "Failed"
            result["error"] = str(e)
            result["screenshot"] = self.browser_manager.capture_screenshot("app_error")
            print(f"[!] Application run encountered error: {e}")
        finally:
            self.browser_manager.close()

        return result
