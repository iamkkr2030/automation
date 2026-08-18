# SauceDemo 테스트 케이스 문서

## 1. 개요
- 프로젝트: SauceDemo Playwright QA Automation
- 대상 기능: 로그인, 상품 목록, 장바구니, 체크아웃
- 테스트 도구: Playwright + Python + pytest
- 검증 일자: 2026-08-18
- 실행 명령: `pytest tests/test_login.py tests/test_products.py tests/test_cart.py tests/test_checkout.py -ra`
- 수정 전 기준 실행 결과: 25 passed, 2 failed in 54.05s
- 현재 상태: 자동화 테스트 2건을 수정했으며 전체 회귀 테스트 재실행 필요

## 2. 수정 전 기준 테스트 결과 요약

> 아래 수치는 자동화 코드 수정 전 실행 결과이며 현재 품질 상태를 의미하지 않는다.

| 상태 | 건수 |
|---|---:|
| 통과 | 25 |
| 실패 | 2 |
| 전체 | 27 |

## 3. 실행 로그 구조화 요약

| 항목 | 값 |
|---|---|
| 실행일시 | 2026-08-18 |
| 수정 전 실행 환경 | Windows 11 / Python 3.14.6 |
| 브라우저 | Chromium |
| 테스트 프레임워크 | Playwright + pytest |
| 전체 테스트 수 | 27 |
| 통과 | 25 |
| 실패 | 2 |
| 실패율 | 7.41% |
| 실행 시간 | 54.05s |
| 기본 URL | https://www.saucedemo.com/ |
| 주요 실패 파일 | tests/test_cart.py, tests/test_checkout.py |

### 3.1 전체 실행 로그 요약
- 로그인, 상품, 장바구니, 체크아웃 플로우 모두 정상적으로 실행되었음
- 실패는 총 2건으로, 전체 흐름의 핵심 기능은 대부분 안정적임
- 실패는 모두 UI 상태/총액 검증 단계에서 발생했으며, 제품 핵심 기능 자체의 전체 경로는 대부분 통과함

### 3.2 실패 통계

| 실패 유형 | 건수 | 비고 |
|---|---:|---|
| UI 상태 검증 실패 | 1 | 빈 장바구니 체크아웃 버튼이 enabled 상태 |
| 요소 탐색/검증 실패 | 1 | 총액 라벨 `.summary_total_label` 미탐색 |
| 환경 문제 | 0 | 현재 확인되지 않음 |
| 데이터 문제 | 0 | 현재 확인되지 않음 |

## 4. 테스트 케이스 목록

