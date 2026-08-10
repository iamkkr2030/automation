from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from selenium_pages.base_page import SeleniumBasePage


class SeleniumCheckoutPage(SeleniumBasePage):

    def fill_information(self, first_name: str, last_name: str, postal_code: str) -> None:
        for field_id, value in (("first-name", first_name), ("last-name", last_name), ("postal-code", postal_code)):
            field = WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.ID, field_id)))
            self.driver.execute_script(
                """
                const setter = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value').set;
                setter.call(arguments[0], arguments[1]);
                arguments[0].dispatchEvent(new Event('input', {bubbles: true}));
                arguments[0].dispatchEvent(new Event('change', {bubbles: true}));
                """,
                field,
                value,
            )
            WebDriverWait(self.driver, 10).until(lambda driver: field.get_attribute("value") == value)
        self.capture_step("customer_information_entered")

    def continue_checkout(self) -> None:
        continue_button = WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.ID, "continue")))
        self.driver.execute_script("arguments[0].click();", continue_button)
        WebDriverWait(self.driver, 10).until(EC.url_contains("checkout-step-two.html"))
        self.capture_step("order_review_opened")

    def finish(self) -> None:
        finish_button = WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.ID, "finish")))
        self.driver.execute_script("arguments[0].click();", finish_button)
        WebDriverWait(self.driver, 10).until(EC.url_contains("checkout-complete.html"))
        self.capture_step("order_completed")
