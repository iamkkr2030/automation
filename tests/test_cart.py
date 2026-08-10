from playwright.sync_api import expect

from data.users import STANDARD_USER
from pages.cart_page import CartPage
from pages.login_page import LoginPage
from pages.products_page import ProductsPage


def test_add_and_remove_cart_item(page):
    LoginPage(page).login(**STANDARD_USER)
    products = ProductsPage(page)
    products.add_product("Sauce Labs Backpack")
    expect(products.cart_badge).to_have_text("1")
    products.open_cart()
    cart = CartPage(page)
    assert cart.item_names() == ["Sauce Labs Backpack"]
    cart.remove_product("Sauce Labs Backpack")
    expect(cart.items).to_have_count(0)


def test_add_multiple_cart_items(page):
    LoginPage(page).login(**STANDARD_USER)
    products = ProductsPage(page)
    products.add_product("Sauce Labs Backpack")
    products.add_product("Sauce Labs Bike Light")
    expect(products.cart_badge).to_have_text("2")
    products.open_cart()
    assert CartPage(page).item_names() == ["Sauce Labs Backpack", "Sauce Labs Bike Light"]
