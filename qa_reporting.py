from __future__ import annotations

import datetime
import json
import logging
import os
import re
import urllib.error
import urllib.request
from pathlib import Path

import pytest
from dotenv import load_dotenv

load_dotenv()

LOGGER = logging.getLogger("automation")
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


def _safe_text(value: object, fallback: str = "N/A") -> str:
    if value is None:
        return fallback
    if isinstance(value, str):
        return value.strip() or fallback
    return str(value)


def _extract_url_from_longrepr(longrepr: str) -> str:
    match = re.search(r"Page url='([^']+)'", longrepr)
    if match:
        return match.group(1)
    match = re.search(r'Page url="([^"]+)"', longrepr)
    if match:
        return match.group(1)
    return "N/A"


def _extract_failed_step(nodeid: str, record: dict, item: pytest.Item | None = None) -> str:
    meta = record.get("meta") or {}
    procedure = meta.get("procedure") or []
    if not procedure:
        return "N/A"

    longrepr = str(record.get("longrepr") or "")
    lower = longrepr.lower()

    if item is not None:
        qa_log = getattr(item, "qa_log", None)
        if qa_log is not None:
            last_step = getattr(qa_log, "last_step", "")
            if last_step:
                last_lower = last_step.lower()
                for step in procedure:
                    step_lower = step.lower()
                    if "총액" in step or "total" in step_lower or "주문 총액" in step:
                        if any(keyword in last_lower for keyword in ["총액", "total", "검증", "합계"]):
                            return step
                    if "체크아웃" in step or "checkout" in step_lower:
                        if any(keyword in last_lower for keyword in ["체크아웃", "checkout", "검증", "진행"]):
                            return step
                    if "정보" in step or "입력" in step:
                        if any(keyword in last_lower for keyword in ["정보", "입력", "first name", "last name", "postal"]):
                            return step

    if "summary_total_label" in lower or ("total" in lower and "locator" in lower):
        for step in procedure:
            if "총액" in step or "total" in step.lower() or "결제" in step.lower():
                return step
    if "expected to be disabled" in lower or "to_be_disabled" in lower or ("checkout" in lower and "disabled" in lower):
        for step in procedure:
            if "체크아웃" in step or "checkout" in step.lower():
                return step
    if "first name is required" in lower or "last name is required" in lower or "postal code is required" in lower:
        for step in procedure:
            if "고객 정보를 입력한다." in step or "고객 정보" in step or "정보" in step:
                return step
    return procedure[-1]


def _extract_failure_facts(nodeid: str, record: dict, item: pytest.Item | None = None) -> dict:
    longrepr = str(record.get("longrepr") or "")
    lower = longrepr.lower()

    actual_result = _safe_text(_summarize_actual_result(record), "N/A")

    current_url = _extract_url_from_longrepr(longrepr)
    if current_url == "N/A" and item is not None and getattr(item, "page", None) is not None:
        try:
            current_url = item.page.url
        except Exception:
            current_url = "N/A"

    failed_step = _extract_failed_step(nodeid, record, item=item)

    location = "N/A"
    if ".summary_total_label" in longrepr:
        location = ".summary_total_label"
    elif 'get_by_role("button", name="Checkout")' in longrepr:
        location = 'get_by_role("button", name="Checkout")'
    elif "locator" in lower:
        match = re.search(r"waiting for locator\((.+?)\)", longrepr, flags=re.IGNORECASE | re.DOTALL)
        if match:
            location = match.group(1).strip()

    failure_type = "Automation Bug"
    if "timeout" in lower and ("locator" in lower or "element" in lower):
        failure_type = "Automation Bug / UI Selector Issue"
    elif "expected to be disabled" in lower or "enabled" in lower:
        failure_type = "Product Bug / Automation Bug"
    elif "required" in lower:
        failure_type = "Product Bug"
    elif "http" in lower or "network" in lower or "connection" in lower:
        failure_type = "Environment Issue"
    elif "data" in lower or "missing" in lower:
        failure_type = "Data Issue"

    raw_log = _extract_key_error_lines(longrepr) or actual_result
    return {
        "test_id": nodeid,
        "actual_result": actual_result,
        "current_url": current_url,
        "failed_step": failed_step,
        "failure_type": failure_type,
        "locator": location,
        "raw_log": raw_log,
        "evidence": raw_log,
    }


