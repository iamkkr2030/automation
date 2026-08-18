from __future__ import annotations

import datetime
import json
import logging
import os
import re
import shutil
import urllib.error
import urllib.request
from pathlib import Path

import pytest

from config.site_config import DEFAULT_CONFIG

PASS_LEVEL = 25
FAIL_LEVEL = 35

logging.addLevelName(PASS_LEVEL, "PASS")
logging.addLevelName(FAIL_LEVEL, "FAIL")


class QATestFormatter(logging.Formatter):
    """QA-oriented formatter: [TIME] [LEVEL] [TEST_ID] MESSAGE."""

    def format(self, record: logging.LogRecord) -> str:
        timestamp = self.formatTime(record, self.datefmt or "%Y-%m-%d %H:%M:%S")
        test_id = getattr(record, "test_id", "SYSTEM")
        return f"[{timestamp}] [{record.levelname}] [{test_id}] {record.getMessage()}"

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover
    def load_dotenv() -> bool:
        return False

load_dotenv()
from playwright.sync_api import Browser, Page, sync_playwright

BASE_URL = os.getenv("BASE_URL", DEFAULT_CONFIG.base_url)
LOGS_DIR = Path("logs")
LOG_FILE: Path | None = None
LOG_HANDLER: logging.Handler | None = None
LOGGER = logging.getLogger("automation")
TEST_RESULTS: list[dict] = []
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("GENINI_API_KEY")
REPORTS_DIR = Path("reports")
BUG_REPORT_DIR = REPORTS_DIR / "bug_reports"
ERROR_TOKENS = (
    "AssertionError",
    "TimeoutError",
    "ElementNotFound",
    "NoSuchElementException",
    "WebDriverException",
    "HTTPError",
    "Exception",
    "Error",
)


def _normalize_error_line(line: str) -> str:
    cleaned = line.strip()
    if cleaned.startswith("E "):
        cleaned = cleaned[2:].strip()
    return cleaned


def _is_noise_line(line: str) -> bool:
    cleaned = line.strip()
    if not cleaned:
        return True
    if cleaned.startswith(("page =", "test_meta =", "qa_log =", "> ")):
        return True
    return "rewrite_error" in cleaned or "apiName" in cleaned


def _safe_test_name(nodeid: str) -> str:
    return nodeid.replace("::", "_").replace("/", "_").replace("\\", "_")


def _infer_test_procedure(nodeid: str) -> list[str]:
    lower = nodeid.lower()
    if "login" in lower:
        return [
            "로그인 페이지에 접속한다.",
            "사용자 이름과 비밀번호를 입력한다.",
            "로그인 버튼을 클릭한다.",
            "로그인 결과를 확인한다.",
        ]
    if "product" in lower:
        return [
            "상품 목록 페이지에 접속한다.",
            "상품 목록과 가격을 확인한다.",
            "정렬 기능을 사용한다.",
            "상품 상세 페이지를 확인한다.",
        ]
    if "checkout" in lower:
        return [
            "상품을 장바구니에 담는다.",
            "장바구니에서 체크아웃을 진행한다.",
            "고객 정보를 입력한다.",
            "결제 정보를 검증하고 주문을 완료한다.",
        ]
    return ["테스트 절차를 확인할 수 없습니다."]


def _infer_expected_result(nodeid: str) -> str:
    lower = nodeid.lower()
    if "login" in lower:
        return "로그인 성공 시 상품 목록 페이지가 표시되어야 하며, 실패 시 적절한 에러 메시지가 노출되어야 한다."
    if "product" in lower:
        return "상품 목록, 정렬, 상세 페이지 동작이 정상적으로 수행되어야 한다."
    if "checkout" in lower:
        return "체크아웃 입력 검증과 주문 완료 과정이 정상적으로 동작해야 한다."
    return "테스트는 정상적으로 수행되며, 의도된 동작 결과가 기대값과 일치해야 한다."


def _extract_key_error_lines(raw_text: str) -> str:
    text = str(raw_text or "").replace("\\n", "\n")
    if not text:
        return ""

    lines: list[str] = []
    seen: set[str] = set()

    for line in text.splitlines():
        cleaned = _normalize_error_line(line)
        if _is_noise_line(cleaned):
            continue
        if any(token in cleaned for token in ERROR_TOKENS):
            if cleaned not in seen:
                seen.add(cleaned)
                lines.append(cleaned)
        elif "locator" in cleaned.lower() and ("timeout" in cleaned.lower() or "not found" in cleaned.lower()):
            if cleaned not in seen:
                seen.add(cleaned)
                lines.append(cleaned)

    if not lines:
        return ""
    return "\n".join(lines[:4])


