from __future__ import annotations

from playwright.sync_api import Page

from config.site_config import DEFAULT_CONFIG
from pages.base_page import BasePage


class CheckoutPage(BasePage):
    def __init__(self, page: Page, config=None):
        super().__init__(page, config or DEFAULT_CONFIG)
        selectors = self.selectors["checkout"]
        self.error_message = page.locator(selectors["error"])

    def fill_information(self, first_name: str, last_name: str, postal_code: str) -> None:
        self.page.locator(self.selectors["checkout"]["first_name_input"]).fill(first_name)
        self.page.locator(self.selectors["checkout"]["last_name_input"]).fill(last_name)
        self.page.locator(self.selectors["checkout"]["postal_code_input"]).fill(postal_code)

    def continue_checkout(self) -> None:
        self.page.get_by_role("button", name=self.selectors["checkout"]["continue_button"]).click()

    def finish(self) -> None:
        self.page.get_by_role("button", name=self.selectors["checkout"]["finish_button"]).click()

    def total(self) -> float:
        return float(self.page.locator(self.selectors["checkout"]["total_label"]).inner_text().replace("Total: $", ""))
