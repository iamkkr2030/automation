# SauceDemo Playwright QA Automation

이 프로젝트는 SauceDemo 데모 쇼핑몰을 대상으로 한 E2E 자동화 테스트 프로젝트입니다.

핵심 목적은 실제 쇼핑몰 사용자 흐름을 자동으로 검증하고, 실패 시 재현 가능한 증거를 남기는 것입니다. 테스트는 단순한 클릭 검증이 아니라, 실제 사용자 여정을 중심으로 동작을 확인하도록 설계되었습니다.

---

## 1. 프로젝트 개요

이 프로젝트는 SauceDemo의 핵심 사용자 경로를 검증하는 자동화 스위트를 구성합니다. 주요 대상은 다음과 같습니다.

- 로그인
- 상품 목록 조회
- 정렬 기능 확인
- 상품 상세 페이지 이동
- 장바구니 추가/삭제
- Continue Shopping 이동
- 체크아웃 정보 입력
- 총액 검증
- 주문 완료 확인
- 로그아웃

실제 결제는 수행하지 않고, 쇼핑몰의 핵심 사용자 여정을 자동화 테스트로 검증합니다. 이 구조는 웹 UI 동작 검증뿐 아니라, 상태 전이와 예외 상황까지 함께 확인하는 데 적합합니다.

---

## 2. 기술 스택

- Python 3
- pytest
- Playwright
- Page Object Model (POM)
- JSON/HTML 리포트 생성
- 브라우저 자동화 및 실패 리포트 보존
- 테스트 로그 및 스크린샷 기반 재현 지원

---

## 3. 프로젝트 구조

```text
project/
├─ conftest.py
├─ pytest.ini
├─ requirements.txt
├─ README.md
├─ data/
│  ├─ checkout_data.py
│  └─ users.py
├─ pages/
│  ├─ cart_page.py
│  ├─ checkout_page.py
│  ├─ login_page.py
│  └─ products_page.py
├─ tests/
│  ├─ test_login.py
│  ├─ test_products.py
│  ├─ test_cart.py
│  └─ test_checkout.py
├─ logs/
├─ screenshots/
├─ traces/
├─ reports/
│  ├─ bug_reports/
│  ├─ *_summary.json
│  └─ *_failures.txt
└─ .env
```

주요 파일 역할:

- `conftest.py`: 공통 fixture, 브라우저 설정, 로그, 리포트 생성, 실패 스크린샷 및 trace 저장
- `data/users.py`: 테스트 계정 데이터
- `data/checkout_data.py`: 고객 정보 데이터
- `pages/*.py`: 페이지 오브젝트 모델
- `tests/*.py`: 실제 사용자 시나리오 기반 테스트
- `reports/`: 테스트 실행 결과와 버그 리포트 저장 위치
- `screenshots/`: 실패 시 캡처 이미지 저장 위치
- `traces/`: Playwright trace 저장 위치

---

## 4. 테스트 계정

기본 계정은 다음과 같습니다.

```python
STANDARD_USER = {"username": "standard_user", "password": "secret_sauce"}
LOCKED_OUT_USER = {"username": "locked_out_user", "password": "secret_sauce"}
```

기본 비밀번호는 `secret_sauce` 입니다. 로그인 화면에서 사용자 입력값이 올바른지, 에러 메시지가 정상적으로 노출되는지, 잠금 계정 처리가 제대로 되는지를 검증합니다.

---

## 5. 실행 방법

### 의존성 설치

```bash
pip install -r requirements.txt
playwright install chromium
```

Playwright 패키지와 브라우저 실행 파일은 별도로 설치해야 합니다. CI에서는 Chromium과 운영체제 의존성을 자동으로 설치합니다.

### 전체 테스트 실행

```bash
pytest -q
```

### 특정 파일 실행

```bash
pytest tests/test_login.py -q
pytest tests/test_cart.py -q
pytest tests/test_products.py -q
pytest tests/test_checkout.py -q
```

### 브라우저 헤드 모드 실행

```bash
pytest --headed -q
```

### 느린 동작으로 실행

```bash
pytest --slowmo 200 -q
```

### 보고서와 로그와 함께 실행