def _summarize_actual_result(record: dict) -> str:
    raw_text = (record.get("actual") or record.get("longrepr") or "실제 결과를 확인할 수 없습니다.")
    text = str(raw_text).replace("\\n", "\n")

    error_patterns = [
        r"(AssertionError|TimeoutError|ElementNotFound|NoSuchElementException|WebDriverException|Exception|Error):\s*(.*)",
        r"E\s+(AssertionError|TimeoutError|ElementNotFound|NoSuchElementException|WebDriverException|Exception|Error):\s*(.*)",
        r"playwright\._impl\._errors\.(AssertionError|TimeoutError|ElementNotFound|NoSuchElementException|WebDriverException|Exception|Error):\s*(.*)",
    ]
    for pattern in error_patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            detail = (match.group(2) or match.group(0)).strip()
            if detail:
                clean_detail = detail.replace("Locator.inner_text: ", "").replace("Call log:", "")
                return clean_detail.strip()

    for line in text.splitlines():
        cleaned = _normalize_error_line(line)
        if _is_noise_line(cleaned):
            continue
        if cleaned.startswith(("expected=", "actual=", "assert ")):
            continue
        if any(token in cleaned for token in ERROR_TOKENS[:5]):
            return cleaned
        if cleaned:
            return cleaned

    short = text.strip().splitlines()
    if short:
        summary = short[0].strip()
        if summary.startswith(("expected=", "actual=")):
            return "실제 결과를 확인할 수 없습니다."
        if len(summary) > 220:
            return summary[:220].rstrip() + "..."
        return summary
    return "실제 결과를 확인할 수 없습니다."


