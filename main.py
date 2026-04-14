"""
main.py — FastAPI REST API wrapping the Java Selenium Tree-sitter parser.

Run:
    pip install -r requirements.txt
    uvicorn main:app --reload

Swagger UI : http://127.0.0.1:8000/docs
ReDoc      : http://127.0.0.1:8000/redoc
"""

from __future__ import annotations

import logging
import pathlib
import sys
import time
from typing import Optional

from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# Import JavaSeleniumParser from our local parser.py.
#
# On Python 3.9–3.11 the deprecated stdlib `parser` module still exists as
# a shared-library extension (.so/.dylib), NOT as a built-in, so it is
# resolved via sys.path just like any other module.  Inserting our project
# directory at position 0 guarantees that Python finds parser.py here before
# it finds the stdlib copy.  On Python 3.12+ the stdlib module is gone, so
# there is no conflict at all.
# ---------------------------------------------------------------------------
_HERE = str(pathlib.Path(__file__).parent.resolve())
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

from parser import JavaSeleniumParser  # noqa: E402

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Singleton parser — Tree-sitter language initialisation is expensive;
# do it once at startup and reuse for every request.
# ---------------------------------------------------------------------------

_parser = JavaSeleniumParser()
logger.info("JavaSeleniumParser initialised and ready.")

# ---------------------------------------------------------------------------
# Built-in Java Selenium samples used by GET /parse/sample/{name}.
# These also serve as copy-paste examples when testing /parse via Swagger.
# ---------------------------------------------------------------------------

SAMPLES: dict[str, str] = {

    # ------------------------------------------------------------------
    # LoginTest — covers @Before/@After, driver.get, findElement,
    #              sendKeys, click, getTitle, getText
    # ------------------------------------------------------------------
    "LoginTest": """\
import org.junit.*;
import org.openqa.selenium.*;
import org.openqa.selenium.chrome.ChromeDriver;

@RunWith(JUnit4.class)
public class LoginTest {

    private WebDriver driver;

    @Before
    public void setUp() {
        driver = new ChromeDriver();
        driver.manage().timeouts().implicitlyWait(10, TimeUnit.SECONDS);
    }

    // Tests successful login with valid credentials
    @Test
    public void testSuccessfulLogin() {
        driver.get("https://example.com/login");
        driver.findElement(By.id("username")).sendKeys("admin");
        driver.findElement(By.id("password")).sendKeys("password123");
        driver.findElement(By.id("loginBtn")).click();
        String title = driver.getTitle();
        Assert.assertEquals("Dashboard", title);
    }

    @Test
    public void testLoginWithInvalidCredentials() {
        driver.get("https://example.com/login");
        driver.findElement(By.id("username")).sendKeys("wronguser");
        driver.findElement(By.id("password")).sendKeys("wrongpass");
        driver.findElement(By.cssSelector("button[type='submit']")).click();
        String errorMsg = driver.findElement(By.className("error-message")).getText();
        Assert.assertTrue(errorMsg.contains("Invalid credentials"));
    }

    @After
    public void tearDown() {
        if (driver != null) {
            driver.quit();
        }
    }
}
""",

    # ------------------------------------------------------------------
    # SearchTest — covers @BeforeClass/@AfterClass, submit, clear,
    #              getCurrentUrl, isDisplayed, block comments
    # ------------------------------------------------------------------
    "SearchTest": """\
import org.junit.*;
import org.openqa.selenium.*;
import org.openqa.selenium.chrome.ChromeDriver;

public class SearchTest {

    private WebDriver driver;

    @BeforeClass
    public static void setUpClass() {
        System.out.println("Starting Search Test Suite");
    }

    @Before
    public void setUp() {
        driver = new ChromeDriver();
    }

    /* Verifies that a basic keyword search returns at least one result */
    @Test
    public void testBasicSearch() {
        driver.get("https://example.com");
        driver.findElement(By.name("q")).sendKeys("Selenium WebDriver");
        driver.findElement(By.name("q")).submit();
        WebElement firstResult = driver.findElement(By.cssSelector(".result:first-child"));
        Assert.assertTrue(firstResult.isDisplayed());
    }

    // Tests search with a filter option applied
    @Test
    public void testSearchWithFilters() {
        driver.get("https://example.com/search");
        driver.findElement(By.id("searchBox")).clear();
        driver.findElement(By.id("searchBox")).sendKeys("Java testing");
        driver.findElement(By.id("filterDropdown")).click();
        driver.findElement(By.xpath("//option[@value='recent']")).click();
        driver.findElement(By.id("searchBtn")).click();
        String url = driver.getCurrentUrl();
        Assert.assertTrue(url.contains("filter=recent"));
    }

    @After
    public void tearDown() {
        driver.close();
    }

    @AfterClass
    public static void tearDownClass() {
        System.out.println("Search Tests Completed");
    }
}
""",

    # ------------------------------------------------------------------
    # CheckoutTest — covers chained calls, multiple sendKeys, isEnabled,
    #                @SuppressWarnings (normal_annotation), maximize
    # ------------------------------------------------------------------
    "CheckoutTest": """\
import org.junit.*;
import org.openqa.selenium.*;
import org.openqa.selenium.chrome.ChromeDriver;

@RunWith(JUnit4.class)
public class CheckoutTest {

    private WebDriver driver;

    @Before
    public void setUp() {
        driver = new ChromeDriver();
        driver.manage().window().maximize();
    }

    // Tests the complete e-commerce checkout flow end-to-end
    @Test
    @SuppressWarnings("unused")
    public void testCompleteCheckoutFlow() {
        driver.get("https://shop.example.com");
        driver.findElement(By.cssSelector(".product-card .add-to-cart")).click();
        driver.findElement(By.id("cart-icon")).click();
        driver.findElement(By.id("checkout-btn")).click();
        driver.findElement(By.id("firstName")).sendKeys("John");
        driver.findElement(By.id("lastName")).sendKeys("Doe");
        driver.findElement(By.id("email")).sendKeys("john@example.com");
        driver.findElement(By.id("address")).sendKeys("123 Main St");
        driver.findElement(By.id("placeOrder")).click();
        String confirmationText = driver.findElement(By.id("confirmation")).getText();
        Assert.assertTrue(confirmationText.contains("Order placed"));
    }

    @Test
    public void testEmptyCartCheckout() {
        driver.get("https://shop.example.com/cart");
        boolean checkoutDisabled = !driver.findElement(By.id("checkout-btn")).isEnabled();
        Assert.assertTrue(checkoutDisabled);
    }

    @After
    public void tearDown() {
        driver.quit();
    }
}
""",
}

