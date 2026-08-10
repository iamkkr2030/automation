from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from selenium_pages.base_page import SeleniumBasePage


class SeleniumCartPage(SeleniumBasePage):

    def item_names(self) -> list[str]:
        return [element.text for element in self.driver.find_elements(By.CSS_SELECTOR, ".inventory_item_name")]

    def checkout(self) -> None:
        checkout_button = WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.ID, "checkout")))
        self.driver.execute_script("arguments[0].click();", checkout_button)
        WebDriverWait(self.driver, 10).until(EC.url_contains("checkout-step-one.html"))
        WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.ID, "first-name")))
        self.capture_step("checkout_started")
