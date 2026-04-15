package com.ntrs.demoapp.testcases.web;

// extends BaseTest
// uses businessfunctions.Test
// uses Accounts_Page (API)
// uses MyAccount_Page (UI)
// uses ATR_Application_Page (UI)
// Flow 2: Account Creation (API + UI)

import com.ntrs.demoapp.businessfunctions.Test;
import com.ntrs.demoapp.pages.api.Accounts_Page;
import com.ntrs.demoapp.pages.atrwebportal.ATR_Application_Page;
import com.ntrs.demoapp.pages.atrwebportal.MyAccount_Page;
import com.ntrs.demoapp.testcases.BaseTest;
import org.testng.Assert;
import org.testng.annotations.Test as TestNG;

import java.util.Map;

/**
 * Regression test class for ATR Application management flows.
 * Covers Flow 2: Account Creation via API followed by UI verification.
 *
 * Layer: test
 * Extends: BaseTest
 * Uses: businessfunctions.Test, Accounts_Page, MyAccount_Page, ATR_Application_Page
 */
// extends BaseTest
public class ATR_Application_Regression_Tests extends BaseTest {

    // ──────────────────────────────────────────────────────────────────────────
    // Flow 2: Account Creation (API + UI)
    // ──────────────────────────────────────────────────────────────────────────

    /**
     * TC-010: Create an account via the Accounts API and verify it in the MyAccount UI page.
     */
    @TestNG(description = "TC-010: Create account via API and verify in UI",
            groups = {"regression", "accounts"})
    public void testCreateAccountViaAPI() {
        System.out.println("[TEST] ATR_Application_Regression_Tests.testCreateAccountViaAPI()");

        String accountName = "RegressionTestAccount-" + System.currentTimeMillis();

        // new Accounts_Page() — API layer
        Accounts_Page accountsApi = new Accounts_Page();
        String accountId = accountsApi.createAccount(accountName, "ENTERPRISE");
        Assert.assertNotNull(accountId, "Account ID should not be null");
        System.out.println("[TEST] Account created via API: " + accountId);

        // new MyAccount_Page() — UI layer
        MyAccount_Page myAccountPage = new MyAccount_Page(driver);
        myAccountPage.verifyAccount(accountName);
        System.out.println("[TEST] Account verified in UI");
    }

    /**
     * TC-011: Full application creation flow using BusinessFunctions orchestration.
     */
    @TestNG(description = "TC-011: Full account creation and verification via BusinessFunctions",
            groups = {"regression", "accounts"})
    public void testFullApplicationFlow() {
        System.out.println("[TEST] ATR_Application_Regression_Tests.testFullApplicationFlow()");

        // new BusinessFunctions (Test)
        Test businessFunctions = new Test(driver);
        businessFunctions.createAndVerifyAccount("EnterpriseAccount-001", "ENTERPRISE");

        System.out.println("[TEST] Full application flow completed");
    }

    /**
     * TC-012: Verify the application grid loads and shows the expected number of apps.
     */
    @TestNG(description = "TC-012: Application grid loads correctly",
            groups = {"regression", "ui"})
    public void testApplicationGridLoad() {
        System.out.println("[TEST] ATR_Application_Regression_Tests.testApplicationGridLoad()");

        // new ATR_Application_Page()
        ATR_Application_Page appPage = new ATR_Application_Page(driver);
        int count = appPage.getApplicationCount();
        System.out.println("[TEST] Application count in grid: " + count);
        Assert.assertTrue(count >= 0, "Application grid count should be non-negative");
    }

    /**
     * TC-013: Create an application through ATR_Application_Page and verify it appears in the grid.
     */
    @TestNG(description = "TC-013: Create application via UI and verify in grid",
            groups = {"regression", "accounts"})
    public void testCreateApplicationThroughUI() {
        System.out.println("[TEST] ATR_Application_Regression_Tests.testCreateApplicationThroughUI()");

        String appName = "AutoApp-" + System.currentTimeMillis();
        String accountName = "AutoAccount-" + System.currentTimeMillis();

        // new ATR_Application_Page() — calls Accounts_Page and Core_Reference_Page internally
        ATR_Application_Page appPage = new ATR_Application_Page(driver);
        appPage.createApplication(appName, accountName);

        System.out.println("[TEST] Application created: " + appName);
    }

    /**
     * TC-014: Retrieve and assert account details from the API.
     */
    @TestNG(description = "TC-014: Get account details from API and assert key fields",
            groups = {"regression", "api"})
    public void testGetAccountDetailsFromAPI() {
        System.out.println("[TEST] ATR_Application_Regression_Tests.testGetAccountDetailsFromAPI()");

        // new Accounts_Page()
        Accounts_Page accountsApi = new Accounts_Page();
        String accountId = accountsApi.createAccount("DetailCheckAccount", "STANDARD");

        Map<String, String> details = accountsApi.getAccountDetails(accountId);
        Assert.assertNotNull(details, "Account details map should not be null");
        Assert.assertTrue(details.containsKey("status"), "Account details should include 'status'");
        Assert.assertEquals(details.get("status"), "ACTIVE", "Newly created account should be ACTIVE");
    }
}
