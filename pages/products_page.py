from playwright.sync_api import Page


class ProductsPage:
    def __init__(self, page: Page):
        self.page = page
        self.title = page.get_by_text("Products", exact=True)
        self.inventory_items = page.locator(".inventory_item")
        self.sort_select = page.locator("[data-test='product-sort-container']")
        self.cart_badge = page.locator("[data-test='shopping-cart-badge']")

    def product_names(self) -> list[str]:
        return self.page.locator(".inventory_item_name").all_inner_texts()

    def product_prices(self) -> list[float]:
        texts = self.page.locator(".inventory_item_price").all_inner_texts()
        return [float(price.replace("$", "")) for price in texts]

    def sort_by(self, option: str) -> None:
        self.sort_select.select_option(option)

    def add_product(self, product_name: str) -> None:
        item = self.page.locator(".inventory_item").filter(has_text=product_name)
        item.get_by_role("button", name="Add to cart").click()

    def open_cart(self) -> None:
        self.page.locator("[data-test='shopping-cart-link']").click()

    def open_product(self, product_name: str) -> None:
        self.page.get_by_text(product_name, exact=True).click()

    def logout(self) -> None:
        self.page.get_by_role("button", name="Open Menu").click()
        self.page.get_by_role("link", name="Logout").click()
