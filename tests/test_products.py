from playwright.sync_api import expect

from data.users import STANDARD_USER
from pages.login_page import LoginPage
from pages.products_page import ProductsPage


def logged_in_products(page) -> ProductsPage:
    LoginPage(page).login(**STANDARD_USER)
    return ProductsPage(page)


# 상품 목록의 기본 정보를 검증한다.
# 인증 후 상품이 6개 표시되는지 확인하고
# 각 상품 이름과 가격이 정상 범위인지 점검한다.
# 목록 자체가 비어 있거나 이상한 값이면 쇼핑 흐름 전체가 깨진다.
# 이 테스트는 카탈로그 품질을 보장하는 기준 역할을 한다.
def test_product_list_contains_names_and_prices(page):
    products = logged_in_products(page)
    expect(products.inventory_items).to_have_count(6)
    assert all(products.product_names())
    assert all(price > 0 for price in products.product_prices())


# 가격 오름차순 정렬 동작을 검증한다.
# 낮은 가격 순으로 정렬을 적용한 뒤
# 실제 표시 순서가 기대한 정렬 결과와 일치하는지 확인한다.
# 정렬 로직이 깨지면 사용자는 상품을 올바르게 비교할 수 없다.
# 이 테스트는 필터링 기능의 신뢰성을 검증한다.
def test_sort_products_by_price_low_to_high(page):
    products = logged_in_products(page)
    products.sort_by("lohi")
    assert products.product_prices() == sorted(products.product_prices())


# 이름 내림차순 정렬 동작을 검증한다.
# Z부터 A 순서로 정렬을 적용하고
# 상품 명칭 배열이 예상 순서대로 정렬되는지 확인한다.
# 다양한 정렬 옵션이 모두 보장되어야 사용자 경험이 일관된다.
# 이 테스트는 정렬 옵션의 로직 무결성을 확인한다.
def test_sort_products_by_name_z_to_a(page):
    products = logged_in_products(page)
    products.sort_by("za")
    assert products.product_names() == sorted(products.product_names(), reverse=True)


# 상품 상세 페이지 이동 흐름을 검증한다.
# 특정 상품을 선택하면 상세 페이지로 진입하고
# 해당 상품 이름과 URL이 일치하는지 확인한다.
# 상세 진입이 실패하면 사용자가 상품 정보를 신뢰할 수 없다.
# 이 테스트는 상품 탐색의 핵심 경로를 점검한다.
def test_product_detail_page_opens(page):
    products = logged_in_products(page)
    products.open_product("Sauce Labs Backpack")
    expect(page.get_by_text("Sauce Labs Backpack", exact=True)).to_be_visible()
    expect(page).to_have_url("https://www.saucedemo.com/inventory-item.html?id=4")


# 로그아웃이 정상적으로 동작하는지 검증한다.
# 로그아웃 후 로그인 페이지로 복귀하는지 확인하고
# 다시 로그인 버튼이 노출되는지 점검한다.
# 세션 종료가 잘못되면 사용자 보안과 흐름 안정성이 깨진다.
# 이 테스트는 사용자 세션 종료 기능의 완성도를 확인한다.
def test_logout_returns_to_login_page(page):
    products = logged_in_products(page)
    products.logout()
    expect(page).to_have_url("https://www.saucedemo.com/")
    expect(page.get_by_role("button", name="Login")).to_be_visible()
