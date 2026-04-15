# ATR Automation Framework

A TestNG-based Java automation framework for the **ATR (Automated Test Repository) Web Portal**.
Covers UI automation (Selenium WebDriver, Playwright, Perfecto), REST API validation, and mobile testing (Appium).

---

## Project Overview

This framework is organised into clear, interconnected layers:

```
Test Layer (testcases/web/)
    ↓
Business Functions Layer (businessfunctions/)
    ↓
Page Layer (pages/)
    ├── UI Pages     (pages/atrwebportal/)   — Selenium / Playwright / Perfecto
    └── API Pages    (pages/api/)            — REST API wrappers
```

Each layer depends only on lower layers — test classes call business functions, which call pages, which call APIs.

---

## Folder Structure

```
src/
├── main/java/pkg1/test/
│   └── AppConfig.java              — global config constants
└── test/java/com/ntrs/demoapp/
    ├── businessfunctions/
    │   └── Test.java               — orchestration layer
    ├── pages/
    │   ├── api/                    — REST API page wrappers
    │   │   ├── Accounts_Page.java
    │   │   ├── Adu_Saas_Page.java
    │   │   ├── Core_Reference_Page.java
    │   │   └── Get_CertificateToken_Page.java
    │   └── atrwebportal/           — Selenium UI pages
    │       ├── Login_Page.java
    │       ├── Navigation_Page.java
    │       ├── Menu_Page.java
    │       ├── MyAccount_Page.java
    │       ├── RegisterUser_Page.java
    │       ├── ATR_HomePage.java
    │       ├── ATR_Application_Page.java
    │       ├── ATR_Portal_Playwright_Page.java
    │       ├── Login_Playwright_Page.java
    │       ├── Azure_Cloud_Page.java
    │       ├── FinancialCalculators_Perfecto_Page.java
    │       └── InterestCalculator_Perfecto_Page.java
    ├── retryanalyzer/
    │   └── RetryAnalyzer.java      — TestNG IRetryAnalyzer
    └── testcases/
        ├── BaseTest.java           — Selenium driver setup/teardown
        ├── BaseTestAppium.java     — Appium driver setup/teardown
        └── web/
            ├── ATR_Portal_Tests.java
            ├── ATR_Application_Regression_Tests.java
            ├── ATR_Web_Portal_Tests.java
            ├── ATR_Portal_POC_Tests.java
            ├── ATR_Portal_POC_Retry_Tests.java
            └── Azure_Public_Cloud_Tests.java
resources/
└── test_suites/
    └── regression.xml
```

---

## Automation Flows

| Flow | Test Class | Description |
|------|-----------|-------------|
| Flow 1 | `ATR_Portal_Tests` | Login (with token) + Dashboard navigation |
| Flow 2 | `ATR_Application_Regression_Tests` | Create account via API, verify in UI |
| Flow 3 | `ATR_Web_Portal_Tests` | Menu navigation, item visibility |
| Flow 4 | `ATR_Portal_POC_Retry_Tests` | Flaky test retry via `RetryAnalyzer` |
| Flow 5 | `Azure_Public_Cloud_Tests` | Azure deployment UI + ADU SaaS API calls |
| POC    | `ATR_Portal_POC_Tests` | Playwright login, registration, home page |

---

## Prerequisites

- Java 11+
- Maven 3.8+
- Chrome or Firefox browser
- ChromeDriver / GeckoDriver on PATH (or use Selenium Manager)
- _(Optional)_ Appium server for mobile tests
- _(Optional)_ Node.js for Playwright browser installation

---

## How to Run Tests

### Full Regression Suite (default)

```bash
mvn test
```

### Specific test class

```bash
mvn test -Dtest=ATR_Portal_Tests
```

### Specific test method

```bash
mvn test -Dtest=ATR_Portal_Tests#testLoginFlow
```

### With custom browser

```bash
mvn test -Dbrowser=firefox
```

### Headless mode

```bash
mvn test -Dheadless=true
```

### Smoke tests only

```bash
mvn test -P smoke
```

### LambdaTest cloud execution

```bash
export LT_USERNAME=your_username
export LT_ACCESS_KEY=your_access_key
mvn test -P lambdatest
```

---

## Key Class Relationships

```
ATR_Portal_Tests
  ├── extends BaseTest
  └── uses businessfunctions.Test
        ├── Login_Page  →  Get_CertificateToken_Page (API)
        └── Navigation_Page

ATR_Application_Regression_Tests
  ├── extends BaseTest
  ├── uses Accounts_Page (API)  →  Get_CertificateToken_Page
  └── uses ATR_Application_Page → Accounts_Page + Core_Reference_Page

Azure_Public_Cloud_Tests
  ├── extends BaseTest
  ├── uses Azure_Cloud_Page  →  Adu_Saas_Page + Core_Reference_Page
  └── uses Adu_Saas_Page  →  Get_CertificateToken_Page

ATR_Portal_POC_Retry_Tests
  ├── extends BaseTest
  └── uses RetryAnalyzer (retryAnalyzer = RetryAnalyzer.class)
```

---

## Configuration

All constants are centralised in `AppConfig.java` (`pkg1.test` package).
Override at runtime with `-D` system properties or environment variables:

| Property | Default | Description |
|----------|---------|-------------|
| `browser` | `chrome` | Browser (`chrome` / `firefox`) |
| `headless` | `false` | Run headless |
| `env` | `staging` | Target environment |
| `platform` | `android` | Mobile platform (Appium) |
| `LT_USERNAME` | — | LambdaTest username |
| `LT_ACCESS_KEY` | — | LambdaTest access key |

---

## Reporting

Test results are written to `target/surefire-reports/`.
Open `target/surefire-reports/index.html` for the HTML report.
