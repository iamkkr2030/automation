import pytest
from playwright.sync_api import expect

from data.users import LOCKED_OUT_USER, STANDARD_USER
from pages.login_page import LoginPage


@pytest.mark.smoke
def test_valid_login_opens_products(page):
    LoginPage(page).login(**STANDARD_USER)
    expect(page).to_have_url("https://www.saucedemo.com/inventory.html")
    expect(page.get_by_text("Products", exact=True)).to_be_visible()


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


def test_locked_out_user_cannot_login(page):
    login = LoginPage(page)
    login.login(**LOCKED_OUT_USER)
    expect(login.error_message).to_contain_text("Sorry, this user has been locked out")
