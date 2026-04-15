package com.ntrs.demoapp.pages.atrwebportal;

import com.microsoft.playwright.Browser;
import com.microsoft.playwright.BrowserContext;
import com.microsoft.playwright.BrowserType;
import com.microsoft.playwright.Page;
import com.microsoft.playwright.Playwright;

/**
 * Playwright-based page wrapper for the ATR Portal.
 * Manages Playwright lifecycle and delegates login to Login_Playwright_Page.
 *
 * Layer: ui (atrwebportal)
 * Depends on: Login_Playwright_Page
 * Used by: ATR_Portal_POC_Tests
 */
public class ATR_Portal_Playwright_Page {

    private Playwright playwright;
    private Browser browser;
    private BrowserContext context;
    private Page page;

    // uses Login_Playwright_Page for authentication
    private Login_Playwright_Page loginPlaywrightPage;

    private static final String BASE_URL = "https://demo.atrwebportal.com";

    public ATR_Portal_Playwright_Page() {
        this.playwright = Playwright.create();
        this.browser = playwright.chromium().launch(
                new BrowserType.LaunchOptions().setHeadless(true)
        );
        this.context = browser.newContext();
        this.page = context.newPage();
        // new Login_Playwright_Page()
        this.loginPlaywrightPage = new Login_Playwright_Page(page);
    }

    /**
     * Navigates to the given URL in the Playwright browser.
     *
     * @param url the full URL to navigate to
     */
    public void navigateTo(String url) {
        System.out.println("[Playwright] Navigating to: " + url);
        page.navigate(url);
    }

    /**
     * Navigates to the portal base URL.
     */
    public void openPortal() {
        navigateTo(BASE_URL);
    }

    /**
     * Performs login using the Login_Playwright_Page helper.
     *
     * @param username login email/name
     * @param password login password
     */
    public void loginWithPlaywright(String username, String password) {
        // uses Login_Playwright_Page
        loginPlaywrightPage.performLogin(username, password);
    }

    /**
     * Returns the current page's <title> text.
     *
     * @return page title string
     */
    public String getPageTitle() {
        return page.title();
    }

    /**
     * Returns the current page URL.
     *
     * @return URL string
     */
    public String getCurrentUrl() {
        return page.url();
    }

    /**
     * Takes a screenshot and saves it to the given path.
     *
     * @param filePath destination path for the screenshot PNG
     */
    public void takeScreenshot(String filePath) {
        System.out.println("[Playwright] Taking screenshot: " + filePath);
        page.screenshot(new Page.ScreenshotOptions().setPath(java.nio.file.Paths.get(filePath)));
    }

    /**
     * Returns true if the login flow completed successfully.
     *
     * @return true if on the dashboard
     */
    public boolean isLoggedIn() {
        return loginPlaywrightPage.isLoggedIn();
    }

    /**
     * Closes the browser and Playwright engine.
     */
    public void close() {
        System.out.println("[Playwright] Closing browser and Playwright context");
        if (context != null) context.close();
        if (browser != null) browser.close();
        if (playwright != null) playwright.close();
    }
}
