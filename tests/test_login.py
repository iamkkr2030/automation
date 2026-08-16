import pytest
from playwright.sync_api import expect

from data.users import LOCKED_OUT_USER, STANDARD_USER
from pages.login_page import LoginPage


# 로그인 성공 시나리오를 검증한다.
# 표준 사용자 계정으로 인증하면
# 상품 목록 페이지로 이동해야 하며
# 사용자는 제품 목록 화면을 볼 수 있어야 한다.
# 이 테스트는 전체 로그인 흐름의 기준점 역할을 한다.
@pytest.mark.smoke
def test_valid_login_opens_products(page):
    LoginPage(page).login(**STANDARD_USER)
    expect(page).to_have_url("https://www.saucedemo.com/inventory.html")
    expect(page.get_by_text("Products", exact=True)).to_be_visible()


# 잘못된 로그인 입력에 대한 예외 처리를 검증한다.
# 여러 입력 조합을 반복해서 확인하고
# 서버가 적절한 메시지를 반환하는지 본다.
# 잘못된 사용자 이름, 비밀번호, 빈 값 모두 검증한다.
# 이 테스트는 입력 방어 로직의 안정성을 확인한다.
@pytest.mark.parametrize(
    ("username", "password", "message"),
    [
        ("standard_user", "wrong_password", "Username and password do not match"),
        ("not_a_user", "secret_sauce", "Username and password do not match"),
        ("", "secret_sauce", "Username is required"),
        ("standard_user", "", "Password is required"),
    ],
)
def test_invalid_login_shows_error(page, username, password, message):
    login = LoginPage(page)
    login.login(username, password)
    expect(login.error_message).to_contain_text(message)


# 잠금 계정 로그인 시나리오를 검증한다.
# 접근이 제한된 사용자가 로그인을 시도할 때
# 에러 메시지가 노출되고 인증이 막혀야 한다.
# 이 테스트는 보안 정책이 제대로 작동하는지 확인한다.
# 실패 시 사용자 접근 제어가 무너진 상태를 의미한다.
def test_locked_out_user_cannot_login(page):
    login = LoginPage(page)
    login.login(**LOCKED_OUT_USER)
    expect(login.error_message).to_contain_text("Sorry, this user has been locked out")
