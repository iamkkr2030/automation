import pytest
from playwright.sync_api import expect

from config.site_config import DEFAULT_CONFIG
from data.checkout_data import VALID_CUSTOMER
from data.users import STANDARD_USER
from pages.cart_page import CartPage
from pages.checkout_page import CheckoutPage
from pages.login_page import LoginPage
from pages.products_page import ProductsPage


def begin_checkout(page) -> CheckoutPage:
    LoginPage(page).login(**STANDARD_USER)
    products = ProductsPage(page)
    products.add_product(DEFAULT_CONFIG.products["backpack"])
    products.open_cart()
    CartPage(page).checkout()
    return CheckoutPage(page)


# 정상 주문 플로우를 검증한다.
# 사용자가 상품을 담고 배송 정보를 입력하면
# 주문 합계 산출과 결제 완료 화면까지 이어져야 한다.
# 마지막에는 성공 메시지가 표시되는지 확인한다.
# 이 테스트는 체크아웃의 성공 경로를 종합적으로 검증한다.
@pytest.mark.smoke
def test_complete_checkout(page):
    checkout = begin_checkout(page)
    checkout.fill_information(**VALID_CUSTOMER)
    checkout.continue_checkout()
    assert checkout.total() == pytest.approx(32.39)
    checkout.finish()
    expect(page.get_by_text(DEFAULT_CONFIG.selectors["checkout"]["success_message"])).to_be_visible()


# 체크아웃 총액이 실제 계산과 일치하는지 검증한다.
# 사용자는 각 상품 금액과 세금이 반영된 최종 총액을 확인할 수 있어야 한다.
# 이 테스트는 정상 계산 로직을 고정하여 회귀가 생기지 않도록 보호하는 역할을 한다.
def test_checkout_total_is_reported(page, test_meta, qa_log):
    test_meta.set(
        condition=f"표준 사용자가 {DEFAULT_CONFIG.products['backpack']}을 담고 체크아웃 정보를 입력한 상태에서 총액을 검증한다.",
        procedure=[
            "로그인 페이지에 접속한다.",
            "표준 사용자 계정으로 로그인한다.",
            f"{DEFAULT_CONFIG.products['backpack']}을 장바구니에 담는다.",
            "장바구니에서 체크아웃을 진행한다.",
            "고객 정보를 입력한다.",
            "주문 총액을 확인한다.",
            "결제 완료를 진행한다.",
        ],
        expected=f"주문 총액은 ${32.39:,.2f}여야 하며, 결제 완료 메시지가 표시되어야 한다.",
    )

    qa_log.step("SauceDemo 로그인")
    checkout = begin_checkout(page)
    qa_log.pass_step("로그인 및 장바구니 준비 완료")

    qa_log.step("구매자 정보 입력")
    checkout.fill_information(**VALID_CUSTOMER)
    qa_log.pass_step("구매자 정보 입력 완료")

    qa_log.step("체크아웃 총액 검증")
    actual_total = checkout.total()
    qa_log.expect(description="주문 총액 검증", expected=32.39, actual=actual_total)
    assert actual_total == pytest.approx(32.39)


# 필수 입력값 누락 시 처리 로직을 검증한다.
# 이름이 비어 있는 상태에서 다음 단계를 진행하면
# 사용자에게 적절한 오류 메시지가 표시되어야 한다.
# 이 테스트는 폼 검증이 실제로 막는지 확인하는 핵심 시나리오다.
# 잘못 검증되면 결제 단계에서 잘못된 주문이 생성될 수 있다.
def test_checkout_requires_first_name(page):
    checkout = begin_checkout(page)
    checkout.fill_information("", "Lovelace", "12345")
    checkout.continue_checkout()
    expect(checkout.error_message).to_contain_text("First Name is required")


# 성이 비어 있는 상태에서 다음 단계로 진행하면
# 사용자에게 적절한 오류 메시지가 노출되어야 한다.
# 이 검증은 체크아웃 유효성 검사가 마지막 이름까지 포함하는지 확인한다.
def test_checkout_requires_last_name(page):
    checkout = begin_checkout(page)
    checkout.fill_information("Ada", "", "12345")
    checkout.continue_checkout()
    expect(checkout.error_message).to_contain_text("Last Name is required")


# 우편번호가 비어 있는 상태에서 다음 단계로 진행하면
# 사용자에게 적절한 오류 메시지가 노출되어야 한다.
# 이는 배송 정보 누락으로 주문이 잘못 생성되는 문제를 막는 핵심 검증이다.
def test_checkout_requires_postal_code(page):
    checkout = begin_checkout(page)
    checkout.fill_information("Ada", "Lovelace", "")
    checkout.continue_checkout()
    expect(checkout.error_message).to_contain_text("Postal Code is required")


# 여러 상품을 담았을 때 주문 총액이 실제 산출 결과와 맞는지 검증한다.
# 사용자는 장바구니 합계와 세금이 반영된 최종 금액을 확인할 수 있어야 한다.
# 상품 조합이 늘어나면 계산 오류가 발생할 수 있으므로 다중 상품 시나리오가 중요하다.
def test_checkout_total_for_multiple_items(page):
    LoginPage(page).login(**STANDARD_USER)
    products = ProductsPage(page)
    products.add_product(DEFAULT_CONFIG.products["backpack"])
    products.add_product(DEFAULT_CONFIG.products["bike_light"])
    products.open_cart()

    cart = CartPage(page)
    cart.checkout()

    checkout = CheckoutPage(page)
    checkout.fill_information(**VALID_CUSTOMER)
    checkout.continue_checkout()

    assert checkout.total() == pytest.approx(43.18)
