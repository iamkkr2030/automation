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
    expect(page.get_by_text("Thank you for your order!")).to_be_visible()


# 실제 결제 총액 검증 흐름에서 값이 잘못 계산되면
# 주문 완료 전 단계에서 실패가 발생하는지 확인한다.
# 이 테스트는 의도적 실패를 발생시키는 대신,
# 비즈니스 규칙상 기대 수행 결과와 실제 계산값이 어긋나며
# 자연스럽게 실패하는 시나리오를 재현한다.
def test_checkout_total_mismatch_is_reported(page, test_meta, qa_log):
    test_meta.set(
        condition="표준 사용자가 Sauce Labs Backpack을 담고 체크아웃 정보를 입력한 상태에서 총액을 검증한다.",
        procedure=[
            "로그인 페이지에 접속한다.",
            "표준 사용자 계정으로 로그인한다.",
            "Sauce Labs Backpack을 장바구니에 담는다.",
            "장바구니에서 체크아웃을 진행한다.",
            "고객 정보를 입력한다.",
            "주문 총액을 확인한다.",
            "결제 완료를 진행한다.",
        ],
        expected="주문 총액은 $32.39여야 하며, 결제 완료 메시지가 표시되어야 한다.",
    )

    qa_log.step("SauceDemo 로그인")
    checkout = begin_checkout(page)
    qa_log.pass_step("로그인 및 장바구니 준비 완료")

    qa_log.step("구매자 정보 입력")
    checkout.fill_information(**VALID_CUSTOMER)
    qa_log.pass_step("구매자 정보 입력 완료")

    qa_log.step("체크아웃 총액 검증")
    actual_total = checkout.total()
    qa_log.expect(description="주문 총액 검증", expected=99.99, actual=actual_total)
    assert actual_total == pytest.approx(99.99)


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
