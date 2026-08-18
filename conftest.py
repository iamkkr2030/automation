from __future__ import annotations

import datetime
import json
import logging
import os
import platform
import sys
from collections.abc import Iterator
from pathlib import Path

import pytest
from playwright.sync_api import Browser, Page, sync_playwright

from config.site_config import DEFAULT_CONFIG
from qa_reporting import (
    _build_failure_metadata,
    _extract_failure_facts,
    _infer_expected_result,
    _infer_test_procedure,
    _safe_test_name,
    save_bug_report,
)

PASS_LEVEL = 25
FAIL_LEVEL = 35
logging.addLevelName(PASS_LEVEL, "PASS")
logging.addLevelName(FAIL_LEVEL, "FAIL")

BASE_URL = os.getenv("BASE_URL", DEFAULT_CONFIG.base_url)
LOGS_DIR = Path("logs")
REPORTS_DIR = Path("reports")
BUG_REPORT_DIR = REPORTS_DIR / "bug_reports"
LOG_FILE: Path | None = None
LOG_HANDLER: logging.Handler | None = None
LOGGER = logging.getLogger("automation")
TEST_RESULTS: list[dict] = []
BROWSER_VERSION = "unknown"


class QATestFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        timestamp = self.formatTime(record, self.datefmt or "%Y-%m-%d %H:%M:%S")
        test_id = getattr(record, "test_id", "SYSTEM")
        return f"[{timestamp}] [{record.levelname}] [{test_id}] {record.getMessage()}"
class TestSteps:
    def __init__(self) -> None:
        self.steps: list[dict] = []

    def add(self, description: str, expected: str | None = None) -> None:
        entry = {
            "time": datetime.datetime.now().isoformat(),
            "description": description,
            "expected": expected or "",
        }
        LOGGER.info("Step - %s | expected: %s", description, expected)
        self.steps.append(entry)


class TestLogContext:
    def __init__(self, item: pytest.Item):
        self.item = item
        self.test_id = item.nodeid
        self.test_name = item.name
        self.current_step = 0
        self.last_step = ""

    def start(self) -> None:
        LOGGER.info("========================================")
        LOGGER.info("TEST START")
        LOGGER.info("Test ID: %s", self.test_id)
        LOGGER.info("Test Name: %s", self.test_name)
        LOGGER.info("Browser: Chromium")
        LOGGER.info("Environment: SauceDemo")
        LOGGER.info("========================================")

    def step(self, description: str) -> None:
        self.current_step += 1
        self.last_step = description
        LOGGER.info("Step %02d - %s", self.current_step, description)

    def info(self, message: str) -> None:
        LOGGER.info(message)

    def pass_step(self, message: str) -> None:
        LOGGER.log(PASS_LEVEL, message)

    def fail_step(self, message: str) -> None:
        LOGGER.log(FAIL_LEVEL, message)

    def expect(self, *, description: str, expected: object, actual: object) -> bool:
        LOGGER.info("%s", description)
        LOGGER.info("Expected: %s", expected)
        LOGGER.info("Actual: %s", actual)
        passed = expected == actual
        if passed:
            self.pass_step(f"{description} 검증 성공")
        else:
            self.fail_step(f"{description} 검증 실패")
        return passed

    def assert_equal(self, *, description: str, expected: object, actual: object) -> None:
        if not self.expect(description=description, expected=expected, actual=actual):
            raise AssertionError(f"{description}: expected={expected!r}, actual={actual!r}")

    def end(self, result: str) -> None:
        LOGGER.info("========================================")
        LOGGER.log(PASS_LEVEL if result == "PASSED" else FAIL_LEVEL, "[%s] TEST %s", self.test_id, result)
        LOGGER.info("========================================")


class TestCaseMeta:
    def __init__(self) -> None:
        self.condition: str = ""
        self.procedure: list[str] = []
        self.expected: str = ""

    def set(self, *, condition: str = "", procedure: list[str] | None = None, expected: str = "") -> None:
        if condition:
            self.condition = condition
        if procedure is not None:
            self.procedure = procedure
        if expected:
            self.expected = expected