기본 설정에서 pytest는 테스트 실행 중 로그를 남기고, 실패 시 스크린샷과 trace를 저장합니다. 팀에서 디버깅하거나 QA 리뷰를 할 때 이 리포트가 중요한 근거 자료가 됩니다.

---

## 6. 상세 워크플로우

### 1) pytest 실행 시작

테스트가 실행되면 `conftest.py`가 먼저 동작합니다.

- 브라우저를 초기화하고 테스트 환경을 준비한다.
- 테스트별 로그 컨텍스트를 생성한다.
- 각 테스트에 필요한 페이지 객체를 연결한다.
- 실패 시 스크린샷과 trace를 저장한다.
- 결과를 JSON/텍스트 형태로 정리한다.

이 단계는 테스트 코드 본문보다 앞서 실행되므로, 공통 설정을 한 번에 관리하는 구조가 매우 중요합니다.

### 2) 테스트 전반의 실행 흐름

테스트는 보통 아래 순서로 진행됩니다.

1. 페이지 진입
2. 사용자 입력 또는 버튼 클릭
3. UI 상태 변화 확인
4. 기대 값과 실제 값 비교
5. 실패 시 로그/스크린샷/trace 수집
6. 다음 테스트로 정리 및 재사용

이 흐름은 페이지 객체와 테스트 코드가 분리되어 있어, 각 시나리오가 로직보다 사용자 행동 중심으로 읽히도록 설계되어 있습니다.

### 3) 사용자 시나리오별 세부 검증

#### 로그인
- 정상 로그인
- 잘못된 사용자 이름/비밀번호
- 빈 값 검증
- 잠금 계정 처리
- 성공/실패 이후 페이지 전환 확인

#### 상품
- 상품 목록 수 검증
- 가격 확인
- 정렬 검증
- 상세 페이지 진입
- 로그아웃 검증
- 선택된 상품 정보와 목록 정보 일치 여부 확인

#### 장바구니
- 상품 추가
- 여러 상품 추가
- 상품 제거
- 상품 추가/제거 버튼 상태 전환 검증
- 빈 장바구니 상태 검증
- Continue Shopping 동작 확인
- 비어 있는 장바구니에서 체크아웃 버튼 비활성화 검증

#### 체크아웃
- 고객 정보 입력
- 필수 입력값 누락 검증
- 총액 계산 검증
- 주문 완료 플로우 확인
- 여러 상품 조합의 합계 처리 검증

### 4) 결과 수집 및 실패 처리

테스트 종료 시 저장되는 정보는 다음과 같습니다.

- 로그 파일: `logs/`
- 스크린샷: `screenshots/`
- Trace: `traces/`
- 결과 요약: `reports/*.json`
- 실패 리포트: `reports/bug_reports/*.md`

특히 실패 발생 시에는 단순히 테스트가 실패했다는 사실만 보다는, 어떤 입력값을 넣었고 어떤 단계에서 멈췄는지 확인할 수 있도록 스크린샷과 trace를 남깁니다. 이는 디버깅 속도와 재현성을 크게 개선합니다.

---

## 7. 테스트 범위

### 로그인
- `test_valid_login_opens_products`
- `test_invalid_login_shows_error`
- `test_locked_out_user_cannot_login`

### 상품
- `test_product_list_contains_names_and_prices`
- `test_sort_products_by_price_low_to_high`
- `test_sort_products_by_price_high_to_low`
- `test_sort_products_by_name_z_to_a`
- `test_product_detail_page_opens`
- `test_logout_returns_to_login_page`

### 장바구니
- `test_add_and_remove_cart_item`
- `test_add_multiple_cart_items`
- `test_add_button_changes_to_remove_and_removes_item`
- `test_remove_last_item_leaves_cart_empty`
- `test_continue_shopping_returns_to_products`
- `test_remove_one_of_multiple_items_keeps_remaining_items`
- `test_checkout_disabled_when_cart_is_empty`
- `test_removing_item_keeps_remaining_order`

### 체크아웃
- `test_complete_checkout`
- `test_checkout_total_is_reported`
- `test_checkout_requires_first_name`
- `test_checkout_requires_last_name`
- `test_checkout_requires_postal_code`
- `test_checkout_total_for_multiple_items`

