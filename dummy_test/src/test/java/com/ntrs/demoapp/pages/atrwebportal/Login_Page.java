package com.ntrs.demoapp.pages.atrwebportal;

import com.ntrs.demoapp.pages.api.Get_CertificateToken_Page;
import org.openqa.selenium.By;
import org.openqa.selenium.WebDriver;
import org.openqa.selenium.WebElement;
import org.openqa.selenium.support.ui.ExpectedConditions;
import org.openqa.selenium.support.ui.WebDriverWait;

import java.time.Duration;

/**
 * UI Page: Login screen for the ATR Web Portal.
 * Calls Get_CertificateToken_Page to support certificate-based (SSO) login.
 *
 * Layer: ui (atrwebportal)
 * Depends on: Get_CertificateToken_Page (api layer)
 * Used by: businessfunctions.Test, ATR_Portal_Tests, ATR_Portal_POC_Tests
 */
public class Login_Page {

    private WebDriver driver;

    // calls Get_CertificateToken_Page for SSO token-based login
    private Get_CertificateToken_Page tokenPage;

    // Locators
    private final By usernameField     = By.id("username");
    private final By passwordField     = By.id("password");
    private final By loginButton       = By.id("loginBtn");
    private final By errorMessage      = By.id("loginError");
    private final By forgotPasswordLink = By.id("forgotPassword");
    private final By rememberMeCheckbox = By.id("rememberMe");

    public Login_Page(WebDriver driver) {
        this.driver = driver;
        this.tokenPage = new Get_CertificateToken_Page();
    }

    /**
     * Enters the username into the username field.
     *
     * @param username the user's email or login name
     */
    public void enterUsername(String username) {
        WebElement field = driver.findElement(usernameField);
        field.clear();
        field.sendKeys(username);
        System.out.println("[UI] Entered username: " + username);
    }

    /**
     * Enters the password into the password field.
     *
     * @param password the user's password
     */
    public void enterPassword(String password) {
        WebElement field = driver.findElement(passwordField);
        field.clear();
        field.sendKeys(password);
        System.out.println("[UI] Entered password: ****");
    }

    /**
     * Clicks the Login button to submit credentials.
     */
    public void clickLogin() {
        System.out.println("[UI] Clicking Login button");
        driver.findElement(loginButton).click();
    }

    /**
     * Full login helper: enters credentials and submits.
     *
     * @param username the login username
     * @param password the login password
     */
    public void login(String username, String password) {
        enterUsername(username);
        enterPassword(password);
        clickLogin();
    }

    /**
     * Certificate-based (SSO) login flow.
     * Fetches a token from Get_CertificateToken_Page and uses it for login.
     *
     * @param username the user for whom to fetch a certificate token
     */
    public void loginWithToken(String username) {
        String token = tokenPage.fetchCertificateToken(username);
        System.out.println("[UI] SSO login with token: " + token);
        enterUsername(username);
        // Token is passed via hidden field or header in a real impl
        clickLogin();
    }

    /**
     * Returns the text of the login error message element.
     *
     * @return error message string, or empty string if not present
     */
    public String getLoginErrorMessage() {
        try {
            return driver.findElement(errorMessage).getText();
        } catch (Exception e) {
            return "";
        }
    }

    /**
     * Checks whether the login error message is displayed.
     *
     * @return true if error element is visible
     */
    public boolean isErrorDisplayed() {
        return driver.findElements(errorMessage).size() > 0
                && driver.findElement(errorMessage).isDisplayed();
    }

    /**
     * Clicks the "Forgot Password" link.
     */
    public void clickForgotPassword() {
        System.out.println("[UI] Clicking Forgot Password link");
        driver.findElement(forgotPasswordLink).click();
    }
}
