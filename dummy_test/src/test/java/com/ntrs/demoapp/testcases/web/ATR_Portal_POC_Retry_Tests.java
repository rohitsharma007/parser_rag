package com.ntrs.demoapp.testcases.web;

// extends BaseTest
// uses RetryAnalyzer
// uses Login_Page
// uses Navigation_Page
// uses businessfunctions.Test
// Flow 4: Retry Scenario

import com.ntrs.demoapp.businessfunctions.Test;
import com.ntrs.demoapp.pages.atrwebportal.Login_Page;
import com.ntrs.demoapp.pages.atrwebportal.Navigation_Page;
import com.ntrs.demoapp.retryanalyzer.RetryAnalyzer;
import com.ntrs.demoapp.testcases.BaseTest;
import org.testng.Assert;
import org.testng.annotations.Test as TestNG;

/**
 * Test class: ATR Portal POC — Tests that use the RetryAnalyzer on flaky flows.
 * Covers Flow 4: Retry Scenario.
 *
 * Layer: test
 * Extends: BaseTest
 * Uses: RetryAnalyzer, Login_Page, Navigation_Page, businessfunctions.Test
 */
// extends BaseTest
public class ATR_Portal_POC_Retry_Tests extends BaseTest {

    /** Counter to simulate intermittent failure on first 2 attempts. */
    private int loginAttemptCount = 0;

    /** Counter to simulate intermittent navigation failure. */
    private int navAttemptCount = 0;

    // ──────────────────────────────────────────────────────────────────────────
    // Flow 4: Retry Scenario
    // ──────────────────────────────────────────────────────────────────────────

    /**
     * TC-040: Simulates a flaky login that fails on first attempt, succeeds on retry.
     * RetryAnalyzer retries up to 3 times.
     */
    @TestNG(description = "TC-040: Retry on flaky login flow",
            groups = {"retry", "login"},
            retryAnalyzer = RetryAnalyzer.class)
    public void testLoginWithRetry() {
        loginAttemptCount++;
        System.out.println("[TEST] ATR_Portal_POC_Retry_Tests.testLoginWithRetry() — attempt " + loginAttemptCount);

        // Simulate intermittent failure: fail on attempt 1
        if (loginAttemptCount == 1) {
            System.out.println("[TEST] Simulating intermittent failure on attempt " + loginAttemptCount);
            Assert.fail("Simulated intermittent failure — RetryAnalyzer should retry this");
        }

        // new Login_Page()
        Login_Page loginPage = new Login_Page(driver);
        loginPage.enterUsername("retry.user@atrportal.com");
        loginPage.enterPassword("Retry@1234");
        loginPage.clickLogin();

        System.out.println("[TEST] Login succeeded on attempt " + loginAttemptCount);
        Assert.assertFalse(loginPage.isErrorDisplayed(),
                "No error should be shown on successful login attempt");
    }

    /**
     * TC-041: Simulates a flaky navigation flow with retry support.
     */
    @TestNG(description = "TC-041: Retry on flaky navigation flow",
            groups = {"retry", "navigation"},
            retryAnalyzer = RetryAnalyzer.class)
    public void testNavigationWithRetry() {
        navAttemptCount++;
        System.out.println("[TEST] ATR_Portal_POC_Retry_Tests.testNavigationWithRetry() — attempt " + navAttemptCount);

        // new Navigation_Page()
        Navigation_Page navPage = new Navigation_Page(driver);

        // Simulate intermittent failure on first attempt
        if (navAttemptCount == 1) {
            System.out.println("[TEST] Simulating navigation timeout on attempt " + navAttemptCount);
            Assert.fail("Simulated navigation timeout — RetryAnalyzer should retry");
        }

        navPage.goToDashboard();
        System.out.println("[TEST] Navigation succeeded on attempt " + navAttemptCount);
    }

    /**
     * TC-042: Full business functions flow with retry — login + navigate via BF layer.
     */
    @TestNG(description = "TC-042: BusinessFunctions login+navigate with retry",
            groups = {"retry", "regression"},
            retryAnalyzer = RetryAnalyzer.class)
    public void testBusinessFunctionLoginWithRetry() {
        System.out.println("[TEST] ATR_Portal_POC_Retry_Tests.testBusinessFunctionLoginWithRetry()");

        // new BusinessFunctions (Test)
        Test businessFunctions = new Test(driver);
        businessFunctions.loginAndNavigate("retry.bf.user@atrportal.com", "BF@Retry1");

        System.out.println("[TEST] BusinessFunctions login+navigate with retry — passed");
    }

    /**
     * TC-043: Verify RetryAnalyzer configuration is correct.
     */
    @TestNG(description = "TC-043: Verify RetryAnalyzer max retry count",
            groups = {"utility"})
    public void testRetryAnalyzerConfiguration() {
        System.out.println("[TEST] ATR_Portal_POC_Retry_Tests.testRetryAnalyzerConfiguration()");

        int maxRetries = RetryAnalyzer.getMaxRetryCount();
        System.out.println("[TEST] RetryAnalyzer max retries: " + maxRetries);
        Assert.assertEquals(maxRetries, 3,
                "RetryAnalyzer should be configured for 3 max retries");
    }
}
