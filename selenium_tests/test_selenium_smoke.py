import pytest
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from data.checkout_data import VALID_CUSTOMER
from data.users import STANDARD_USER
from selenium_pages.cart_page import SeleniumCartPage
from selenium_pages.checkout_page import SeleniumCheckoutPage
from selenium_pages.login_page import SeleniumLoginPage
from selenium_pages.products_page import SeleniumProductsPage


def wait(driver):
    return WebDriverWait(driver, 10)


@pytest.mark.selenium
@pytest.mark.smoke
def test_selenium_login_and_sort(selenium_driver):
    SeleniumLoginPage(selenium_driver).login(**STANDARD_USER)
    wait(selenium_driver).until(EC.url_contains("inventory.html"))
    products = SeleniumProductsPage(selenium_driver)
    products.sort_by("za")
    assert products.product_names() == sorted(products.product_names(), reverse=True)


@pytest.mark.selenium
@pytest.mark.smoke
def test_selenium_complete_checkout(selenium_driver):
    SeleniumLoginPage(selenium_driver).login(**STANDARD_USER)
    wait(selenium_driver).until(EC.url_contains("inventory.html"))
    products = SeleniumProductsPage(selenium_driver)
    products.add_product("Sauce Labs Backpack")
    assert int(products.cart_count()) >= 1
    products.open_cart()
    cart = SeleniumCartPage(selenium_driver)
    assert "Sauce Labs Backpack" in cart.item_names()
    cart.checkout()
    checkout = SeleniumCheckoutPage(selenium_driver)
    checkout.fill_information(**VALID_CUSTOMER)
    checkout.continue_checkout()
    wait(selenium_driver).until(EC.url_contains("checkout-step-two.html"))
    checkout.finish()
    assert "Thank you for your order!" in selenium_driver.page_source
