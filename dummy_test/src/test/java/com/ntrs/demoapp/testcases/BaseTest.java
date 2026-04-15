package com.ntrs.demoapp.testcases;

import org.openqa.selenium.WebDriver;
import org.openqa.selenium.chrome.ChromeDriver;
import org.openqa.selenium.chrome.ChromeOptions;
import org.openqa.selenium.firefox.FirefoxDriver;
import org.testng.annotations.AfterMethod;
import org.testng.annotations.BeforeMethod;
import org.testng.annotations.Optional;
import org.testng.annotations.Parameters;

/**
 * Base test class for all Selenium WebDriver tests.
 * Initialises and tears down the WebDriver session.
 * All web test classes extend this class.
 *
 * Layer: base (testcases)
 * Extended by: BaseTestAppium, all testcases/web/* test classes
 */
public class BaseTest {

    /** Shared WebDriver instance, accessible to all subclasses. */
    protected WebDriver driver;

    /** Default portal URL — overridden via TestNG parameter if needed. */
    protected static final String BASE_URL = "https://demo.atrwebportal.com";

    /**
     * Initialises the WebDriver before each test method.
     * Browser defaults to Chrome; pass browser="firefox" as a TestNG parameter to switch.
     *
     * @param browser optional browser name ("chrome" or "firefox"), defaults to "chrome"
     */
    @BeforeMethod
    @Parameters({"browser"})
    public void setup(@Optional("chrome") String browser) {
        System.out.println("[BaseTest] setup() — browser=" + browser);

        if ("firefox".equalsIgnoreCase(browser)) {
            driver = new FirefoxDriver();
        } else {
            ChromeOptions options = new ChromeOptions();
            options.addArguments("--start-maximized");
            options.addArguments("--disable-notifications");
            driver = new ChromeDriver(options);
        }

        driver.manage().window().maximize();
        driver.manage().deleteAllCookies();
        driver.get(BASE_URL);
        System.out.println("[BaseTest] Browser opened: " + BASE_URL);
    }

    /**
     * Quits the WebDriver after each test method, regardless of outcome.
     */
    @AfterMethod
    public void teardown() {
        System.out.println("[BaseTest] teardown() — closing browser");
        if (driver != null) {
            driver.quit();
            driver = null;
        }
    }

    /**
     * Returns the current page title from the active browser window.
     *
     * @return page title string
     */
    protected String getPageTitle() {
        return driver.getTitle();
    }

    /**
     * Returns the current URL of the browser.
     *
     * @return current URL string
     */
    protected String getCurrentUrl() {
        return driver.getCurrentUrl();
    }

    /**
     * Navigates the browser to the given URL.
     *
     * @param url the URL to open
     */
    protected void navigateTo(String url) {
        System.out.println("[BaseTest] navigating to: " + url);
        driver.get(url);
    }
}