@pytest.fixture
def qa_log(request: pytest.FixtureRequest):
    log_context = getattr(request.node, "qa_log", None)
    if log_context is None:
        log_context = TestLogContext(request.node)
        request.node.qa_log = log_context
        log_context.start()
    yield log_context


@pytest.fixture(scope="session")
def browser(request: pytest.FixtureRequest) -> Iterator[Browser]:
    global BROWSER_VERSION
    LOGGER.info("Launching Playwright browser")
    with sync_playwright() as playwright:
        launched_browser = playwright.chromium.launch(
            headless=not request.config.getoption("--headed"),
            slow_mo=request.config.getoption("--slowmo"),
        )
        BROWSER_VERSION = launched_browser.version
        yield launched_browser


@pytest.fixture
def page(browser: Browser, request: pytest.FixtureRequest, test_steps: TestSteps) -> Iterator[Page]:
    LOGGER.info("Creating browser context and opening page")
    context = browser.new_context(viewport={"width": 1440, "height": 900})
    context.tracing.start(screenshots=True, snapshots=True, sources=True)
    page = context.new_page()
    request.node.page = page
    trace_stopped = False
    try:
        page.goto(BASE_URL, wait_until="domcontentloaded")
        LOGGER.info("Navigated to %s", BASE_URL)
        page.test_steps = test_steps
        yield page
    except Exception:
        LOGGER.warning("Test failed: capturing evidence for %s", request.node.nodeid)
        safe_name = _safe_test_name(request.node.nodeid)
        Path("screenshots").mkdir(exist_ok=True)
        Path("traces").mkdir(exist_ok=True)
        try:
            page.screenshot(path=f"screenshots/{safe_name}_failed.png", full_page=True)
        except Exception:
            LOGGER.exception("Failed to capture screenshot for %s", request.node.nodeid)
        try:
            context.tracing.stop(path=f"traces/{safe_name}.zip")
            trace_stopped = True
        except Exception:
            LOGGER.exception("Failed to save trace for %s", request.node.nodeid)
        raise
    finally:
        if not trace_stopped:
            failed = hasattr(request.node, "rep_call") and request.node.rep_call.failed
            try:
                if failed:
                    safe_name = _safe_test_name(request.node.nodeid)
                    Path("screenshots").mkdir(exist_ok=True)
                    Path("traces").mkdir(exist_ok=True)
                    page.screenshot(path=f"screenshots/{safe_name}_failed.png", full_page=True)
                    context.tracing.stop(path=f"traces/{safe_name}.zip")
                else:
                    context.tracing.stop()
            except Exception:
                LOGGER.exception("Failed to finalize evidence for %s", request.node.nodeid)
        context.close()


@pytest.fixture
def test_steps(request: pytest.FixtureRequest):
    ts = TestSteps()
    try:
        request.node.test_steps = ts
    except Exception:
        pass
    yield ts


@pytest.fixture
def test_meta(request: pytest.FixtureRequest):
    meta = TestCaseMeta()
    try:
        request.node.test_meta = meta
    except Exception:
        pass
    yield meta


def _setup_test_run_logger() -> None:
    global LOG_FILE, LOG_HANDLER
    TEST_RESULTS.clear()
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    run_name = datetime.datetime.now().strftime("test_run_%Y%m%d_%H%M%S")
    LOG_FILE = LOGS_DIR / f"{run_name}.txt"
    LOG_HANDLER = logging.FileHandler(LOG_FILE, encoding="utf-8")
    LOG_HANDLER.setFormatter(QATestFormatter())
    LOG_HANDLER.setLevel(logging.INFO)
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(LOG_HANDLER)
    LOGGER.info("=== pytest session started ===")


