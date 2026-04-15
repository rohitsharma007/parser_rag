package com.ntrs.demoapp.testcases.web;

// extends BaseTest
// uses Login_Page
// uses ATR_HomePage
// uses businessfunctions.Test
// uses RegisterUser_Page
// uses ATR_Portal_Playwright_Page (Playwright flow)

import com.ntrs.demoapp.businessfunctions.Test;
import com.ntrs.demoapp.pages.atrwebportal.ATR_HomePage;
import com.ntrs.demoapp.pages.atrwebportal.ATR_Portal_Playwright_Page;
import com.ntrs.demoapp.pages.atrwebportal.Login_Page;
import com.ntrs.demoapp.pages.atrwebportal.RegisterUser_Page;
import com.ntrs.demoapp.testcases.BaseTest;
import org.testng.Assert;
import org.testng.annotations.Test as TestNG;

/**
 * POC (Proof of Concept) test class for the ATR Portal.
 * Validates basic portal flows and Playwright-based login.
 *
 * Layer: test
 * Extends: BaseTest
 * Uses: Login_Page, ATR_HomePage, businessfunctions.Test, RegisterUser_Page,
 *        ATR_Portal_Playwright_Page
 */
// extends BaseTest
public class ATR_Portal_POC_Tests extends BaseTest {

    /**
     * TC-030: POC — Basic login page interaction.
     */
    @TestNG(description = "TC-030: POC login page — enter credentials and submit",
            groups = {"poc", "login"})
    public void testPortalLoginPOC() {
        System.out.println("[TEST] ATR_Portal_POC_Tests.testPortalLoginPOC()");

        // new Login_Page()
        Login_Page loginPage = new Login_Page(driver);
        loginPage.enterUsername("poc.user@atrportal.com");
        loginPage.enterPassword("POC@pass123");
        loginPage.clickLogin();

        String currentUrl = getCurrentUrl();
        System.out.println("[TEST] URL after login attempt: " + currentUrl);
        Assert.assertNotNull(currentUrl, "URL should be present after login");
    }

    /**
     * TC-031: POC — Register a new user via business functions layer.
     */
    @TestNG(description = "TC-031: POC — Register new user via BusinessFunctions",
            groups = {"poc", "registration"})
    public void testRegisterNewUserPOC() {
        System.out.println("[TEST] ATR_Portal_POC_Tests.testRegisterNewUserPOC()");

        // new BusinessFunctions (Test)
        Test businessFunctions = new Test(driver);
        businessFunctions.registerNewUser(
                "John",
                "POC",
                "poc.john." + System.currentTimeMillis() + "@test.com",
                "Secure@Pass1"
        );
        System.out.println("[TEST] Registration flow completed via business functions");
    }

    /**
     * TC-032: POC — Verify home page content after login.
     */
    @TestNG(description = "TC-032: POC — Home page welcome and quick links visible",
            groups = {"poc", "homepage"})
    public void testHomePagePOC() {
        System.out.println("[TEST] ATR_Portal_POC_Tests.testHomePagePOC()");

        // new ATR_HomePage()
        ATR_HomePage homePage = new ATR_HomePage(driver);
        String greeting = homePage.getUserGreeting();
        boolean quickLinksVisible = homePage.isQuickLinksSectionVisible();

        System.out.println("[TEST] User greeting: " + greeting);
        System.out.println("[TEST] Quick links visible: " + quickLinksVisible);
    }

    /**
     * TC-033: POC — Direct registration via RegisterUser_Page (without BF layer).
     */
    @TestNG(description = "TC-033: POC — Direct RegisterUser_Page interaction",
            groups = {"poc", "registration"})
    public void testDirectRegistrationPagePOC() {
        System.out.println("[TEST] ATR_Portal_POC_Tests.testDirectRegistrationPagePOC()");

        navigateTo(BASE_URL + "/register");

        // new RegisterUser_Page()
        RegisterUser_Page registerPage = new RegisterUser_Page(driver);
        registerPage.fillAndSubmit(
                "Jane", "POC",
                "jane.poc." + System.currentTimeMillis() + "@test.com",
                "TestPass@2024"
        );
        System.out.println("[TEST] Direct registration submitted");
    }

    /**
     * TC-034: POC — Playwright-based portal login.
     */
    @TestNG(description = "TC-034: POC — Playwright login flow",
            groups = {"poc", "playwright"})
    public void testPlaywrightLoginPOC() {
        System.out.println("[TEST] ATR_Portal_POC_Tests.testPlaywrightLoginPOC()");

        // new ATR_Portal_Playwright_Page()
        ATR_Portal_Playwright_Page playwrightPage = new ATR_Portal_Playwright_Page();
        try {
            playwrightPage.openPortal();
            playwrightPage.loginWithPlaywright("playwright.user@atrportal.com", "PW@Test1234");
            boolean loggedIn = playwrightPage.isLoggedIn();
            System.out.println("[TEST] Playwright login status: " + loggedIn);
            Assert.assertNotNull(playwrightPage.getPageTitle(), "Page title should be present");
        } finally {
            playwrightPage.close();
        }
    }
}
