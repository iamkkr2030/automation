import pytest
from playwright.sync_api import expect

from data.checkout_data import VALID_CUSTOMER
from data.users import STANDARD_USER
from pages.cart_page import CartPage
from pages.checkout_page import CheckoutPage
from pages.login_page import LoginPage
from pages.products_page import ProductsPage


def begin_checkout(page) -> CheckoutPage:
    LoginPage(page).login(**STANDARD_USER)
    products = ProductsPage(page)
    products.add_product("Sauce Labs Backpack")
    products.open_cart()
    CartPage(page).checkout()
    return CheckoutPage(page)


@pytest.mark.smoke
def test_complete_checkout(page):
    checkout = begin_checkout(page)
    checkout.fill_information(**VALID_CUSTOMER)
    checkout.continue_checkout()
    assert checkout.total() == pytest.approx(32.39)
    checkout.finish()
    expect(page.get_by_text("Thank you for your order!")).to_be_visible()


def test_checkout_requires_first_name(page):
    checkout = begin_checkout(page)
    checkout.fill_information("", "Lovelace", "12345")
    checkout.continue_checkout()
    expect(checkout.error_message).to_contain_text("First Name is required")
