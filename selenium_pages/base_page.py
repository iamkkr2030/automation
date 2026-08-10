"""Shared visual-evidence support for Selenium Page Objects."""

import re
import time


class SeleniumBasePage:
    def __init__(self, driver):
        self.driver = driver

    def capture_step(self, label: str) -> None:
        """Save a numbered screenshot after a user-visible browser action."""
        if not hasattr(self.driver, "evidence_dir"):
            return
        self.driver.evidence_step += 1
        safe_label = re.sub(r"[^a-z0-9_-]+", "_", label.lower()).strip("_")
        filename = f"{self.driver.evidence_step:02d}_{safe_label}.png"
        self.driver.save_screenshot(str(self.driver.evidence_dir / filename))
        time.sleep(self.driver.step_delay)
