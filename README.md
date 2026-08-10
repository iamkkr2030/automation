# 🛒 SauceDemo Playwright QA Automation

Playwright와 pytest를 활용하여 데모 쇼핑몰 **SauceDemo**의 주요 기능을 자동으로 테스트하는 QA 자동화 프로젝트입니다.

로그인부터 상품 선택, 장바구니, 주문 완료까지 실제 사용자의 쇼핑 과정을 자동화하고, 각 단계의 결과가 정상적으로 동작하는지 검증하는 것을 목표로 합니다.

---

## 📌 프로젝트 목적

이 프로젝트를 통해 다음과 같은 QA 자동화 기술을 학습하고 실습합니다.

* 웹 UI 자동화
* 테스트 케이스 설계
* pytest 기반 테스트 작성
* Playwright를 이용한 브라우저 제어
* Page Object Model(POM) 적용
* 테스트 데이터 분리
* 테스트 결과 검증
* 실패 시 스크린샷 및 Trace 확인
* 테스트 리포트 생성
* GitHub Actions를 이용한 자동 테스트

단순히 버튼을 클릭하는 자동화가 아니라 **"행동 → 결과 검증"**이 이루어지는 E2E 테스트 구축을 목표로 합니다.

---

# 🎯 테스트 대상

## SauceDemo

테스트 대상 사이트:

https://www.saucedemo.com/

SauceDemo는 Sauce Labs에서 제공하는 데모 쇼핑몰로, QA 자동화 테스트를 연습하기 위한 다양한 기능을 제공합니다.

### 주요 기능

* 로그인
* 상품 목록
* 상품 정렬
* 상품 상세 정보
* 장바구니 상품 추가
* 장바구니 상품 삭제
* 주문 정보 입력
* 주문 확인
* 주문 완료
* 로그아웃

실제 결제가 발생하지 않는 테스트용 사이트이기 때문에 반복적인 자동화 테스트에 적합합니다.

---

# 🔑 테스트 계정

SauceDemo에서는 테스트 목적으로 여러 계정을 제공합니다.

| 계정                        | 목적           |
| ------------------------- | ------------ |
| `standard_user`           | 정상적인 로그인 테스트 |
| `locked_out_user`         | 잠긴 계정 테스트    |
| `problem_user`            | 기능 문제 테스트    |
| `performance_glitch_user` | 성능 지연 테스트    |
| `error_user`              | 오류 동작 테스트    |
| `visual_user`             | 화면 표시 테스트    |

### 기본 비밀번호

```text
secret_sauce
```

### 기본 테스트 계정

```text
Username: standard_user
Password: secret_sauce
```

처음 자동화를 구현할 때는 `standard_user`를 사용합니다.

---

# 🛍️ 쇼핑몰 사용 흐름

전체적인 사용자 흐름은 다음과 같습니다.

```text
사이트 접속
    ↓
로그인
    ↓
상품 목록 확인
    ↓
상품 선택
    ↓
장바구니 추가
    ↓
장바구니 확인
    ↓
상품 삭제 또는 구매
    ↓
Checkout
    ↓
구매자 정보 입력
    ↓
주문 정보 확인
    ↓
구매 완료
    ↓
주문 완료 메시지 확인
```

---

# 🧪 테스트 범위

## 1. 로그인

### 정상 로그인

```text
standard_user
+
secret_sauce
↓
Login
↓
상품 목록 화면 이동
```

### 로그인 실패

다음과 같은 상황을 테스트합니다.

* 잘못된 아이디
* 잘못된 비밀번호
* 아이디 미입력
* 비밀번호 미입력
* 아이디와 비밀번호 모두 미입력
* 잠긴 계정 로그인

---

## 2. 상품

상품 목록에서 다음 기능을 테스트합니다.

* 상품 목록 표시
* 상품명 표시
* 상품 가격 표시
* 상품 상세 페이지 이동
* 상품 이름 오름차순 정렬
* 상품 이름 내림차순 정렬
* 가격 낮은 순 정렬
* 가격 높은 순 정렬

---

## 3. 장바구니

다음 기능을 테스트합니다.