# ---------------------------------------------------------------------------
# Pydantic response models — used for Swagger schema generation and
# response validation.
# ---------------------------------------------------------------------------


class MethodResult(BaseModel):
    """Parsed data for a single Java method."""

    name: str = Field(description="Method name")
    annotations: list[str] = Field(
        default=[],
        description="Annotations decorating the method, e.g. @Test, @Before",
    )
    code: str = Field(default="", description="Full source text of the method")
    comments: str = Field(
        default="", description="Comment(s) immediately preceding the method"
    )
    selenium_actions: list[str] = Field(
        default=[],
        description="Selenium API call snippets detected inside the method body",
    )


class ClassResult(BaseModel):
    """Parsed data for a single Java class."""

    class_name: str = Field(description="Class name")
    annotations: list[str] = Field(
        default=[], description="Class-level annotations e.g. @RunWith(...)"
    )
    methods: list[MethodResult] = Field(
        default=[], description="All methods found in this class"
    )


class ParseResponse(BaseModel):
    """Top-level response returned by POST /parse and GET /parse/sample/{name}."""

    file: str = Field(
        description="Source file name, or '<string>' when raw code was supplied"
    )
    classes: list[ClassResult] = Field(
        default=[], description="All Java classes extracted from the source"
    )
    parse_time_ms: float = Field(
        description="Wall-clock time taken by the parser, in milliseconds"
    )


class HealthResponse(BaseModel):
    status: str
    parser_ready: bool


class SampleListResponse(BaseModel):
    samples: list[str]
    hint: str


# ---------------------------------------------------------------------------
# FastAPI application
# ---------------------------------------------------------------------------