def _compact_log_block(raw_text: str, *, max_lines: int = 18, max_chars: int = 3500) -> str:
    text = str(raw_text or "").replace("\\n", "\n").strip()
    if not text:
        return "로그 없음"

    compact_mode = os.getenv("BUG_REPORT_COMPACT_LOGS", "true").lower() in {"1", "true", "yes", "y"}
    if not compact_mode:
        return text

    if len(text) <= max_chars and len(text.splitlines()) <= max_lines:
        return text

    lines = text.splitlines()
    if len(lines) <= max_lines:
        return text[:max_chars].rstrip() + "\n... (로그가 일부 생략되었습니다.)"

    keep_head = max(4, max_lines // 2)
    keep_tail = max_lines - keep_head
    trimmed = lines[:keep_head] + ["... (로그가 일부 생략되었습니다.) ..."] + lines[-keep_tail:]
    return "\n".join(trimmed)


def _describe_textual_actual_result(raw_text: str) -> str:
    text = str(raw_text or "").replace("\\n", "\n")
    if not text:
        return "실제 결과는 기대한 텍스트가 화면에 나타나지 않는 상태로 확인되었습니다."

    lower = text.lower()

    if "waiting for locator" in lower and ".summary_total_label" in lower:
        return "로그를 기준으로 보면 체크아웃 페이지에서 총액 영역(.summary_total_label)이 나타나지 않아 주문 총액을 읽는 단계에서 타임아웃이 발생한 것으로 보입니다. 즉, 다음 단계의 화면 전환 또는 총액 렌더링이 완료되지 않아 실패한 상태입니다."
    if "first name is required" in lower:
        return "로그를 기준으로 보면 이름 입력이 비어 있어 체크아웃 유효성 검증이 실패한 것으로 보입니다. 필수 정보 누락으로 다음 단계 이동이 막힌 상태입니다."
    if "timeout" in lower and "locator" in lower:
        return "로그를 기준으로 보면 특정 요소를 찾지 못해 대기 시간이 초과된 것으로 보입니다. 페이지 상태가 기대와 달라서 다음 동작을 수행하지 못한 상태입니다."
    if "assertionerror" in lower or "assert " in lower:
        return "로그를 기준으로 보면 기대 값과 실제 값이 일치하지 않아 검증 단계가 실패한 것으로 보입니다. 결과값이 기대 조건과 다르게 도출된 상태입니다."

    candidates: list[str] = []
    for line in text.splitlines():
        cleaned = line.strip()
        if not cleaned or cleaned.startswith("page =") or cleaned.startswith("test_meta =") or cleaned.startswith("qa_log =") or cleaned.startswith("> "):
            continue
        if cleaned.startswith("E "):
            cleaned = cleaned[2:].strip()
        if cleaned.startswith("expected=") or cleaned.startswith("actual=") or cleaned.startswith("assert "):
            continue
        if "rewrite_error" in cleaned or "apiName" in cleaned:
            continue
        if cleaned and len(cleaned) < 220:
            candidates.append(cleaned)

    if candidates:
        first = candidates[0]
        if first.startswith("except Exception as error:"):
            first = "오류가 발생한 상태"
        return f"로그를 기준으로 보면 '{first}'가 발생하면서 실패가 확인되었습니다. 이로 인해 기대한 화면 동작을 완료하지 못한 상태로 보입니다."

    return "로그를 기준으로 보면 기대한 화면 상태가 도달하지 못했고, 검증 단계에서 실패가 발생한 것으로 보입니다."


def build_bug_report_content(
    *,
    test_name: str,
    timestamp: str,
    condition: str,
    procedure: list[str],
    expected: str,
    actual: str,
    error_log: str,
    screenshot_path: str = "",
    log_path: str = "",
    trace_path: str = "",
) -> str:
    safe_procedure = procedure or _infer_test_procedure(test_name)
    safe_expected = expected or _infer_expected_result(test_name)
    inferred_failure = _describe_textual_actual_result(error_log or actual or "")
    safe_actual = inferred_failure or (actual or "실제 결과를 확인할 수 없습니다.").strip()
    safe_error_log = (error_log or safe_actual).strip()
    full_error_log = str(safe_error_log).replace("\\n", "\n")
    proc_block = "\n".join(f"{idx}. {step}" for idx, step in enumerate(safe_procedure, start=1))

    scenario_name = condition.strip() or "테스트 시나리오 확인 불가"
    actual_result_lines = [safe_actual]
    actual_result_lines.append("")
    actual_result_lines.append("원인 분석:")
    actual_result_lines.append(inferred_failure or safe_actual)

    return f"""# {test_name} 실패 보고서

## 1. 요약
- 발생 일자: {timestamp}
- 테스트명: {test_name}
- 조건: {condition or '조건 정보 없음'}
- 시나리오: {scenario_name}

## 2. 재현 절차
{proc_block}

## 3. 기대 결과
{safe_expected}

## 4. 실제 결과
{chr(10).join(actual_result_lines)}

## 5. 실패 로그
```text
{_compact_log_block(full_error_log)}
```

## 6. 증거
- 스크린샷: {screenshot_path or '없음'}
- 로그: {log_path or '없음'}
- Trace: {trace_path or '없음'}
"""


def _generate_bug_report_with_gemini(payload: dict) -> str:
    if not GEMINI_API_KEY:
        return ""

    prompt = """당신은 QA 자동화 팀의 버그 리포트 작성 도우미입니다.
다음 테스트 실패 정보를 기반으로 한글 버그 리포트를 작성해주세요.
반드시 아래 항목을 포함하세요:
- 발생 일자
- 조건
- 절차
- 예상 결과
- 실제 결과

중요 규칙:
- 실제 결과는 내부 구현 코드 문자열을 그대로 적지 마세요.
- `raise rewrite_error(error, f"{{parsed_st['apiName']}}: {{error}}") from None` 같은 내부 스택프레임, 에러 래퍼, 라이브러리 구현 문구는 절대 그대로 적지 마세요.
- 로그에 보이는 실패 원인만 근거로 사용하여, 사용자 이해가 가능한 한글 문장으로 요약하세요.
- 실제 결과는 반드시 "로그상 ... 때문에 ...한 것으로 보입니다" 형태로 설명하세요.
- 예시: "로그상 총액 영역(.summary_total_label)을 찾지 못해 30초 대기 후 타임아웃이 발생한 것으로 보입니다." 또는 "로그상 이름 입력값이 비어 있어 유효성 검사에서 실패한 것으로 보입니다."
- `expected=...`, `actual=...`, `assert ...` 같은 pytest 내부 표현식은 절대 적지 마세요.

출력 형식:
1. 제목
2. 발생 일자
3. 테스트명
4. 조건
5. 절차
6. 예상 결과
7. 실제 결과
8. 실패 로그
9. 증거

한글로 작성하고, 로그를 근거로 한 추정과 원인 설명을 깔끔하게 구성해주세요.

테스트 정보:
- 테스트명: {test_name}
- 발생 일자: {timestamp}
- 조건: {condition}
- 절차: {procedure}
- 예상 결과: {expected}
- 실제 결과: {actual}
- 실패 로그: {error_log}
- 스크린샷 경로: {screenshot_path}
- 로그 경로: {log_path}
- trace 경로: {trace_path}
""".format(
        test_name=payload["test_name"],
        timestamp=payload["timestamp"],
        condition=payload["condition"],
        procedure=payload["procedure"],
        expected=payload["expected"],
        actual=payload["actual"],
        error_log=payload["error_log"],
        screenshot_path=payload["screenshot_path"],
        log_path=payload["log_path"],
        trace_path=payload["trace_path"],
    )

    url = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        "gemini-2.5-flash:generateContent?key="
        f"{GEMINI_API_KEY}"
    )
    body = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.2},
    }

    try:
        req = urllib.request.Request(
            url,
            data=json.dumps(body).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=30) as response:
            data = json.loads(response.read().decode("utf-8"))
        candidate = data.get("candidates", [{}])[0]
        content = candidate.get("content", {}).get("parts", [])
        parts_text = "".join(part.get("text", "") for part in content)
        if parts_text:
            return parts_text.strip()
    except (urllib.error.URLError, ValueError, KeyError, TimeoutError):
        LOGGER.exception("Gemini bug report generation failed")
    return ""


