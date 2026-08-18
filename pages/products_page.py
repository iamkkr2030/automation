from __future__ import annotations

from playwright.sync_api import Page

from config.site_config import DEFAULT_CONFIG
from pages.base_page import BasePage


class ProductsPage(BasePage):
    def __init__(self, page: Page, config=None):
        super().__init__(page, config or DEFAULT_CONFIG)
        selectors = self.selectors["products"]
        self.title = page.get_by_text(selectors["title"], exact=True)
        self.inventory_items = page.locator(selectors["inventory_item"])
        self.sort_select = page.locator(selectors["sort_container"])
        self.cart_badge = page.locator(selectors["cart_badge"])
        self.cart_link = page.locator(selectors["shopping_cart_link"])

    def product_names(self) -> list[str]:
        return self.page.locator(self.selectors["products"]["inventory_item_name"]).all_inner_texts()

    def product_prices(self) -> list[float]:
        texts = self.page.locator(self.selectors["products"]["inventory_item_price"]).all_inner_texts()
        return [float(price.replace("$", "")) for price in texts]

    def sort_by(self, option: str) -> None:
        self.sort_select.select_option(option)

    def add_product(self, product_name: str) -> None:
        item = self.page.locator(self.selectors["products"]["inventory_item"]).filter(has_text=product_name)
        item.get_by_role("button", name=self.selectors["products"]["product_button"]).click()

    def open_cart(self) -> None:
        self.cart_link.click()

    def open_product(self, product_name: str) -> None:
        self.page.get_by_text(product_name, exact=True).click()

    def logout(self) -> None:
        self.page.get_by_role("button", name="Open Menu").click()
        self.page.get_by_role("link", name="Logout").click()