| ID | 기능 | 조건 | 절차 | 예상 결과 | 실제 결과 | 상태 |
|---|---|---|---|---|---|---|
| TC-CONFIG-01 | 사이트 설정 값 정상 로딩 | 기본 설정 객체를 생성했을 때 | `SauceDemoConfig()` 인스턴스 생성 | 기본 URL, 사용자 정보, 셀렉터 값이 정상 로딩됨 | PASS. 설정값 정상 로딩 | Pass |
| TC-LOGIN-01 | 정상 로그인 시 상품 목록 페이지 진입 | 로그인 페이지에 접속하고 표준 사용자 계정이 준비됨 | 표준 사용자 계정으로 로그인 | `/inventory.html`로 이동하고 상품 목록 제목이 표시됨 | PASS. URL과 상품 제목이 정상 노출됨 | Pass |
| TC-LOGIN-02 | 잘못된 비밀번호 로그인 | 사용자 이름은 올바르고 비밀번호가 틀린 상태 | `standard_user` / `wrong_password`로 로그인 | "Username and password do not match" 메시지 노출 | PASS. 오류 메시지 정상 표시 | Pass |
| TC-LOGIN-03 | 존재하지 않는 사용자 로그인 | 등록되지 않은 사용자 이름 사용 | `not_a_user` / `secret_sauce`로 로그인 | "Username and password do not match" 메시지 노출 | PASS. 오류 메시지 정상 표시 | Pass |
| TC-LOGIN-04 | 빈 사용자 이름 로그인 | 비밀번호는 정상, 사용자 이름 공백 | 빈 사용자 이름 + `secret_sauce`로 로그인 | "Username is required" 메시지 노출 | PASS. 필수값 검증 정상 동작 | Pass |
| TC-LOGIN-05 | 빈 비밀번호 로그인 | 사용자 이름은 정상, 비밀번호 공백 | `standard_user` + 빈 비밀번호로 로그인 | "Password is required" 메시지 노출 | PASS. 필수값 검증 정상 동작 | Pass |
| TC-LOGIN-06 | 잠금 계정 로그인 차단 | 잠금된 계정 정보 사용 | 잠금 계정으로 로그인 | "Sorry, this user has been locked out" 메시지 노출 | PASS. 접근 제한 메시지 정상 표시 | Pass |
| TC-PRODUCT-01 | 상품 목록 이름/가격 표시 확인 | 로그인 완료 상태 | 상품 목록 페이지 진입 후 항목 수와 이름/가격 확인 | 6개 상품이 표시되고 각 항목의 이름/가격이 비어 있지 않음 | PASS. 6개 상품, 이름/가격 정상 노출 | Pass |
| TC-PRODUCT-02 | 낮은 가격순 정렬 | 상품 목록이 표시된 상태 | 정렬 옵션을 `lohi`로 변경 | 가격 오름차순으로 정렬됨 | PASS. 예상 정렬 결과와 일치 | Pass |
| TC-PRODUCT-03 | 높은 가격순 정렬 | 상품 목록이 표시된 상태 | 정렬 옵션을 `hilo`로 변경 | 가격 내림차순으로 정렬됨 | PASS. 예상 정렬 결과와 일치 | Pass |
| TC-PRODUCT-04 | 이름 내림차순 정렬 | 상품 목록이 표시된 상태 | 정렬 옵션을 `za`로 변경 | 이름 Z→A 순서로 정렬됨 | PASS. 예상 정렬 결과와 일치 | Pass |
| TC-PRODUCT-05 | 상품 상세 페이지 진입 | 상품 목록이 표시된 상태 | 특정 상품 선택 | 상품 상세 페이지로 이동하고 선택 상품 이름이 표시됨 | PASS. 상세 페이지와 URL 정상 진입 | Pass |
| TC-PRODUCT-06 | 로그아웃 후 로그인 페이지 복귀 | 로그인된 상태 | 로그아웃 버튼 클릭 | 로그인 페이지로 이동하고 로그인 버튼 표시 | PASS. 로그인 페이지 복귀 정상 | Pass |
| TC-CART-01 | 장바구니에 상품 추가/삭제 | 로그인 완료 상태 | 상품 추가 → 장바구니 확인 → 상품 제거 | 장바구니 상품 수가 증가/감소하고 항목이 정상 삭제됨 | PASS. 수량/항목 상태 정상 반영 | Pass |
| TC-CART-02 | 다중 상품 추가 | 로그인 완료 상태 | 두 개 이상의 상품 추가 | 장바구니 배지 숫자가 2이며 목록에 두 상품 표시 | PASS. 누적 카운트 및 항목 표시 정상 | Pass |
| TC-CART-03 | 상품 추가/제거 버튼 상태 전환 | 로그인 완료 상태 | 상품 추가 → Remove 버튼 확인 → 상품 제거 | 버튼 상태가 전환되고 장바구니 배지가 제거됨 | 수정 후 재검증 필요 | Not Run |
| TC-CART-04 | 마지막 상품 제거 시 장바구니 비우기 | 장바구니에 1개 상품 담긴 상태 | 마지막 상품 제거 | 장바구니가 비어 있고 항목 0개 유지 | PASS. Empty 상태 정상 동작 | Pass |
| TC-CART-05 | 계속 쇼핑 기능 | 장바구니에 상품 담긴 상태 | "Continue Shopping" 클릭 | 상품 목록 페이지로 복귀 | PASS. 상품 목록 표시 정상 | Pass |
| TC-CART-06 | 일부 상품 제거 후 나머지 유지 | 3개 상품이 장바구니에 담긴 상태 | 특정 상품만 삭제 | 선택한 상품만 제거되고 나머지 항목 순서 유지 | PASS. 남은 항목 정상 유지 | Pass |
| TC-CART-07 | 빈 장바구니에서 체크아웃 비활성화 | 로그인 완료, 장바구니 비어 있음 | 장바구니 페이지에서 체크아웃 버튼 확인 | Checkout 버튼이 비활성화 상태여야 함 | 의도적으로 실패하도록 유지 | Fail Demo |
| TC-CART-08 | 항목 제거 후 남은 순서 유지 | 3개 상품이 담긴 상태 | 중간 상품 제거 | 남은 상품의 순서가 유지됨 | PASS. 순서 유지 정상 | Pass |
| TC-CHECKOUT-01 | 정상 체크아웃 완료 | 상품 1개 담긴 상태, 고객 정보 입력 가능 | 로그인 → 상품 추가 → 장바구니 → 체크아웃 → 정보 입력 → 결제 완료 | 주문 성공 메시지 표시 및 총액 계산 정상 | PASS. 완료 플로우 정상 동작 | Pass |
| TC-CHECKOUT-02 | 총액 보고 값 검증 | 백팩 1개 담긴 상태 | 체크아웃 정보 입력 후 총액 확인 | 총액이 $32.39여야 함 | 의도적으로 화면 이동을 생략하여 실패하도록 유지 | Fail Demo |
| TC-CHECKOUT-03 | 이름 누락 시 체크아웃 차단 | 고객 정보의 이름 공백 | 첫 이름을 비워둔 상태에서 계속 진행 | "First Name is required" 메시지 노출 | PASS. 필수값 검증 정상 | Pass |
| TC-CHECKOUT-04 | 성 누락 시 체크아웃 차단 | 고객 정보의 성 공백 | 마지막 이름을 비워둔 상태에서 계속 진행 | "Last Name is required" 메시지 노출 | PASS. 필수값 검증 정상 | Pass |
| TC-CHECKOUT-05 | 우편번호 누락 시 체크아웃 차단 | 고객 정보의 우편번호 공백 | 우편번호를 비워둔 상태에서 계속 진행 | "Postal Code is required" 메시지 노출 | PASS. 필수값 검증 정상 | Pass |
| TC-CHECKOUT-06 | 여러 상품 총액 계산 | 2개 상품이 장바구니에 담긴 상태 | 상품 추가 후 체크아웃 정보 입력 및 총액 확인 | 총액이 $43.18이어야 함 | PASS. 총액 계산 정상 | Pass |

