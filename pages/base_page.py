from __future__ import annotations

from playwright.sync_api import Page


class BasePage:
    def __init__(self, page: Page, config=None):
        self.page = page
        self.config = config

    @property
    def selectors(self):
        if self.config is None:
            raise ValueError("A configuration object must be provided.")
        return self.config.selectors