def _normalize_procedure(nodeid: str, record: dict) -> list[str]:
    meta = record.get("meta") or {}
    procedure = meta.get("procedure") or []
    if not procedure:
        procedure = [
            step.get("description", "") for step in (record.get("steps") or []) if step.get("description")
        ]
    if not procedure:
        procedure = _infer_test_procedure(nodeid)
    return [step for step in procedure if step]


def _build_bug_report_payload(record: dict) -> dict:
    nodeid = record.get("nodeid") or "unknown_test"
    meta = record.get("meta") or {}
    safe_name = nodeid.replace("::", "_").replace("/", "_").replace("\\", "_")
    procedure = _normalize_procedure(nodeid, record)
    condition = meta.get("condition") or "조건 정보 없음"
    expected = meta.get("expected") or _infer_expected_result(nodeid)
    actual = _summarize_actual_result(record)
    error_log = record.get("longrepr") or actual

    return {
        "test_name": nodeid,
        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "condition": condition,
        "procedure": procedure,
        "expected": expected,
        "actual": actual,
        "error_log": error_log,
        "screenshot_path": f"screenshots/{safe_name}_failed.png",
        "trace_path": f"traces/{safe_name}.zip",
        "log_path": str(LOG_FILE) if LOG_FILE is not None else "",
    }


def save_bug_report(record: dict) -> str | None:
    payload = _build_bug_report_payload(record)
    local_report = build_bug_report_content(**payload)
    try:
        generated_report = _generate_bug_report_with_gemini(payload)
    except Exception:
        LOGGER.exception("Gemini bug report generation crashed; falling back to local report")
        generated_report = ""

    BUG_REPORT_DIR.mkdir(parents=True, exist_ok=True)
    safe_name = _safe_test_name(payload["test_name"])
    safe_name = re.sub(r"[^A-Za-z0-9_\-]+", "_", safe_name).strip("_")
    file_name = f"{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}_{safe_name}_bug_report.md"
    target_path = BUG_REPORT_DIR / file_name
    target_path.write_text(generated_report or local_report, encoding="utf-8")
    LOGGER.info("Bug report saved: %s", target_path)
    return str(target_path)


def _setup_test_run_logger(config: pytest.Config) -> None:
    global LOG_FILE, LOG_HANDLER
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
    if LOG_HANDLER is not None:
        LOGGER.info("=== pytest session finished ===")
        # Write a simple JSON summary and a human-readable failures file
        try:
            reports_dir = Path("reports")
            reports_dir.mkdir(parents=True, exist_ok=True)
            if LOG_FILE is not None:
                base_name = LOG_FILE.stem
            else:
                base_name = datetime.datetime.now().strftime("test_run_%Y%m%d_%H%M%S")

            if TEST_RESULTS:
                json_path = reports_dir / f"{base_name}_summary.json"
                with json_path.open("w", encoding="utf-8") as jf:
                    json.dump(TEST_RESULTS, jf, ensure_ascii=False, indent=2)
                failures = [r for r in TEST_RESULTS if r.get("outcome") == "failed"]
                if failures:
                    txt_path = reports_dir / f"{base_name}_failures.txt"
                    with txt_path.open("w", encoding="utf-8") as tf:
                        for f in failures:
                            tf.write(f"TEST: {f.get('nodeid')}\n")
                            meta = f.get("meta") or {}
                            if meta:
                                tf.write("Test Condition:\n")
                                tf.write(meta.get("condition", "") + "\n\n")
                                tf.write("Expected Result:\n")
                                tf.write(meta.get("expected", "") + "\n\n")
                                proc = meta.get("procedure") or []
                                if proc:
                                    tf.write("Test Procedure:\n")
                                    for i, p in enumerate(proc, start=1):
                                        tf.write(f"  {i}. {p}\n")
                                    tf.write("\n")

                            steps = f.get("steps") or []
                            if steps:
                                tf.write("Steps Taken:\n")
                                for s in steps:
                                    tf.write(f"  - {s.get('time')} {s.get('description')} (expected: {s.get('expected')})\n")
                                tf.write("\n")

                            tf.write("Actual Result:\n")
                            tf.write((f.get("actual") or "") + "\n")
                            tf.write("Long Repr:\n")
                            tf.write((f.get('longrepr') or '') + "\n")
                            tf.write("\n---\n\n")
                    LOGGER.info("Wrote failure report: %s", str(txt_path))

                    for failure in failures:
                        save_bug_report(failure)

                LOGGER.info("Wrote test summary: %s", str(json_path))
        except Exception:
            LOGGER.exception("Failed to write test summary report")

        root_logger = logging.getLogger()
        root_logger.removeHandler(LOG_HANDLER)
        LOG_HANDLER.close()
        LOG_HANDLER = None