def _build_failure_metadata(nodeid: str, record: dict, item: pytest.Item | None = None) -> dict:
    facts = _extract_failure_facts(nodeid, record, item=item)
    longrepr = str(record.get("longrepr") or "")
    lower = longrepr.lower()
    failure_type = facts["failure_type"]
    if failure_type == "Environment Issue":
        classification = "Environment"
        severity = "Medium"
        confidence = "High"
    elif failure_type == "Data Issue":
        classification = "Data"
        severity = "Medium"
        confidence = "Medium"
    elif failure_type.startswith("Automation Bug"):
        classification = "Automation"
        severity = "High" if "timeout" in lower or "locator" in lower else "Medium"
        confidence = "Medium"
    elif failure_type == "Product Bug":
        classification = "Product"
        severity = "Medium"
        confidence = "Medium"
    else:
        classification = "Product / Automation"
        severity = "Medium"
        confidence = "Medium"
    return {
        "test_id": facts["test_id"],
        "failure_type": failure_type,
        "failed_step": facts["failed_step"],
        "current_url": facts["current_url"],
        "locator": facts["locator"],
        "severity": severity,
        "confidence": confidence,
        "classification": classification,
        "evidence": facts["evidence"],
    }


def _summarize_actual_result(record: dict) -> str:
    raw_text = (record.get("actual") or record.get("longrepr") or "실제 결과를 확인할 수 없습니다.")
    text = str(raw_text).replace("\\n", "\n")

    if "Locator expected to be disabled" in text or "expected to be disabled" in text.lower():
        return "Locator expected to be disabled; actual value: enabled"
    if "Locator.inner_text: Timeout 30000ms exceeded" in text or "Timeout 30000ms exceeded" in text:
        return "Locator.inner_text: Timeout 30000ms exceeded"
    if "expected to be disabled" in text.lower() and "enabled" in text.lower():
        return "Locator expected to be disabled; actual value: enabled"

    error_variants = [
        r"AssertionError:\s*(.*)",
        r"TimeoutError:\s*(.*)",
        r"(?:playwright\._impl\._errors\.)?(?:AssertionError|TimeoutError|ElementNotFound|NoSuchElementException|WebDriverException):\s*(.*)",
        r"Locator\.inner_text:\s*Timeout\s*\d+ms\s*exceeded\.?",
        r"Locator expected to be disabled.*?actual value: enabled",
    ]
    for pattern in error_variants:
        match = re.search(pattern, text, flags=re.IGNORECASE | re.DOTALL)
        if match:
            detail = match.group(1) if match.lastindex and match.group(1) else match.group(0)
            detail = str(detail).strip()
            detail = detail.replace("Call log:", "").replace("\n", " ")
            detail = re.sub(r"\s+", " ", detail).strip()
            if detail:
                return detail

    for line in text.splitlines():
        cleaned = _normalize_error_line(line)
        if _is_noise_line(cleaned):
            continue
        lowered = cleaned.lower()
        if lowered.startswith("page =") or lowered.startswith("test_meta =") or lowered.startswith("qa_log ="):
            continue
        if lowered.startswith("e "):
            cleaned = cleaned[2:].strip()
        if "rewrite_error" in lowered or "apiName" in lowered:
            continue
        if "assertionerror" in lowered or "timeouterror" in lowered or "locator" in lowered or "expected to be disabled" in lowered:
            return cleaned
        if cleaned.startswith(("expected=", "actual=", "assert ")):
            continue
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
    failure_metadata: dict | None = None,
    facts: dict | None = None,
) -> str:
    safe_procedure = procedure or _infer_test_procedure(test_name)
    safe_expected = expected or _infer_expected_result(test_name)
    metadata = failure_metadata or {}
    fact_data = facts or {
        "actual_result": actual or "실제 결과를 확인할 수 없습니다.",
        "current_url": metadata.get("current_url", "N/A"),
        "failed_step": metadata.get("failed_step", "N/A"),
        "failure_type": metadata.get("failure_type", "N/A"),
        "locator": metadata.get("locator", "N/A"),
        "raw_log": error_log or "로그 없음",
    }
    safe_actual = fact_data.get("actual_result") or (actual or "실제 결과를 확인할 수 없습니다.").strip()
    safe_error_log = (error_log or fact_data.get("raw_log") or safe_actual).strip()
    full_error_log = str(safe_error_log).replace("\\n", "\n")
    proc_block = "\n".join(f"{idx}. {step}" for idx, step in enumerate(safe_procedure, start=1))
    scenario_name = condition.strip() or "테스트 시나리오 확인 불가"

    confirmed_facts = [
        f"- 테스트명: {test_name}",
        f"- 발생 일자: {timestamp}",
        f"- 조건: {condition or '조건 정보 없음'}",
        f"- 실제 결과: {safe_actual}",
        f"- 현재 URL: {fact_data.get('current_url') or 'N/A'}",
        f"- 실패 단계: {fact_data.get('failed_step') or 'N/A'}",
        f"- 실패 유형: {fact_data.get('failure_type') or 'N/A'}",
        f"- 대상 Locator: {fact_data.get('locator') or 'N/A'}",
    ]
    ai_summary = [
        "- 로그에서 확인된 사실만을 기준으로 정리하면, 실패는 위의 실제 결과와 현재 화면/단계 정보와 일치합니다.",
        "- 원인은 로그 상의 실패 메시지와 화면 상태를 종합해 추정할 수 있지만, 최종 결론은 추가 검증이 필요합니다.",
        "- 추가 확인 포인트: 현재 URL, Locator, 실패 단계, 그리고 실제 화면 상태를 재검증해야 합니다.",
    ]

    return f"""# {test_name} 실패 보고서

## 1. 요약
- 발생 일자: {timestamp}
- 테스트명: {test_name}
- 조건: {condition or '조건 정보 없음'}
- 시나리오: {scenario_name}
- 분류: {fact_data.get('failure_type') or metadata.get('failure_type') or '분류 미확인'}
- 심각도: {metadata.get('severity') or 'Medium'}

## 2. 확인된 사실
{chr(10).join(confirmed_facts)}

## 3. 재현 절차
{proc_block}

## 4. 기대 결과
{safe_expected}

## 5. 실제 결과
{safe_actual}

## 6. AI 요약
{chr(10).join(ai_summary)}

## 7. 실패 로그
```text
{_compact_log_block(full_error_log)}
```

## 8. 메타데이터
- Failure Type: {fact_data.get('failure_type') or metadata.get('failure_type') or 'N/A'}
- Failed Step: {fact_data.get('failed_step') or metadata.get('failed_step') or 'N/A'}
- Current URL: {fact_data.get('current_url') or metadata.get('current_url') or 'N/A'}
- Locator: {fact_data.get('locator') or metadata.get('locator') or 'N/A'}
- Severity: {metadata.get('severity') or 'N/A'}
- Confidence: {metadata.get('confidence') or 'N/A'}
- Classification: {metadata.get('classification') or 'N/A'}

## 9. 증거
- 스크린샷: {screenshot_path or '없음'}
- 로그: {log_path or '없음'}
- Trace: {trace_path or '없음'}
"""