* 상품 1개 추가
* 여러 상품 추가
* 장바구니 상품 개수 확인
* 상품명 확인
* 상품 가격 확인
* 상품 삭제
* 여러 상품 중 특정 상품 삭제
* 전체 상품 삭제
* 쇼핑 계속하기

---

## 4. 주문

주문 과정에서 다음 기능을 테스트합니다.

* Checkout 진입
* 이름 입력
* 성 입력
* 우편번호 입력
* 필수 입력값 검증
* 상품 가격 확인
* 상품 합계 확인
* 세금 확인
* 총 주문 금액 확인
* 주문 완료
* 주문 완료 메시지 확인

---

# 📋 주요 테스트 시나리오

## TC-001 정상 로그인

```text
1. SauceDemo 접속
2. standard_user 입력
3. secret_sauce 입력
4. Login 클릭
5. 상품 목록 화면 확인
```

### 기대 결과

상품 목록 화면으로 정상적으로 이동한다.

---

## TC-002 상품 장바구니 추가

```text
1. 로그인
2. 상품 선택
3. Add to cart 클릭
4. 장바구니 확인
```

### 기대 결과

선택한 상품이 장바구니에 추가되고 장바구니 개수가 `1`로 표시된다.

---

## TC-003 상품 삭제

```text
1. 로그인
2. 상품 추가
3. 장바구니 이동
4. Remove 클릭
```

### 기대 결과

선택한 상품이 장바구니에서 제거된다.

---

## TC-004 정상 구매

```text
1. 로그인
2. 상품 추가
3. 장바구니 이동
4. Checkout 클릭
5. 이름 입력
6. 성 입력
7. 우편번호 입력
8. Continue 클릭
9. 주문 정보 확인
10. Finish 클릭
```

### 기대 결과

다음 메시지가 표시된다.

```text
Thank you for your order!
```

---

# 🧪 테스트 케이스

## Login

| ID        | 테스트         | 기대 결과     | 우선순위   |
| --------- | ----------- | --------- | ------ |
| LOGIN-001 | 정상 로그인      | 상품 목록 이동  | High   |
| LOGIN-002 | 잘못된 비밀번호    | 오류 메시지 표시 | High   |
| LOGIN-003 | 존재하지 않는 사용자 | 오류 메시지 표시 | High   |
| LOGIN-004 | 아이디 미입력     | 오류 메시지 표시 | Medium |
| LOGIN-005 | 비밀번호 미입력    | 오류 메시지 표시 | Medium |
| LOGIN-006 | 전체 미입력      | 오류 메시지 표시 | Medium |
| LOGIN-007 | 잠긴 계정       | 계정 잠김 오류  | Medium |
| LOGIN-008 | 로그아웃        | 로그인 화면 이동 | High   |

## Product

| ID          | 테스트       | 기대 결과     | 우선순위   |
| ----------- | --------- | --------- | ------ |
| PRODUCT-001 | 상품 목록 확인  | 상품 표시     | High   |
| PRODUCT-002 | 상품명 확인    | 상품명 정상 표시 | Medium |
| PRODUCT-003 | 가격 확인     | 가격 정상 표시  | Medium |
| PRODUCT-004 | 상세 페이지    | 선택한 상품 표시 | Medium |
| PRODUCT-005 | 이름 A-Z 정렬 | 오름차순 정렬   | Medium |
| PRODUCT-006 | 이름 Z-A 정렬 | 내림차순 정렬   | Medium |
| PRODUCT-007 | 가격 낮은 순   | 가격 오름차순   | High   |
| PRODUCT-008 | 가격 높은 순   | 가격 내림차순   | High   |

## Cart

| ID       | 테스트      | 기대 결과      | 우선순위   |
| -------- | -------- | ---------- | ------ |
| CART-001 | 상품 추가    | 상품 추가 성공   | High   |
| CART-002 | 여러 상품 추가 | 상품 개수 일치   | High   |
| CART-003 | 상품 확인    | 상품 정보 일치   | High   |
| CART-004 | 가격 확인    | 가격 정보 일치   | High   |
| CART-005 | 상품 삭제    | 상품 제거      | High   |
| CART-006 | 특정 상품 삭제 | 해당 상품만 제거  | High   |
| CART-007 | 전체 삭제    | 장바구니 비어 있음 | Medium |

## Checkout

