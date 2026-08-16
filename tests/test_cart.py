from playwright.sync_api import expect

from data.users import STANDARD_USER
from pages.cart_page import CartPage
from pages.login_page import LoginPage
from pages.products_page import ProductsPage


# 장바구니에 상품을 추가하고 제거하는 흐름을 검증한다.
# 사용자는 상품을 담고 카운트가 증가하는지 확인하며
# 장바구니 화면에서 항목이 정상적으로 표시되는지 본다.
# 마지막에는 항목을 제거하고 상태가 비워지는지 점검한다.
# 이 테스트는 장바구니의 기본 CRUD 동작을 보장한다.
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


# 여러 상품을 동시에 담는 동작을 검증한다.
# 사용자가 두 개 이상의 상품을 장바구니에 추가하면
# 카운트가 올바르게 누적되고 장바구니 목록에도 순서대로 표시된다.
# 이 테스트는 다중 선택 상태를 검증하는 핵심 시나리오다.
# 장바구니 수량 계산이 잘못되면 결제 단계에서 오류가 발생한다.
def test_add_multiple_cart_items(page):
    LoginPage(page).login(**STANDARD_USER)
    products = ProductsPage(page)
    products.add_product("Sauce Labs Backpack")
    products.add_product("Sauce Labs Bike Light")
    expect(products.cart_badge).to_have_text("2")
    products.open_cart()
    assert CartPage(page).item_names() == ["Sauce Labs Backpack", "Sauce Labs Bike Light"]
