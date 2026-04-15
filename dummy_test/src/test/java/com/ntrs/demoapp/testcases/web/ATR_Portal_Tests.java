package com.ntrs.demoapp.testcases.web;

// extends BaseTest
// uses businessfunctions.Test (orchestration)
// uses Login_Page
// uses Navigation_Page
// uses ATR_HomePage
// Flow 1: Login + Navigation

import com.ntrs.demoapp.businessfunctions.Test;
import com.ntrs.demoapp.pages.atrwebportal.ATR_HomePage;
import com.ntrs.demoapp.pages.atrwebportal.Login_Page;
import com.ntrs.demoapp.pages.atrwebportal.Navigation_Page;
import com.ntrs.demoapp.testcases.BaseTest;
import org.testng.Assert;
import org.testng.annotations.Test as TestNG;

/**
 * Test class: ATR Portal — Login and Navigation flows.
 * All tests extend BaseTest for WebDriver lifecycle management.
 *
 * Layer: test
 * Extends: BaseTest
 * Uses: businessfunctions.Test, Login_Page, Navigation_Page, ATR_HomePage
 */
// extends BaseTest
public class ATR_Portal_Tests extends BaseTest {

    // ──────────────────────────────────────────────────────────────────────────
    // Flow 1: Login + Navigation (via Business Functions)
    // ──────────────────────────────────────────────────────────────────────────

    /**
     * TC-001: End-to-end login and dashboard navigation using business functions layer.
     */
    @TestNG(description = "TC-001: Login and navigate to dashboard via BusinessFunctions",
            groups = {"smoke", "login"})
    public void testLoginFlow() {
        System.out.println("[TEST] ATR_Portal_Tests.testLoginFlow()");

        // new BusinessFunctions (Test)
        Test businessFunctions = new Test(driver);
        businessFunctions.loginAndNavigate("testuser@atrportal.com", "Test@1234");

        Assert.assertTrue(getCurrentUrl().contains("dashboard"),
                "Should be on dashboard after login");
    }

    /**
     * TC-002: Direct login page interaction without business functions layer.
     */
    @TestNG(description = "TC-002: Direct Login_Page and Navigation_Page interaction",
            groups = {"smoke", "login"})
    public void testDirectLoginPage() {
        System.out.println("[TEST] ATR_Portal_Tests.testDirectLoginPage()");

        // new Login_Page()
        Login_Page loginPage = new Login_Page(driver);
        loginPage.enterUsername("admin@atrportal.com");
        loginPage.enterPassword("Admin@1234");
        loginPage.clickLogin();

        // new Navigation_Page()
        Navigation_Page nav = new Navigation_Page(driver);
        nav.goToDashboard();

        Assert.assertFalse(loginPage.isErrorDisplayed(),
                "No login error should be shown for valid credentials");
    }

    /**
     * TC-003: Login via certificate token (SSO) and verify home page welcome message.
     */
    @TestNG(description = "TC-003: Certificate SSO login and home page verification",
            groups = {"regression", "login"})
    public void testHomePageAfterLogin() {
        System.out.println("[TEST] ATR_Portal_Tests.testHomePageAfterLogin()");

        // uses businessfunctions.Test
        Test businessFunctions = new Test(driver);
        businessFunctions.loginWithCertificate("ssouser@atrportal.com");

        // new ATR_HomePage()
        ATR_HomePage homePage = new ATR_HomePage(driver);
        String welcomeMsg = homePage.getWelcomeMessage();
        System.out.println("[TEST] Welcome message: " + welcomeMsg);

        Assert.assertNotNull(welcomeMsg, "Welcome message should be present after login");
        Assert.assertTrue(homePage.isQuickLinksSectionVisible(),
                "Quick links section should be visible on home page");
    }

    /**
     * TC-004: Login with invalid credentials — verify error message is shown.
     */
    @TestNG(description = "TC-004: Invalid credentials show login error",
            groups = {"regression", "negative"})
    public void testLoginWithInvalidCredentials() {
        System.out.println("[TEST] ATR_Portal_Tests.testLoginWithInvalidCredentials()");

        // new Login_Page()
        Login_Page loginPage = new Login_Page(driver);
        loginPage.enterUsername("invalid@atrportal.com");
        loginPage.enterPassword("WrongPassword!");
        loginPage.clickLogin();

        Assert.assertTrue(loginPage.isErrorDisplayed(),
                "Login error message should be displayed for invalid credentials");
    }
}
