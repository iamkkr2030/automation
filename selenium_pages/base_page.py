"""Shared visual-evidence support for Selenium Page Objects."""

import logging
import re
import time

LOGGER = logging.getLogger("automation")


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
        dest = self.driver.evidence_dir / filename
        LOGGER.info("Saving screenshot step %s for %s -> %s", self.driver.evidence_step, getattr(self.driver, 'session_id', 'unknown'), str(dest))
        self.driver.save_screenshot(str(dest))
        # If a test_steps collector is attached to the driver, record this step there too
        try:
            if hasattr(self.driver, "test_steps") and self.driver.test_steps is not None:
                # expected unknown here; allow caller/tests to add expected separately
                self.driver.test_steps.add(f"screenshot: {filename}")
        except Exception:
            LOGGER.debug("Failed to add screenshot step to test_steps", exc_info=True)
        time.sleep(self.driver.step_delay)
