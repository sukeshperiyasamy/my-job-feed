import os
import time
from pathlib import Path
from typing import Optional, Dict, Any
from playwright.sync_api import sync_playwright, BrowserContext, Page

PROFILES_BASE_DIR = Path("C:/sukesh/job/browser-profiles")
SCREENSHOTS_DIR = Path("C:/sukesh/job/screenshots")

PROFILES_BASE_DIR.mkdir(parents=True, exist_ok=True)
SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)

class DedicatedBrowserManager:
    """
    Manages dedicated Playwright Chromium browser instances with isolated profiles.
    Uses system Chromium binary (Edge/Chrome) in Program Files to comply with Windows AppLocker,
    pointing to a completely dedicated, isolated user_data_dir in browser-profiles/.
    Never touches personal Chrome profiles.
    """
    def __init__(self, profile_name: str = "default_portal", headless: bool = False, shared_project: bool = False):
        self.profile_name = profile_name
        self.profile_dir = PROFILES_BASE_DIR / profile_name
        self.profile_dir.mkdir(parents=True, exist_ok=True)
        self.headless = headless
        self.shared_project = shared_project
        self._owned_pages = []
        self._playwright = None
        self._context: Optional[BrowserContext] = None
        self._page: Optional[Page] = None

    def start(self) -> Page:
        if self._page and not self._page.is_closed():
            return self._page

        print(f"[*] Launching dedicated Chromium profile: '{self.profile_name}' (headless={self.headless})")
        self._playwright = sync_playwright().start()

        if self.shared_project:
            from services.browser_manager.project_browser import project_browser
            endpoint = project_browser.ensure_running()
            self._remote_browser = self._playwright.chromium.connect_over_cdp(endpoint)
            self._context = self._remote_browser.contexts[0]
            self._page = self._context.new_page()
            self._track_page(self._page)
            self._page.bring_to_front()
            return self._page
        
        # Determine executable path from Program Files to satisfy Windows Application Control
        edge_path = "C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe"
        chrome_path = "C:/Program Files/Google/Chrome/Application/chrome.exe"
        exec_path = edge_path if os.path.exists(edge_path) else (chrome_path if os.path.exists(chrome_path) else None)

        launch_kwargs = {
            "user_data_dir": str(self.profile_dir),
            "headless": self.headless,
            "viewport": {"width": 1280, "height": 800},
            "args": [
                "--no-first-run",
                "--no-default-browser-check"
            ]
        }
        if exec_path:
            launch_kwargs["executable_path"] = exec_path

        self._context = self._playwright.chromium.launch_persistent_context(**launch_kwargs)
        if len(self._context.pages) > 0:
            self._page = self._context.pages[0]
        else:
            self._page = self._context.new_page()

        return self._page

    def _track_page(self, page):
        if page not in self._owned_pages:
            self._owned_pages.append(page)
            page.on('popup', self._track_page)

    def application_pages(self):
        pages = self._owned_pages if self.shared_project else (self._context.pages if self._context else [])
        return [page for page in pages if not page.is_closed()]

    def navigate(self, url: str, wait_until: str = "domcontentloaded") -> bool:
        if not self._page:
            self.start()
        try:
            print(f"[*] Navigating to: {url}")
            self._page.goto(url, wait_until=wait_until, timeout=30000)
            return True
        except Exception as e:
            print(f"[!] Navigation error: {e}")
            return False

    def capture_screenshot(self, name_prefix: str = "screen") -> str:
        if not self._page:
            return ""
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        filename = f"{name_prefix}_{timestamp}.png"
        filepath = SCREENSHOTS_DIR / filename
        self._page.screenshot(path=str(filepath), full_page=True)
        print(f"[+] Screenshot saved: {filepath}")
        return str(filepath)

    def fill_field(self, selector: str, value: str) -> bool:
        if not self._page:
            return False
        try:
            self._page.wait_for_selector(selector, timeout=5000)
            self._page.fill(selector, value)
            return True
        except Exception as e:
            print(f"[!] Failed to fill selector '{selector}': {e}")
            return False

    def upload_document(self, selector: str, file_path: str) -> bool:
        if not self._page or not os.path.exists(file_path):
            return False
        try:
            self._page.set_input_files(selector, file_path)
            print(f"[+] Uploaded document '{file_path}' to '{selector}'")
            return True
        except Exception as e:
            print(f"[!] Upload error on selector '{selector}': {e}")
            return False

    def close(self):
        try:
            if self.shared_project:
                # Disconnect from the shared browser; never close its context or user tabs.
                for page in self._owned_pages:
                    try:
                        if not page.is_closed():page.close()
                    except Exception:
                        pass
            elif self._context:
                self._context.close()
            if self._playwright:
                self._playwright.stop()
        except Exception as e:
            print(f"[!] Error during browser shutdown: {e}")
        finally:
            self._page = None
            self._context = None
            self._playwright = None
            self._owned_pages = []
            print(f"[*] Browser profile '{self.profile_name}' safely closed.")
