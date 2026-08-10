from __future__ import annotations

import os
import shutil
import time
from pathlib import Path

import pytest
from playwright.sync_api import Browser, Page, sync_playwright
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service

BASE_URL = "https://www.saucedemo.com/"


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption("--headed", action="store_true", help="브라우저 창을 표시합니다.")
    parser.addoption("--slowmo", action="store", default=0, type=int, help="동작 사이 지연(ms)")
    parser.addoption("--selenium-headed", action="store_true", help="Selenium Chrome 창을 표시합니다.")
    parser.addoption(
        "--chromedriver",
        action="store",
        default=os.getenv("CHROMEDRIVER_PATH"),
        help="chromedriver.exe 경로 (또는 CHROMEDRIVER_PATH 환경 변수)",
    )
    parser.addoption("--step-delay", action="store", default=0, type=float, help="Selenium 단계별 지연(초)")


@pytest.fixture(scope="session")
def browser(request: pytest.FixtureRequest) -> Browser:
    with sync_playwright() as playwright:
        yield playwright.chromium.launch(
            headless=not request.config.getoption("--headed"),
            slow_mo=request.config.getoption("--slowmo"),
        )


@pytest.fixture
def page(browser: Browser, request: pytest.FixtureRequest) -> Page:
    context = browser.new_context(viewport={"width": 1440, "height": 900})
    context.tracing.start(screenshots=True, snapshots=True, sources=True)
    page = context.new_page()
    page.goto(BASE_URL, wait_until="domcontentloaded")
    yield page

    failed = hasattr(request.node, "rep_call") and request.node.rep_call.failed
    if failed:
        safe_name = request.node.nodeid.replace("::", "_").replace("/", "_").replace("\\", "_")
        Path("screenshots").mkdir(exist_ok=True)
        page.screenshot(path=f"screenshots/{safe_name}_failed.png", full_page=True)
        Path("traces").mkdir(exist_ok=True)
        context.tracing.stop(path=f"traces/{safe_name}.zip")
    else:
        context.tracing.stop()
    context.close()


@pytest.fixture
def selenium_driver(request: pytest.FixtureRequest):
    """Use an explicit/cached ChromeDriver, falling back to Selenium Manager."""
    options = Options()
    if not request.config.getoption("--selenium-headed"):
        options.add_argument("--headless=new")
    options.add_argument("--window-size=1440,900")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    chrome_binary = Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe")
    if chrome_binary.is_file():
        options.binary_location = str(chrome_binary)

    configured_path = request.config.getoption("--chromedriver")
    if configured_path:
        driver_path = Path(configured_path)
        if not driver_path.is_file():
            raise pytest.UsageError(f"ChromeDriver를 찾을 수 없습니다: {driver_path}")
        driver = webdriver.Chrome(service=Service(str(driver_path)), options=options)
    else:
        # Selenium Manager cache prevents a new network lookup on later runs.
        cached_drivers = sorted(Path.home().glob(".cache/selenium/chromedriver/*/*/chromedriver.exe"))
        if cached_drivers:
            driver = webdriver.Chrome(service=Service(str(cached_drivers[-1])), options=options)
        else:
            driver = webdriver.Chrome(options=options)
    driver.implicitly_wait(0)
    driver.get(BASE_URL)
    safe_name = request.node.nodeid.replace("::", "_").replace("/", "_").replace("\\", "_")
    driver.evidence_dir = Path("screenshots") / safe_name
    driver.evidence_step = 0
    driver.step_delay = request.config.getoption("--step-delay")
    if driver.evidence_dir.exists():
        shutil.rmtree(driver.evidence_dir)
    driver.evidence_dir.mkdir(parents=True, exist_ok=True)
    driver.save_screenshot(str(driver.evidence_dir / "00_login_page.png"))
    yield driver

    failed = hasattr(request.node, "rep_call") and request.node.rep_call.failed
    if failed:
        driver.save_screenshot(str(driver.evidence_dir / "failed.png"))
    driver.quit()


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item: pytest.Item, call: pytest.CallInfo[object]):
    outcome = yield
    report = outcome.get_result()
    setattr(item, f"rep_{report.when}", report)