---

## 8. 설계 원칙

1. Page Object Model 적용
   - UI 동작을 페이지 객체로 분리한다.
   - 테스트 코드는 사용자 행동 중심으로 작성한다.
   - 중복 로직을 줄이고, 페이지별 책임을 분명하게 유지한다.

2. 테스트 데이터 분리
   - 사용자 정보와 고객 정보는 별도 파일에서 관리한다.
   - 테스트 코드 자체가 값에 종속되지 않도록 구성한다.

3. 실패 증거 보존
   - 스크린샷, trace, 로그를 남겨 재현 가능하게 한다.
   - 버그 리포트 작성 시 근거 자료로 바로 사용할 수 있게 구성한다.

4. 사용자 흐름 중심 검증
   - 단순 클릭이 아니라 실제 쇼핑 플로우를 검증한다.
   - 상태 전이와 예외 상황을 함께 검증한다.

5. 유지보수성 확보
   - 한 페이지의 동작이 여러 테스트에 반복되지 않도록 설계한다.
   - 테스트가 기능 변화에 쉽게 적응할 수 있도록 구조를 유지한다.

---

## 9. 리포트 기능

테스트 실패 시 자동으로 다음 항목이 생성됩니다.

- 로그 파일
- 실패 요약 파일
- 실패 상세 보고서
- 스크린샷
- Playwright trace

이 기능은 단순히 실패 여부만 표시하는 것이 아니라, 어떤 단계에서 어떤 오류가 발생했는지 파악할 수 있게 도와줍니다. 특히 QA 리뷰나 디버깅 회의에서 재현 가능한 근거 자료로 활용됩니다.

---

## 10. 개선점 및 보완 계획

현재 구현은 핵심 구매 흐름과 실패 분석 자동화에 집중한 초기 버전입니다. 실제 서비스 환경에서도 안정적으로 운영하려면 다음 항목을 보완할 필요가 있습니다.

| 개선 영역 | 현재 한계 | 보완 방향 |
| --- | --- | --- |
| 브라우저 호환성 | Chromium 환경에서만 검증 | Firefox·WebKit과 다양한 viewport를 CI matrix에 추가 |
| 안정성 관리 | flaky test를 별도로 측정하지 않음 | 재실행 이력과 실패 빈도를 수집해 flaky 판단 및 격리 기준 수립 |
| 테스트 분류 | 결함 탐지용 테스트와 회귀 테스트가 함께 실행됨 | `regression`, `failure_demo` marker를 추가해 목적별 테스트 스위트 분리 |
| 협업 연동 | CI artifact를 직접 확인해야 함 | Jira·Slack에 실패 요약과 증거 경로를 자동 전달하도록 확장 |


---

## 11. 정리

이 프로젝트는 SauceDemo의 로그인부터 주문 완료까지 이어지는 핵심 사용자 여정을 자동화하고, 정상 흐름과 예외 상황을 함께 검증한 UI E2E 테스트 프로젝트입니다.

Page Object Model, pytest fixture와 hook, 테스트 데이터·환경 설정 분리를 통해 유지보수 가능한 구조를 설계했습니다. 또한 테스트 실패 시 로그, 스크린샷, Playwright trace, JSON 결과와 버그 리포트를 자동으로 생성해 **테스트 실행에서 원인 분석과 공유까지 이어지는 QA 워크플로우**를 구현했습니다.

이를 통해 단순히 자동화 도구를 사용할 수 있다는 점을 넘어 다음과 같은 QA 역량을 보여주고자 했습니다.

- 비즈니스 위험도를 고려한 테스트 시나리오와 우선순위 설계
- 정상·예외·경계 조건을 포함한 검증 범위 구성
- 독립적이고 반복 가능한 테스트 환경 구현
- 실패 원인을 빠르게 파악할 수 있는 증거 수집 및 리포팅
- CI 기반의 지속적인 회귀 테스트 운영

궁극적으로 이 프로젝트는 **결함을 발견하는 테스트뿐 아니라, 발견한 문제를 재현 가능하고 전달 가능한 정보로 만드는 과정까지 자동화하는 것**을 목표로 합니다.