def _teardown_test_run_logger() -> None:
    global LOG_HANDLER
    if LOG_HANDLER is None:
        return

    LOGGER.info("=== pytest session finished ===")
    try:
        reports_dir = Path("reports")
        reports_dir.mkdir(parents=True, exist_ok=True)
        base_name = LOG_FILE.stem if LOG_FILE is not None else datetime.datetime.now().strftime("test_run_%Y%m%d_%H%M%S")

        if TEST_RESULTS:
            passed_count = sum(1 for r in TEST_RESULTS if r.get("outcome") == "passed")
            failed_count = sum(1 for r in TEST_RESULTS if r.get("outcome") == "failed")
            error_count = sum(1 for r in TEST_RESULTS if r.get("outcome") == "error")
            skipped_count = sum(1 for r in TEST_RESULTS if r.get("outcome") == "skipped")
            xfailed_count = sum(1 for r in TEST_RESULTS if r.get("outcome") == "xfailed")
            xpassed_count = sum(1 for r in TEST_RESULTS if r.get("outcome") == "xpassed")
            unsuccessful_count = failed_count + error_count + xpassed_count
            total_duration = sum(float(r.get("duration") or 0.0) for r in TEST_RESULTS)
            summary = {
                "total_tests": len(TEST_RESULTS),
                "passed": passed_count,
                "failed": failed_count,
                "errors": error_count,
                "skipped": skipped_count,
                "xfailed": xfailed_count,
                "xpassed": xpassed_count,
                "pass_rate": round((passed_count / len(TEST_RESULTS)) * 100, 2) if TEST_RESULTS else 0.0,
                "fail_rate": round((unsuccessful_count / len(TEST_RESULTS)) * 100, 2) if TEST_RESULTS else 0.0,
                "error_rate": round((error_count / len(TEST_RESULTS)) * 100, 2) if TEST_RESULTS else 0.0,
                "total_duration_seconds": round(total_duration, 2),
                "failed_tests": [
                    r.get("nodeid") for r in TEST_RESULTS if r.get("outcome") in {"failed", "error", "xpassed"}
                ],
                "environment": {
                    "browser": "Chromium",
                    "browser_version": BROWSER_VERSION,
                    "platform": platform.platform(),
                    "python_version": sys.version.split()[0],
                    "base_url": BASE_URL,
                },
            }
            json_path = reports_dir / f"{base_name}_summary.json"
            with json_path.open("w", encoding="utf-8") as jf:
                json.dump({"summary": summary, "results": TEST_RESULTS}, jf, ensure_ascii=False, indent=2)

            failures = [r for r in TEST_RESULTS if r.get("outcome") in {"failed", "error", "xpassed"}]
            if failures:
                txt_path = reports_dir / f"{base_name}_failures.txt"
                with txt_path.open("w", encoding="utf-8") as tf:
                    tf.write("=== TEST FAILURE SUMMARY ===\n")
                    tf.write(f"Total Failed: {len(failures)}\n")
                    tf.write(f"Fail Rate: {summary['fail_rate']}%\n\n")
                    for failure in failures:
                        tf.write(f"TEST: {failure.get('nodeid')}\n")
                        tf.write(f"Outcome: {failure.get('outcome')}\n")
                        meta = failure.get("meta") or {}
                        tf.write(f"Condition: {meta.get('condition') or 'N/A'}\n")
                        tf.write(f"Expected: {meta.get('expected') or 'N/A'}\n")
                        tf.write(f"Actual: {failure.get('actual') or 'N/A'}\n")
                        tf.write("Failure Meta:\n")
                        meta_json = failure.get("failure_metadata") or {}
                        for key, value in meta_json.items():
                            tf.write(f"  - {key}: {value}\n")
                        tf.write("\n---\n\n")
                for failure in failures:
                    save_bug_report(failure, logger=LOGGER, bug_report_dir=BUG_REPORT_DIR, log_file=LOG_FILE)

            LOGGER.info("=== TEST SUMMARY ===")
            LOGGER.info("Total Tests: %s", summary["total_tests"])
            LOGGER.info("Passed: %s", summary["passed"])
            LOGGER.info("Failed: %s", summary["failed"])
            LOGGER.info("Errors: %s", summary["errors"])
            LOGGER.info("Skipped: %s", summary["skipped"])
            LOGGER.info("Pass Rate: %.2f%%", summary["pass_rate"])
            LOGGER.info("Fail Rate: %.2f%%", summary["fail_rate"])
            LOGGER.info("Total Duration: %.2fs", summary["total_duration_seconds"])
            LOGGER.info("Wrote test summary: %s", str(json_path))
    except Exception:
        LOGGER.exception("Failed to write test summary report")
    finally:
        root_logger = logging.getLogger()
        root_logger.removeHandler(LOG_HANDLER)
        LOG_HANDLER.close()
        LOG_HANDLER = None


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item: pytest.Item, call: pytest.CallInfo[object]):
    outcome = yield
    report = outcome.get_result()
    setattr(item, f"rep_{report.when}", report)
    meta = getattr(item, "test_meta", None)
    steps_obj = getattr(item, "test_steps", None)
    steps = steps_obj.steps if steps_obj is not None else []
    meta_payload = {
        "condition": getattr(meta, "condition", "") if meta else "",
        "procedure": getattr(meta, "procedure", []) if meta else [],
        "expected": getattr(meta, "expected", "") if meta else "",
    }
    if not meta_payload["condition"]:
        meta_payload["condition"] = "조건 정보 없음"
    if not meta_payload["expected"]:
        meta_payload["expected"] = _infer_expected_result(item.nodeid)
    if not meta_payload["procedure"]:
        meta_payload["procedure"] = _infer_test_procedure(item.nodeid)

    record = getattr(item, "qa_result_record", None)
    if record is None:
        record = {
            "nodeid": item.nodeid,
            "outcome": "pending",
            "duration": 0.0,
            "phase_outcomes": {},
            "longrepr": "",
            "meta": meta_payload,
            "steps": steps,
            "actual": "",
            "facts": {},
            "failure_metadata": None,
        }
        item.qa_result_record = record
        TEST_RESULTS.append(record)

    record["duration"] += float(getattr(report, "duration", 0.0) or 0.0)
    record["phase_outcomes"][report.when] = report.outcome
    record["meta"] = meta_payload
    record["steps"] = steps

    was_xfail = getattr(report, "wasxfail", None)
    if was_xfail:
        record["outcome"] = "xfailed" if report.skipped else "xpassed"
    elif report.failed:
        record["outcome"] = "failed" if report.when == "call" else "error"
        raw_actual = str(report.longrepr)
        record["longrepr"] = raw_actual
        record["actual"] = raw_actual
        record["facts"] = _extract_failure_facts(item.nodeid, {"longrepr": raw_actual, "meta": meta_payload}, item=item)
        record["failure_metadata"] = _build_failure_metadata(item.nodeid, {"longrepr": raw_actual, "meta": meta_payload}, item=item)
    elif report.skipped and record["outcome"] == "pending":
        record["outcome"] = "skipped"
        record["actual"] = "skipped"
    elif report.when == "call" and record["outcome"] == "pending":
        record["outcome"] = "passed"
        record["actual"] = "passed"


def pytest_configure(config: pytest.Config) -> None:
    _setup_test_run_logger()


def pytest_runtest_setup(item: pytest.Item) -> None:
    log_context = getattr(item, "qa_log", None)
    if log_context is None:
        item.qa_log = TestLogContext(item)
        item.qa_log.start()
    LOGGER.info("=== TEST START: %s ===", item.nodeid)


def pytest_runtest_teardown(item: pytest.Item, nextitem: pytest.Item | None) -> None:
    LOGGER.info("=== TEST END: %s ===", item.nodeid)
    if getattr(item, "qa_log", None) is not None:
        result = "PASSED" if getattr(item, "rep_call", None) is not None and not item.rep_call.failed else "FAILED"
        item.qa_log.end(result)


def pytest_unconfigure(config: pytest.Config) -> None:
    _teardown_test_run_logger()


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption("--headed", action="store_true", help="브라우저 창을 표시합니다.")
    parser.addoption("--slowmo", action="store", default=0, type=int, help="동작 사이 지연(ms)")
