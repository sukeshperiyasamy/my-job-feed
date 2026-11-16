import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, "C:/sukesh/job")

from services.browser_manager.browser import DedicatedBrowserManager

def test_browser_launch():
    print("[*] Running Playwright dedicated browser verification test...")
    manager = DedicatedBrowserManager(profile_name="test_verification", headless=True)
    try:
        page = manager.start()
        assert page is not None, "Page should not be None"
        success = manager.navigate("https://example.com")
        assert success, "Should successfully navigate to example.com"
        screenshot = manager.capture_screenshot("test_verification")
        assert Path(screenshot).exists(), "Screenshot should exist on disk"
        print(f"[+] Playwright test passed successfully! Screenshot: {screenshot}")
    finally:
        manager.close()

if __name__ == "__main__":
    test_browser_launch()