def _generate_bug_report_with_gemini(payload: dict) -> str:
    gemini_api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GENINI_API_KEY")
    if not gemini_api_key:
        return ""

    prompt = """당신은 QA 자동화 팀의 버그 리포트 작성 도우미입니다.
다음 테스트 실패 정보를 기반으로 한글 버그 리포트를 작성해주세요.
반드시 아래 항목을 포함하세요:
- 발생 일자
- 조건
- 절차
- 예상 결과
- 실제 결과
- AI 로그 해석

중요 규칙:
- 실제 결과는 내부 구현 코드 문자열을 그대로 적지 마세요.
- `raise rewrite_error(error, f"{{parsed_st['apiName']}}: {{error}}") from None` 같은 내부 스택프레임, 에러 래퍼, 라이브러리 구현 문구는 절대 그대로 적지 마세요.
- 로그에 보이는 실패 원인만 근거로 사용하여, 사용자 이해가 가능한 한글 문장으로 요약하세요.
- 실제 결과에는 원본 오류 메시지를 짧게 유지하세요.
- 실제 결과 바로 다음에 `## 6. AI 로그 해석` 제목을 만들고, 원본 오류가 의미하는 상황을 반드시 한국어 1~3문장으로 해석하세요.
- AI 로그 해석은 반드시 "로그상 ... 때문에 ...한 것으로 보입니다" 형태로 시작하세요.
- 예시: "로그상 총액 영역(.summary_total_label)을 찾지 못해 30초 대기 후 타임아웃이 발생한 것으로 보입니다. 현재 URL과 실패 단계를 보면 총액이 표시되는 화면으로 이동했는지 확인이 필요합니다."
- `expected=...`, `actual=...`, `assert ...` 같은 pytest 내부 표현식은 절대 적지 마세요.

출력 형식:
`## 1. 요약`부터 번호가 붙은 Markdown 제목을 사용하세요. 반드시 `## 5. 실제 결과` 다음에 `## 6. AI 로그 해석`을 배치하고, 이후 실패 로그와 증거를 배치하세요.

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
        f"{gemini_api_key}"
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

    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8", errors="replace")

        LOGGER.error(
            "Gemini API HTTP error: status=%s, reason=%s, body=%s",
            e.code,
            e.reason,
            error_body,
        )

    except urllib.error.URLError as e:
        LOGGER.exception("Gemini network error: %s", e)

    except TimeoutError:
        LOGGER.exception("Gemini API timeout")

    except Exception:
        LOGGER.exception("Unexpected Gemini bug report generation error")

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


def _build_bug_report_payload(record: dict, item: pytest.Item | None = None) -> dict:
    nodeid = record.get("nodeid") or "unknown_test"
    meta = record.get("meta") or {}
    safe_name = _safe_test_name(nodeid)
    procedure = _normalize_procedure(nodeid, record)
    condition = meta.get("condition") or "조건 정보 없음"
    expected = meta.get("expected") or _infer_expected_result(nodeid)
    actual = _summarize_actual_result(record)
    error_log = record.get("longrepr") or actual
    failure_metadata = _build_failure_metadata(nodeid, record, item=item)
    facts = _extract_failure_facts(nodeid, record, item=item)

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
        "log_path": "",
        "failure_metadata": failure_metadata,
        "facts": facts,
    }


def save_bug_report(record: dict, item: pytest.Item | None = None, *, logger: logging.Logger | None = None, bug_report_dir: Path | None = None, log_file: Path | None = None) -> str | None:
    logger = logger or LOGGER
    bug_report_dir = bug_report_dir or Path("reports") / "bug_reports"
    bug_report_dir.mkdir(parents=True, exist_ok=True)

    payload = _build_bug_report_payload(record, item=item)
    payload["log_path"] = str(log_file) if log_file is not None else ""

    local_report = build_bug_report_content(
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
        failure_metadata=payload.get("failure_metadata"),
        facts=payload.get("facts"),
    )

    try:
        generated_report = _generate_bug_report_with_gemini(payload)
    except Exception:
        logger.exception("Gemini bug report generation crashed; falling back to local report")
        generated_report = ""

    safe_name = _safe_test_name(payload["test_name"])
    safe_name = re.sub(r"[^A-Za-z0-9_\-]+", "_", safe_name).strip("_")
    file_name = f"{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}_{safe_name}_bug_report.md"
    target_path = bug_report_dir / file_name
    target_path.write_text(generated_report or local_report, encoding="utf-8")
    logger.info("Bug report saved: %s", target_path)
    return str(target_path)
