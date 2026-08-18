from __future__ import annotations

from playwright.sync_api import Page

from config.site_config import DEFAULT_CONFIG
from pages.base_page import BasePage


class CartPage(BasePage):
    def __init__(self, page: Page, config=None):
        super().__init__(page, config or DEFAULT_CONFIG)
        selectors = self.selectors["cart"]
        self.items = page.locator(selectors["item"])

    def item_names(self) -> list[str]:
        return self.page.locator(self.selectors["products"]["inventory_item_name"]).all_inner_texts()

    def remove_product(self, product_name: str) -> None:
        item = self.page.locator(self.selectors["cart"]["item"]).filter(has_text=product_name)
        item.get_by_role("button", name=self.selectors["cart"]["remove_button"]).click()

    def checkout(self) -> None:
        self.page.get_by_role("button", name=self.selectors["cart"]["checkout_button"]).click()

    def continue_shopping(self) -> None:
        self.page.get_by_role("button", name=self.selectors["cart"]["continue_button"]).click()