| ID        | 테스트      | 기대 결과     | 우선순위   |
| --------- | -------- | --------- | ------ |
| ORDER-001 | 정상 주문    | 주문 진행     | High   |
| ORDER-002 | 이름 미입력   | 오류 메시지    | Medium |
| ORDER-003 | 성 미입력    | 오류 메시지    | Medium |
| ORDER-004 | 우편번호 미입력 | 오류 메시지    | Medium |
| ORDER-005 | 상품 합계 확인 | 가격 일치     | High   |
| ORDER-006 | 세금 확인    | 세금 표시     | Medium |
| ORDER-007 | 총 금액 확인  | 계산 결과 일치  | High   |
| ORDER-008 | 주문 완료    | 완료 메시지 표시 | High   |

---

# 🛠️ 기술 스택

| 기술                   | 용도           |
| -------------------- | ------------ |
| Python               | 테스트 코드 작성    |
| Playwright           | 웹 브라우저 자동화   |
| pytest               | 테스트 실행 및 검증  |
| Page Object Model    | 테스트 코드 구조화   |
| pytest-html / Allure | 테스트 결과 리포트   |
| Git                  | 버전 관리        |
| GitHub               | 프로젝트 관리      |
| GitHub Actions       | CI 기반 자동 테스트 |

---

# 📂 프로젝트 구조

```text
playwright-shoppingmall-qa/
│
├── pages/
│   ├── login_page.py
│   ├── products_page.py
│   ├── cart_page.py
│   └── checkout_page.py
│
├── tests/
│   ├── test_login.py
│   ├── test_products.py
│   ├── test_cart.py
│   └── test_checkout.py
│
├── data/
│   ├── users.py
│   └── checkout_data.py
│
├── utils/
│   └── helpers.py
│
├── reports/
│
├── screenshots/
│
├── conftest.py
├── pytest.ini
├── requirements.txt
├── README.md
└── .gitignore
```

---

# 🏗️ Page Object Model

테스트 코드와 웹페이지 조작 코드를 분리하기 위해 Page Object Model(POM)을 사용합니다.

예를 들어 로그인 페이지의 동작을 `LoginPage`에서 관리합니다.

```python
class LoginPage:

    def __init__(self, page):
        self.page = page

    def login(self, username, password):
        self.page.get_by_placeholder("Username").fill(username)
        self.page.get_by_placeholder("Password").fill(password)
        self.page.get_by_role("button", name="Login").click()
```

테스트에서는 페이지의 동작만 호출합니다.

```python
def test_valid_login(page):

    login_page = LoginPage(page)

    login_page.login(
        "standard_user",
        "secret_sauce"
    )
```

이렇게 하면 테스트 코드가 실제 화면 요소를 직접 관리하지 않아 유지보수가 쉬워집니다.

---

# ⚙️ 설치

## 1. 저장소 다운로드

```bash
git clone <repository-url>
cd playwright-shoppingmall-qa
```

## 2. 가상환경 생성

```bash
python -m venv .venv
```

### Windows

```bash
.venv\Scripts\activate
```

### macOS / Linux

```bash
source .venv/bin/activate
```

## 3. 패키지 설치

```bash
pip install -r requirements.txt
```

## 4. Playwright 브라우저 설치

```bash
playwright install
```

---

# ▶️ 테스트 실행

## 전체 테스트

```bash
pytest
```

## 브라우저 화면을 보면서 실행

```bash
pytest --headed
```

## 특정 테스트 파일 실행

```bash
pytest tests/test_login.py --headed
```

## 특정 테스트 실행

```bash
pytest tests/test_login.py::test_valid_login --headed
```

---

# 📊 테스트 리포트

HTML 리포트를 사용하는 경우:

```bash
pytest --html=reports/result.html --self-contained-html
```

실행이 끝나면 다음 위치에 결과가 생성됩니다.

```text
reports/result.html
```

---

# 📸 실패 증거 수집

테스트가 실패했을 때 다음 정보를 남기는 것을 목표로 합니다.

* 테스트 이름
* 오류 메시지
* 기대 결과
* 실제 결과
* 스크린샷
* Playwright Trace
* 실행 브라우저

예:

```text
screenshots/
├── LOGIN-002_failed.png
├── CART-005_failed.png
└── ORDER-008_failed.png
```

