from playwright.sync_api import Page


class CartPage:
    def __init__(self, page: Page):
        self.page = page
        self.items = page.locator(".cart_item")

    def item_names(self) -> list[str]:
        return self.page.locator(".inventory_item_name").all_inner_texts()

    def remove_product(self, product_name: str) -> None:
        item = self.page.locator(".cart_item").filter(has_text=product_name)
        item.get_by_role("button", name="Remove").click()

    def checkout(self) -> None:
        self.page.get_by_role("button", name="Checkout").click()

    def continue_shopping(self) -> None:
        self.page.get_by_role("button", name="Continue Shopping").click()
