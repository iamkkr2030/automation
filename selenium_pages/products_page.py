from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait

from selenium_pages.base_page import SeleniumBasePage


class SeleniumProductsPage(SeleniumBasePage):

    def product_names(self) -> list[str]:
        return [element.text for element in self.driver.find_elements(By.CSS_SELECTOR, ".inventory_item_name")]

    def add_product(self, product_name: str) -> None:
        item = self.driver.find_element(By.XPATH, f"//div[@class='inventory_item'][.//div[text()={product_name!r}]]")
        item.find_element(By.TAG_NAME, "button").click()
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "[data-test='shopping-cart-badge']"))
        )
        self.capture_step("product_added")

    def cart_count(self) -> str:
        badge = WebDriverWait(self.driver, 10).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-test='shopping-cart-badge']"))
        )
        return badge.text

    def open_cart(self) -> None:
        cart_link = WebDriverWait(self.driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "[data-test='shopping-cart-link']"))
        )
        self.driver.execute_script("arguments[0].click();", cart_link)
        WebDriverWait(self.driver, 10).until(EC.url_contains("cart.html"))
        self.capture_step("cart_opened")

    def sort_by(self, value: str) -> None:
        Select(self.driver.find_element(By.CSS_SELECTOR, "[data-test='product-sort-container']")).select_by_value(value)
        self.capture_step(f"products_sorted_{value}")

    def reset_app_state(self) -> None:
        """Remove every item so a test starts with a predictable cart."""
        self.driver.find_element(By.CSS_SELECTOR, "[data-test='shopping-cart-link']").click()
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.ID, "continue-shopping"))
        )
        while self.driver.find_elements(By.CSS_SELECTOR, ".cart_button"):
            self.driver.find_elements(By.CSS_SELECTOR, ".cart_button")[0].click()
        WebDriverWait(self.driver, 10).until(
            EC.element_to_be_clickable((By.ID, "continue-shopping"))
        ).click()
        WebDriverWait(self.driver, 10).until(EC.url_contains("inventory.html"))
        WebDriverWait(self.driver, 10).until(
            EC.element_to_be_clickable((By.ID, "add-to-cart-sauce-labs-backpack"))
        )
        self.capture_step("app_state_reset")