이를 통해 테스트 실패 원인을 빠르게 확인할 수 있도록 구성합니다.

---

# 🔄 자동화 개발 순서

처음부터 모든 테스트를 구현하지 않고 단계적으로 개발합니다.

### Step 1. 환경 구축

```text
Python
↓
pytest
↓
Playwright
↓
Chromium
```

### Step 2. 로그인 자동화

```text
사이트 접속
↓
ID 입력
↓
Password 입력
↓
Login
↓
상품 페이지 확인
```

### Step 3. 상품 자동화

```text
상품 확인
↓
상품 정렬
↓
상품 상세 페이지
```

### Step 4. 장바구니 자동화

```text
상품 추가
↓
장바구니 확인
↓
상품 삭제
↓
개수 확인
```

### Step 5. 주문 자동화

```text
Checkout
↓
구매자 정보 입력
↓
주문 정보 확인
↓
Finish
↓
주문 완료 확인
```

### Step 6. 테스트 구조 개선

```text
Page Object Model
↓
Fixture
↓
테스트 데이터 분리
↓
중복 코드 제거
```

### Step 7. 결과 관리

```text
실패 스크린샷
+
Trace
+
HTML/Allure Report
```

### Step 8. CI 자동화

```text
GitHub Push
↓
GitHub Actions
↓
pytest 실행
↓
테스트 결과 확인
```

---

# 🎯 최종 목표

최종적으로 다음 명령 하나로 쇼핑몰의 주요 기능을 자동으로 테스트할 수 있도록 구성합니다.

```bash
pytest
```

자동화 과정:

```text
┌──────────────┐
│ SauceDemo 접속 │
└──────┬───────┘
       ↓
┌──────────────┐
│    로그인     │
└──────┬───────┘
       ↓
┌──────────────┐
│   상품 확인   │
└──────┬───────┘
       ↓
┌──────────────┐
│ 장바구니 추가 │
└──────┬───────┘
       ↓
┌──────────────┐
│ 장바구니 삭제 │
└──────┬───────┘
       ↓
┌──────────────┐
│  주문 정보   │
└──────┬───────┘
       ↓
┌──────────────┐
│   구매 완료   │
└──────┬───────┘
       ↓
┌──────────────┐
│ 결과 및 리포트 │
└──────────────┘
```

---

# 📈 향후 개선 계획

* [ ] 로그인 테스트 구현
* [ ] 상품 테스트 구현
* [ ] 장바구니 테스트 구현
* [ ] 주문 테스트 구현
* [ ] Page Object Model 적용
* [ ] Fixture 구성
* [ ] 테스트 데이터 분리
* [ ] 실패 스크린샷 저장
* [ ] Playwright Trace 적용
* [ ] HTML/Allure Report 적용
* [ ] Chromium 테스트
* [ ] Firefox 테스트
* [ ] GitHub Actions 연동
* [ ] 테스트 결과 자동 업로드
* [ ] 테스트 케이스 및 실행 결과 문서화

---

# 💡 프로젝트에서 중점적으로 보여줄 부분

이 프로젝트에서는 단순히 "Playwright를 사용할 수 있다"는 것보다 다음 내용을 보여주는 것을 목표로 합니다.

### QA 관점

* 요구사항을 테스트 케이스로 변환
* 정상/비정상 케이스 구분
* 기대 결과와 실제 결과 비교
* 테스트 우선순위 설정
* 테스트 실패 원인 분석

### 자동화 관점

* Playwright 활용
* pytest 활용
* Page Object Model
* Fixture
* 테스트 데이터 관리
* 실패 증거 수집
* 테스트 리포트

### CI/CD 관점

* GitHub Actions
* 자동 테스트 실행
* 테스트 결과 확인

---

# 👨‍💻 프로젝트 목표

> **실제 사용자가 쇼핑몰에서 수행하는 행동을 자동화하고, 각 기능이 정상적으로 동작하는지 자동으로 검증하는 QA 자동화 프로젝트를 구축한다.**

단순한 브라우저 조작이 아닌 **테스트 케이스 설계 → 자동화 → 검증 → 결과 기록 → 자동 실행**까지 하나의 QA 자동화 프로세스를 구현하는 것을 목표로 한다.
