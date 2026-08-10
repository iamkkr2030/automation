from playwright.sync_api import expect

from data.users import STANDARD_USER
from pages.login_page import LoginPage
from pages.products_page import ProductsPage


def logged_in_products(page) -> ProductsPage:
    LoginPage(page).login(**STANDARD_USER)
    return ProductsPage(page)


def test_product_list_contains_names_and_prices(page):
    products = logged_in_products(page)
    expect(products.inventory_items).to_have_count(6)
    assert all(products.product_names())
    assert all(price > 0 for price in products.product_prices())


def test_sort_products_by_price_low_to_high(page):
    products = logged_in_products(page)
    products.sort_by("lohi")
    assert products.product_prices() == sorted(products.product_prices())


def test_sort_products_by_name_z_to_a(page):
    products = logged_in_products(page)
    products.sort_by("za")
    assert products.product_names() == sorted(products.product_names(), reverse=True)


def test_product_detail_page_opens(page):
    products = logged_in_products(page)
    products.open_product("Sauce Labs Backpack")
    expect(page.get_by_text("Sauce Labs Backpack", exact=True)).to_be_visible()
    expect(page).to_have_url("https://www.saucedemo.com/inventory-item.html?id=4")


def test_logout_returns_to_login_page(page):
    products = logged_in_products(page)
    products.logout()
    expect(page).to_have_url("https://www.saucedemo.com/")
    expect(page.get_by_role("button", name="Login")).to_be_visible()