## 5. 수정 전 실패 분석과 조치

### 5.1 확인된 사실 (Confirmed Facts)
- `tests/test_cart.py::test_checkout_disabled_when_cart_is_empty`는 수정 전 실행에서 실패했다.
- `tests/test_checkout.py::test_checkout_total_is_reported`는 수정 전 실행에서 실패했다.
- 실패 로그에 따르면 빈 장바구니에서 `Checkout` 버튼이 `enabled` 상태로 표시되었다.
- 체크아웃 총액 검증 단계에서 `.summary_total_label` 로케이터가 30초 내에 탐색되지 않았다.
- 수정 전 전체 결과는 25 passed, 2 failed이다.

### 5.2 확인된 원인과 의도
- 총액 테스트는 실패 리포트 생성을 확인하기 위해 체크아웃 개요 화면으로 이동하는 `continue_checkout()` 호출을 의도적으로 생략했다.
- 빈 장바구니 Checkout 비활성화 테스트는 실제 SauceDemo 동작과 다른 기대값을 사용하여 실패 증거 수집을 시연하도록 의도적으로 유지했다.
- 동일 상품 중복 방지 테스트는 이름과 실제 절차가 일치하지 않았다. 상품 추가/제거 버튼 상태 전환 테스트로 이름과 설명을 수정했다.

## 6. 실패 분류 메타데이터

| 필드 | 값 (TC-CART-07) | 값 (TC-CHECKOUT-02) |
|---|---|---|
| Test ID | TC-CART-07 | TC-CHECKOUT-02 |
| Failure Type | Test Design Error | Automation Workflow Error |
| Failed Step | 장바구니 페이지에서 Checkout 버튼 상태 검증 | 주문 총액 추출 단계 |
| Current URL | https://www.saucedemo.com/cart.html | https://www.saucedemo.com/checkout-step-one.html |
| Locator | `get_by_role("button", name="Checkout")` | `.summary_total_label` |
| Severity | Low | Medium |
| Confidence | High | High |
| Classification | Automation | Automation |
| Evidence | AssertionError, button enabled | TimeoutError, locator not found |

### 6.1 분류 기준
- 제품 버그: 실제 서비스 로직이 잘못된 경우
- 자동화 코드 문제: selector, assert logic, waiting 로직의 문제
- 환경 문제: 브라우저, 서버, 네트워크, 쿠키 등 외부 이슈
- 데이터 문제: 테스트 데이터, 사용자 상태, 입력 값오류

## 7. 자동화 테스트 수정 내역

### 실패 시연 1: 빈 장바구니 체크아웃 버튼 비활성화 검증
- 테스트 ID: TC-CART-07
- 증상: 장바구니가 비어 있는데도 `Checkout` 버튼이 enabled 상태로 노출됨
- 실제 실행 결과: `AssertionError: Locator expected to be disabled`
- 목적: assertion 실패 시 screenshot, trace, 로그 및 버그 리포트 생성 확인

### 실패 시연 2: 체크아웃 총액 라벨 탐색 실패
- 테스트 ID: TC-CHECKOUT-02
- 증상: 결제 정보 입력 직후 총액 요소를 찾지 못함
- 실제 실행 결과: `TimeoutError: Locator.inner_text: Timeout 30000ms exceeded`
- 목적: locator timeout 발생 시 실패 분석 및 리포트 생성 확인

## 8. 현재 상태
- 전체 테스트 수: 27
- 통과: 25
- 실패: 2
- 의도된 실패 지점: 장바구니 빈 상태 기대값, 체크아웃 개요 화면 이동 생략
- 현재 상태: 실패 리포팅 시연을 위해 두 테스트를 의도적으로 실패하도록 유지

## 9. 참고
- 이 문서의 25 passed, 2 failed 결과는 2026-08-18 수정 전 기준 실행 기록이다.
- 수정 후 결과는 외부 테스트 사이트에 접근 가능한 환경에서 전체 회귀 테스트를 실행한 뒤 갱신한다.
- 이후 수정 후 재검증 시 이 문서를 업데이트하여 실제 결과를 지속적으로 추적하는 것이 좋음
