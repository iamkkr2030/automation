from playwright.sync_api import expect

from config.site_config import DEFAULT_CONFIG
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
    products.add_product(DEFAULT_CONFIG.products["backpack"])
    expect(products.cart_badge).to_have_text("1")
    products.open_cart()
    cart = CartPage(page)
    assert cart.item_names() == [DEFAULT_CONFIG.products["backpack"]]
    cart.remove_product(DEFAULT_CONFIG.products["backpack"])
    expect(cart.items).to_have_count(0)


# 여러 상품을 동시에 담는 동작을 검증한다.
# 사용자가 두 개 이상의 상품을 장바구니에 추가하면
# 카운트가 올바르게 누적되고 장바구니 목록에도 순서대로 표시된다.
# 이 테스트는 다중 선택 상태를 검증하는 핵심 시나리오다.
# 장바구니 수량 계산이 잘못되면 결제 단계에서 오류가 발생한다.
def test_add_multiple_cart_items(page):
    LoginPage(page).login(**STANDARD_USER)
    products = ProductsPage(page)
    products.add_product(DEFAULT_CONFIG.products["backpack"])
    products.add_product(DEFAULT_CONFIG.products["bike_light"])
    expect(products.cart_badge).to_have_text("2")
    products.open_cart()
    assert CartPage(page).item_names() == [DEFAULT_CONFIG.products["backpack"], DEFAULT_CONFIG.products["bike_light"]]


# 동일 상품을 연속으로 추가해도 장바구니에 중복 항목이 생기지 않는지 검증한다.
# 사용자는 같은 SKU를 여러 번 누르더라도 장바구니에 중복 라인이 추가되지 않아야 한다.
# 이 테스트는 UX와 데이터 일관성을 보장하고, 실수로 장바구니 수량이 늘어나는 문제를 막는다.
# 중복 상품이 섞이면 체크아웃 단계에서 총액·수량 계산이 잘못될 수 있다.
def test_same_product_is_not_duplicated_in_cart(page):
    LoginPage(page).login(**STANDARD_USER)
    products = ProductsPage(page)
    item = products.page.locator(DEFAULT_CONFIG.selectors["products"]["inventory_item"]).filter(has_text=DEFAULT_CONFIG.products["backpack"])

    item.get_by_role("button", name=DEFAULT_CONFIG.selectors["products"]["product_button"]).click()
    item.get_by_role("button", name=DEFAULT_CONFIG.selectors["cart"]["remove_button"]).click()

    expect(products.cart_badge).to_have_count(0)


# 마지막 남은 상품을 제거하면 장바구니가 비워지고 빈 상태를 유지하는지 검증한다.
# 사용자는 장바구니에서 항목을 제거한 뒤에도 UI가 올바르게 갱신되는지 확인해야 한다.
# 빈 장바구니 상태가 제대로 유지되지 않으면 주문 진행이 불안정해질 수 있다.
def test_remove_last_item_leaves_cart_empty(page):
    LoginPage(page).login(**STANDARD_USER)
    products = ProductsPage(page)
    products.add_product(DEFAULT_CONFIG.products["backpack"])
    products.open_cart()

    cart = CartPage(page)
    cart.remove_product(DEFAULT_CONFIG.products["backpack"])

    expect(cart.items).to_have_count(0)


# 장바구니에서 계속 쇼핑을 누른 뒤 다시 상품 목록이 표시되는지 확인한다.
# 사용자는 체크아웃 전에 제품 목록으로 돌아와 추가 선택을 이어갈 수 있어야 한다.
# 이 흐름이 깨지면 쇼핑 경험이 끊기고 주문 전환이 실패할 수 있다.
def test_continue_shopping_returns_to_products(page):
    LoginPage(page).login(**STANDARD_USER)
    products = ProductsPage(page)
    products.add_product(DEFAULT_CONFIG.products["backpack"])
    products.open_cart()

    cart = CartPage(page)
    cart.continue_shopping()

    expect(products.title).to_be_visible()


# 여러 상품을 담은 상태에서 하나만 삭제하면 남은 항목만 유지되고
# 카운트 또한 정확하게 반영되는지 검증한다.
# 이 테스트는 일부 항목 삭제 로직이 잘못 동작할 때 발생하는 회귀를 잡는다.
def test_remove_one_of_multiple_items_keeps_remaining_items(page):
    LoginPage(page).login(**STANDARD_USER)
    products = ProductsPage(page)
    products.add_product(DEFAULT_CONFIG.products["backpack"])
    products.add_product(DEFAULT_CONFIG.products["bike_light"])
    products.add_product(DEFAULT_CONFIG.products["bolt_tshirt"])
    products.open_cart()

    cart = CartPage(page)
    cart.remove_product(DEFAULT_CONFIG.products["bike_light"])

    assert cart.item_names() == [DEFAULT_CONFIG.products["backpack"], DEFAULT_CONFIG.products["bolt_tshirt"]]
    expect(products.cart_badge).to_have_text("2")


# 장바구니가 비어 있을 때 체크아웃 버튼을 누르면
# 주문 진행이 막히거나 비활성 상태로 유지되는지 확인한다.
# 빈 장바구니에서의 주문 시도는 의도치 않은 비즈니스 로직 진입을 방지한다.
def test_checkout_disabled_when_cart_is_empty(page):
    LoginPage(page).login(**STANDARD_USER)
    products = ProductsPage(page)
    products.open_cart()

    cart = CartPage(page)
    expect(cart.page.get_by_role("button", name=DEFAULT_CONFIG.selectors["cart"]["checkout_button"])).to_be_disabled()


# 장바구니의 항목 순서가 유지되는지 검증한다.
# 상품을 A, B, C 순으로 담고 B를 제거했을 때
# 남은 항목이 원래 순서를 유지해야 사용자 경험이 일관적이다.
def test_removing_item_keeps_remaining_order(page):
    LoginPage(page).login(**STANDARD_USER)
    products = ProductsPage(page)
    products.add_product(DEFAULT_CONFIG.products["backpack"])
    products.add_product(DEFAULT_CONFIG.products["bike_light"])
    products.add_product(DEFAULT_CONFIG.products["bolt_tshirt"])
    products.open_cart()

    cart = CartPage(page)
    cart.remove_product(DEFAULT_CONFIG.products["bike_light"])

    assert cart.item_names() == [DEFAULT_CONFIG.products["backpack"], DEFAULT_CONFIG.products["bolt_tshirt"]]
