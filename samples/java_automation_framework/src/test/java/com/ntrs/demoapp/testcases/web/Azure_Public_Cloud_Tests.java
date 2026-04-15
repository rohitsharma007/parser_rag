package com.ntrs.demoapp.testcases.web;

// extends BaseTest
// uses Azure_Cloud_Page (UI)
// uses Adu_Saas_Page (API)
// uses Core_Reference_Page (API)
// uses FinancialCalculators_Perfecto_Page (bonus)
// Flow 5: Cloud Validation

import com.ntrs.demoapp.pages.api.Adu_Saas_Page;
import com.ntrs.demoapp.pages.api.Core_Reference_Page;
import com.ntrs.demoapp.pages.atrwebportal.Azure_Cloud_Page;
import com.ntrs.demoapp.pages.atrwebportal.FinancialCalculators_Perfecto_Page;
import com.ntrs.demoapp.testcases.BaseTest;
import org.testng.Assert;
import org.testng.annotations.Test as TestNG;

import java.util.List;
import java.util.Map;

/**
 * Test class: Azure Public Cloud — Cloud deployment validation and SaaS API tests.
 * Covers Flow 5: Cloud Validation (UI + API mix).
 *
 * Layer: test
 * Extends: BaseTest
 * Uses: Azure_Cloud_Page, Adu_Saas_Page, Core_Reference_Page, FinancialCalculators_Perfecto_Page
 */
// extends BaseTest
public class Azure_Public_Cloud_Tests extends BaseTest {

    // ──────────────────────────────────────────────────────────────────────────
    // Flow 5: Cloud Validation (API + UI mix)
    // ──────────────────────────────────────────────────────────────────────────

    /**
     * TC-050: Configure Azure deployment via UI page (which calls Adu_Saas_Page + Core_Reference APIs).
     */
    @TestNG(description = "TC-050: Configure Azure deployment via UI + ADU SaaS API",
            groups = {"cloud", "regression"})
    public void testAzureDeploymentConfig() {
        System.out.println("[TEST] Azure_Public_Cloud_Tests.testAzureDeploymentConfig()");

        String tenantId = "tenant-" + System.currentTimeMillis();
        String subscriptionId = "sub-abc123-" + System.currentTimeMillis();

        // new Azure_Cloud_Page() — internally calls Adu_Saas_Page and Core_Reference_Page
        Azure_Cloud_Page azurePage = new Azure_Cloud_Page(driver);
        azurePage.enterResourceGroup("rg-automation-test");
        azurePage.selectRegion("US-EAST");
        azurePage.configureAzureDeployment(tenantId, subscriptionId);

        String status = azurePage.getDeploymentStatus();
        System.out.println("[TEST] Deployment status: " + status);
        Assert.assertNotNull(status, "Deployment status should be returned");
    }

    /**
     * TC-051: Verify core reference data is fetched correctly for cloud configuration.
     */
    @TestNG(description = "TC-051: Core reference data API returns valid region list",
            groups = {"cloud", "api"})
    public void testCoreReferenceData() {
        System.out.println("[TEST] Azure_Public_Cloud_Tests.testCoreReferenceData()");

        // new Core_Reference_Page()
        Core_Reference_Page coreRefPage = new Core_Reference_Page();
        List<String> regions = coreRefPage.getReferenceData("REGIONS");

        System.out.println("[TEST] Regions returned: " + regions);
        Assert.assertNotNull(regions, "Regions list should not be null");
        Assert.assertFalse(regions.isEmpty(), "Regions list should not be empty");
    }

    /**
     * TC-052: Provision an ADU SaaS instance and verify its status via API.
     */
    @TestNG(description = "TC-052: Provision ADU SaaS instance via API and check status",
            groups = {"cloud", "api"})
    public void testAduSaasProvisioning() {
        System.out.println("[TEST] Azure_Public_Cloud_Tests.testAduSaasProvisioning()");

        // new Adu_Saas_Page()
        Adu_Saas_Page aduSaasPage = new Adu_Saas_Page();
        String instanceId = aduSaasPage.provisionAduSaasInstance("cloud-tenant-001", "ENTERPRISE");
        Assert.assertNotNull(instanceId, "Instance ID should not be null after provisioning");

        String status = aduSaasPage.getSaasStatus(instanceId);
        System.out.println("[TEST] SaaS instance status: " + status);
        Assert.assertEquals(status, "RUNNING", "Newly provisioned instance should be RUNNING");
    }

    /**
     * TC-053: Update SaaS instance configuration and verify no exceptions thrown.
     */
    @TestNG(description = "TC-053: Update SaaS configuration via API",
            groups = {"cloud", "api"})
    public void testUpdateSaasConfiguration() {
        System.out.println("[TEST] Azure_Public_Cloud_Tests.testUpdateSaasConfiguration()");

        // new Adu_Saas_Page()
        Adu_Saas_Page aduSaasPage = new Adu_Saas_Page();
        String instanceId = aduSaasPage.provisionAduSaasInstance("config-tenant-002", "PREMIUM");

        boolean updated = aduSaasPage.updateSaasConfiguration(instanceId, "maxConnections", "100");
        Assert.assertTrue(updated, "Configuration update should return true");
    }

    /**
     * TC-054: Verify Azure UI page can query ADU SaaS status.
     */
    @TestNG(description = "TC-054: Azure_Cloud_Page verifyAduSaasStatus delegates to API",
            groups = {"cloud", "regression"})
    public void testAzurePageSaasStatusCheck() {
        System.out.println("[TEST] Azure_Public_Cloud_Tests.testAzurePageSaasStatusCheck()");

        // new Azure_Cloud_Page()
        Azure_Cloud_Page azurePage = new Azure_Cloud_Page(driver);
        String status = azurePage.verifyAduSaasStatus("instance-check-001");
        System.out.println("[TEST] ADU SaaS status via Azure UI page: " + status);
        Assert.assertNotNull(status, "Status should not be null");
    }

    /**
     * TC-055: Bonus — Financial calculator test via Perfecto page.
     */
    @TestNG(description = "TC-055: Bonus — Financial calculator via FinancialCalculators_Perfecto_Page",
            groups = {"cloud", "perfecto"})
    public void testFinancialCalculatorPerfecto() {
        System.out.println("[TEST] Azure_Public_Cloud_Tests.testFinancialCalculatorPerfecto()");

        // new FinancialCalculators_Perfecto_Page()
        FinancialCalculators_Perfecto_Page calcPage = new FinancialCalculators_Perfecto_Page(driver);
        double interest = calcPage.calculateInterest(10000.0, 5.5, 3);
        System.out.println("[TEST] Calculated interest: " + interest);
        Assert.assertTrue(interest >= 0, "Interest result should be a non-negative number");
    }
}
