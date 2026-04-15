package com.ntrs.demoapp.pages.atrwebportal;

import com.microsoft.playwright.Page;

/**
 * Playwright-based Login Page for the ATR portal.
 * Used exclusively by ATR_Portal_Playwright_Page for browser-less / headless login flows.
 *
 * Layer: ui (atrwebportal)
 * Depends on: com.microsoft.playwright.Page
 * Used by: ATR_Portal_Playwright_Page
 */
public class Login_Playwright_Page {

    private Page page;

    // Playwright selectors
    private static final String USERNAME_SELECTOR        = "#username";
    private static final String PASSWORD_SELECTOR        = "#password";
    private static final String LOGIN_BTN_SELECTOR       = "#loginBtn";
    private static final String ERROR_MSG_SELECTOR       = "#loginError";
    private static final String DASHBOARD_URL_PATTERN    = "**/dashboard";

    public Login_Playwright_Page(Page page) {
        this.page = page;
    }

    /**
     * Types into the username field.
     *
     * @param username the login email/name
     */
    public void enterUsername(String username) {
        System.out.println("[Playwright] Entering username: " + username);
        page.fill(USERNAME_SELECTOR, username);
    }

    /**
     * Types into the password field.
     *
     * @param password the login password
     */
    public void enterPassword(String password) {
        System.out.println("[Playwright] Entering password: ****");
        page.fill(PASSWORD_SELECTOR, password);
    }

    /**
     * Clicks the Login button.
     */
    public void clickLoginButton() {
        System.out.println("[Playwright] Clicking login button");
        page.click(LOGIN_BTN_SELECTOR);
    }

    /**
     * Full login sequence: fill credentials and click login,
     * then wait for the dashboard URL.
     *
     * @param username login email/name
     * @param password login password
     */
    public void performLogin(String username, String password) {
        System.out.println("[Playwright] Performing login for: " + username);
        enterUsername(username);
        enterPassword(password);
        clickLoginButton();
        page.waitForURL(DASHBOARD_URL_PATTERN);
        System.out.println("[Playwright] Login successful — redirected to dashboard");
    }

    /**
     * Returns true if the current URL contains "/dashboard".
     *
     * @return true if logged in
     */
    public boolean isLoggedIn() {
        return page.url().contains("/dashboard");
    }

    /**
     * Returns the login error message text if visible.
     *
     * @return error text or empty string
     */
    public String getErrorMessage() {
        try {
            return page.textContent(ERROR_MSG_SELECTOR);
        } catch (Exception e) {
            return "";
        }
    }
}
