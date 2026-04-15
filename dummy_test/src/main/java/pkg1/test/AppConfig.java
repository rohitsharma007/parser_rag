package pkg1.test;

/**
 * Application-level configuration constants used across the automation framework.
 * Provides URLs, credentials, and timeout values consumed by BaseTest and page classes.
 *
 * Layer: utility (main/java)
 * Used by: BaseTest (indirectly), API page classes, test classes
 */
public class AppConfig {

    // ─── Environment ────────────────────────────────────────────────────────

    /** Base URL for the ATR Web Portal (UI). */
    public static final String BASE_URL = "https://demo.atrwebportal.com";

    /** Base URL for the ATR REST API. */
    public static final String API_BASE_URL = "https://api.atrwebportal.com";

    /** Active environment (dev / staging / prod). */
    public static final String ENVIRONMENT = System.getProperty("env", "staging");

    // ─── Default Credentials ─────────────────────────────────────────────────

    /** Default test admin username. */
    public static final String DEFAULT_ADMIN_USER = "admin@atrportal.com";

    /** Default test admin password. */
    public static final String DEFAULT_ADMIN_PASSWORD = "Admin@Test1234";

    /** Default standard test user. */
    public static final String DEFAULT_TEST_USER = "testuser@atrportal.com";

    /** Default test user password. */
    public static final String DEFAULT_TEST_PASSWORD = "Test@1234";

    // ─── API Endpoints ───────────────────────────────────────────────────────

    /** Endpoint for certificate token retrieval. */
    public static final String TOKEN_ENDPOINT = API_BASE_URL + "/auth/certificate-token";

    /** Endpoint for accounts resource. */
    public static final String ACCOUNTS_ENDPOINT = API_BASE_URL + "/v1/accounts";

    /** Endpoint for ADU SaaS resource. */
    public static final String ADU_SAAS_ENDPOINT = API_BASE_URL + "/v1/adu-saas";

    /** Endpoint for core reference data. */
    public static final String CORE_REFERENCE_ENDPOINT = API_BASE_URL + "/v1/core-reference";

    // ─── Timeouts ────────────────────────────────────────────────────────────

    /** Implicit wait timeout in seconds. */
    public static final int IMPLICIT_WAIT_SECONDS = 10;

    /** Explicit wait timeout in seconds. */
    public static final int EXPLICIT_WAIT_SECONDS = 30;

    /** API request timeout in milliseconds. */
    public static final int API_TIMEOUT_MS = 15000;

    // ─── Retry Configuration ─────────────────────────────────────────────────

    /** Maximum number of retry attempts for flaky tests (used by RetryAnalyzer). */
    public static final int MAX_RETRY_COUNT = 3;

    // ─── Browser Configuration ───────────────────────────────────────────────

    /** Default browser for Selenium tests. */
    public static final String DEFAULT_BROWSER = System.getProperty("browser", "chrome");

    /** Whether to run in headless mode. */
    public static final boolean HEADLESS = Boolean.parseBoolean(
            System.getProperty("headless", "false"));

    // ─── Appium Configuration ────────────────────────────────────────────────

    /** Appium server URL. */
    public static final String APPIUM_SERVER_URL = "http://127.0.0.1:4723/wd/hub";

    /** Default mobile platform. */
    public static final String DEFAULT_PLATFORM = System.getProperty("platform", "android");

    /** Path to the Android APK. */
    public static final String ANDROID_APP_PATH = "app/ATRApp.apk";

    /** Path to the iOS IPA. */
    public static final String IOS_APP_PATH = "app/ATRApp.ipa";

    // ─── LambdaTest Configuration ────────────────────────────────────────────

    /** LambdaTest Hub URL for remote execution. */
    public static final String LAMBDATEST_HUB_URL = "https://hub.lambdatest.com/wd/hub";

    /** LambdaTest username (read from system property or env). */
    public static final String LT_USERNAME = System.getenv().getOrDefault(
            "LT_USERNAME", System.getProperty("lt.username", ""));

    /** LambdaTest access key (read from system property or env). */
    public static final String LT_ACCESS_KEY = System.getenv().getOrDefault(
            "LT_ACCESS_KEY", System.getProperty("lt.access.key", ""));

    // Private constructor — utility class
    private AppConfig() {}

    /**
     * Returns the full API URL for the given endpoint path.
     *
     * @param path relative path (e.g. "/v1/accounts/123")
     * @return full URL string
     */
    public static String apiUrl(String path) {
        return API_BASE_URL + path;
    }

    /**
     * Returns the full portal URL for the given page path.
     *
     * @param path relative path (e.g. "/dashboard")
     * @return full URL string
     */
    public static String portalUrl(String path) {
        return BASE_URL + path;
    }
}