app = FastAPI(
    title="Java Selenium Parser API",
    description=(
        "Parse Java Selenium test files using a **Tree-sitter AST** — no regex.\n\n"
        "Extracts **classes**, **methods**, **annotations**, **comments**, "
        "and **Selenium API calls**.\n\n"
        "### Quick start\n"
        "1. `GET /samples` — list built-in samples\n"
        "2. `GET /parse/sample/LoginTest` — parse the login sample\n"
        "3. `POST /parse` — upload your own `.java` file or paste raw code\n"
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Allow all origins — fine for local development; tighten in production.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Request logging middleware
# ---------------------------------------------------------------------------


@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log method, path, status code, and elapsed time for every request."""
    t0 = time.perf_counter()
    response = await call_next(request)
    ms = (time.perf_counter() - t0) * 1000
    logger.info(
        "%s %s → %d  (%.1f ms)",
        request.method,
        request.url.path,
        response.status_code,
        ms,
    )
    return response


# ---------------------------------------------------------------------------
# Internal helper
# ---------------------------------------------------------------------------


def _build_response(raw: dict, elapsed_ms: float) -> ParseResponse:
    """
    Convert the dict produced by ParseResult.to_dict() into a ParseResponse.

    The parser returns {"class": "ClassName", ...} per class; we map that to
    ClassResult.class_name to avoid the Python reserved-word clash.
    """
    classes = [
        ClassResult(
            class_name=cls["class"],
            annotations=cls.get("annotations", []),
            methods=[MethodResult(**m) for m in cls.get("methods", [])],
        )
        for cls in raw.get("classes", [])
    ]
    return ParseResponse(
        file=raw["file"],
        classes=classes,
        parse_time_ms=round(elapsed_ms, 2),
    )


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@app.get(
    "/health",
    response_model=HealthResponse,
    tags=["Utility"],
    summary="Health check",
)
async def health_check():
    """Returns `status: ok` confirming the API and parser are ready."""
    return HealthResponse(status="ok", parser_ready=True)


@app.get(
    "/samples",
    response_model=SampleListResponse,
    tags=["Samples"],
    summary="List built-in sample names",
)
async def list_samples():
    """
    Returns the names of all built-in Java Selenium samples.

    Use `GET /parse/sample/{name}` to parse any of them instantly.
    """
    return SampleListResponse(
        samples=list(SAMPLES.keys()),
        hint="Use GET /parse/sample/{name} to parse any of these.",
    )


@app.get(
    "/parse/sample/{name}",
    response_model=ParseResponse,
    tags=["Samples"],
    summary="Parse a built-in sample by name",
)
async def parse_sample(name: str):
    """
    Parse one of the embedded Java Selenium samples and return structured JSON.

    **Available names:** `LoginTest` · `SearchTest` · `CheckoutTest`

    Each sample demonstrates different Selenium patterns:
    - **LoginTest** — `@Before/@After`, `findElement`, `sendKeys`, `click`, `getTitle`
    - **SearchTest** — `@BeforeClass/@AfterClass`, `submit`, `clear`, `getCurrentUrl`
    - **CheckoutTest** — chained calls, multiple `sendKeys`, `isEnabled`, `@SuppressWarnings`
    """
    code = SAMPLES.get(name)
    if code is None:
        raise HTTPException(
            status_code=404,
            detail=f"Sample '{name}' not found. Available: {list(SAMPLES.keys())}",
        )

    t0 = time.perf_counter()
    try:
        result = _parser.parse_source(code, filename=f"{name}.java")
    except Exception as exc:
        logger.exception("Parser error on sample '%s'", name)
        raise HTTPException(status_code=500, detail=f"Parser error: {exc}") from exc

    return _build_response(result.to_dict(), (time.perf_counter() - t0) * 1000)


@app.post(
    "/parse",
    response_model=ParseResponse,
    tags=["Parser"],
    summary="Parse a Java file or raw code",
)
async def parse_java(
    file: Optional[UploadFile] = File(
        default=None,
        description="Upload a `.java` source file.",
    ),
    code: Optional[str] = Form(
        default=None,
        description=(
            "Paste raw Java source code as a plain string "
            "(use this when you don't have a file to upload)."
        ),
    ),
):
    """
    Parse Java Selenium source code and return structured JSON.

    **Provide exactly one of the following inputs:**

    | Input | How |
    |-------|-----|
    | `file` | Upload a `.java` file via the file picker |
    | `code` | Paste raw Java source into the text field |

    **Output includes:**
    - Class names and class-level annotations
    - Method names, full source, annotations, and preceding comments
    - Selenium API calls detected in each method body

    ---
    *Tip: copy one of the samples from `GET /samples` into the `code` field to try it out.*
    """
    # Require at least one input
    if file is None and not code:
        raise HTTPException(
            status_code=422,
            detail="Provide either a 'file' (file upload) or 'code' (form text).",
        )

    # File takes priority when both are supplied
    if file is not None:
        raw_bytes = await file.read()
        if not raw_bytes:
            raise HTTPException(status_code=422, detail="Uploaded file is empty.")
        filename = file.filename or "upload.java"
        source: bytes | str = raw_bytes
        logger.info("Parsing uploaded file: %s (%d bytes)", filename, len(raw_bytes))
    else:
        source = code  # type: ignore[assignment]
        filename = "<string>"
        logger.info("Parsing raw code (%d chars)", len(code or ""))

    t0 = time.perf_counter()
    try:
        result = _parser.parse_source(source, filename=filename)
    except Exception as exc:
        logger.exception("Parser failed for '%s'", filename)
        raise HTTPException(status_code=500, detail=f"Parser error: {exc}") from exc

    return _build_response(result.to_dict(), (time.perf_counter() - t0) * 1000)
