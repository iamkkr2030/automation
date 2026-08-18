from __future__ import annotations

from playwright.sync_api import Page

from config.site_config import DEFAULT_CONFIG
from pages.base_page import BasePage


class LoginPage(BasePage):
    def __init__(self, page: Page, config=None):
        super().__init__(page, config or DEFAULT_CONFIG)
        selectors = self.selectors["login"]
        self.username = page.get_by_placeholder(selectors["username_placeholder"])
        self.password = page.get_by_placeholder(selectors["password_placeholder"])
        self.login_button = page.get_by_role("button", name=selectors["submit_button"])
        self.error_message = page.locator(selectors["error"])

    def login(self, username: str, password: str) -> None:
        self.username.fill(username)
        self.password.fill(password)
        self.login_button.click()

    def error_text(self) -> str:
        return self.error_message.inner_text()
