from playwright.sync_api import Page


class CheckoutPage:
    def __init__(self, page: Page):
        self.page = page
        self.error_message = page.locator("[data-test='error']")

    def fill_information(self, first_name: str, last_name: str, postal_code: str) -> None:
        self.page.locator("[data-test='firstName']").fill(first_name)
        self.page.locator("[data-test='lastName']").fill(last_name)
        self.page.locator("[data-test='postalCode']").fill(postal_code)

    def continue_checkout(self) -> None:
        self.page.get_by_role("button", name="Continue").click()

    def finish(self) -> None:
        self.page.get_by_role("button", name="Finish").click()

    def total(self) -> float:
        return float(self.page.locator(".summary_total_label").inner_text().replace("Total: $", ""))
