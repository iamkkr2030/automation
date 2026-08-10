from selenium.webdriver.common.by import By

from selenium_pages.base_page import SeleniumBasePage


class SeleniumLoginPage(SeleniumBasePage):

    def login(self, username: str, password: str) -> None:
        self.driver.find_element(By.ID, "user-name").send_keys(username)
        self.driver.find_element(By.ID, "password").send_keys(password)
        self.driver.find_element(By.ID, "login-button").click()
        self.capture_step("login_submitted")

    def error_text(self) -> str:
        return self.driver.find_element(By.CSS_SELECTOR, "[data-test='error']").text