def pytest_configure(config: pytest.Config) -> None:
    _setup_test_run_logger(config)


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
    log_context = TestLogContext(request.node)
    request.node.qa_log = log_context
    log_context.start()
    yield log_context
    result = "PASSED" if not request.node.rep_call.failed else "FAILED"
    log_context.end(result)


@pytest.fixture(scope="session")
def browser(request: pytest.FixtureRequest) -> Browser:
    LOGGER.info("Launching Playwright browser")
    with sync_playwright() as playwright:
        yield playwright.chromium.launch(
            headless=not request.config.getoption("--headed"),
            slow_mo=request.config.getoption("--slowmo"),
        )


@pytest.fixture
def page(browser: Browser, request: pytest.FixtureRequest, test_steps: TestSteps) -> Page:
    LOGGER.info("Creating browser context and opening page")
    context = browser.new_context(viewport={"width": 1440, "height": 900})
    context.tracing.start(screenshots=True, snapshots=True, sources=True)
    page = context.new_page()
    page.goto(BASE_URL, wait_until="domcontentloaded")
    LOGGER.info("Navigated to %s", BASE_URL)
    # attach test steps collector to the Playwright page for convenience
    try:
        page.test_steps = test_steps
    except Exception:
        pass
    yield page

    failed = hasattr(request.node, "rep_call") and request.node.rep_call.failed
    if failed:
        LOGGER.warning("Test failed: capturing screenshot and trace for %s", request.node.nodeid)
        safe_name = _safe_test_name(request.node.nodeid)
        Path("screenshots").mkdir(exist_ok=True)
        page.screenshot(path=f"screenshots/{safe_name}_failed.png", full_page=True)
        Path("traces").mkdir(exist_ok=True)
        context.tracing.stop(path=f"traces/{safe_name}.zip")
    else:
        LOGGER.info("Test passed: stopping tracing")
        context.tracing.stop()
    context.close()


@pytest.fixture
def test_steps(request: pytest.FixtureRequest):
    """Per-test collector for human-readable step records."""
    ts = TestSteps()
    try:
        request.node.test_steps = ts
    except Exception:
        pass
    yield ts


@pytest.fixture
def test_meta(request: pytest.FixtureRequest):
    """Per-test meta: condition, procedure, expected result."""
    meta = TestCaseMeta()
    try:
        request.node.test_meta = meta
    except Exception:
        pass
    yield meta


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item: pytest.Item, call: pytest.CallInfo[object]):
    outcome = yield
    report = outcome.get_result()
    setattr(item, f"rep_{report.when}", report)
    # Collect call-phase results for a session-level summary report
    if report.when == "call":
        meta = getattr(item, "test_meta", None)
        steps_obj = getattr(item, "test_steps", None)
        steps = steps_obj.steps if steps_obj is not None else []
        record = {
            "nodeid": item.nodeid,
            "outcome": report.outcome,
            "duration": getattr(report, "duration", None),
            "longrepr": str(report.longrepr) if report.failed else "",
            "meta": {
                "condition": getattr(meta, "condition", "") if meta else "",
                "procedure": getattr(meta, "procedure", []) if meta else [],
                "expected": getattr(meta, "expected", "") if meta else "",
            },
            "steps": steps,
            "actual": str(report.longrepr) if report.failed else "passed",
        }
        TEST_RESULTS.append(record)
