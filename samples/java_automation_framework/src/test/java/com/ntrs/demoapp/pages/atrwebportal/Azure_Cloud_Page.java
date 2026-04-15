package com.ntrs.demoapp.pages.atrwebportal;

import com.ntrs.demoapp.pages.api.Adu_Saas_Page;
import com.ntrs.demoapp.pages.api.Core_Reference_Page;
import org.openqa.selenium.By;
import org.openqa.selenium.WebDriver;
import org.openqa.selenium.WebElement;

/**
 * UI Page: Azure Public Cloud configuration and deployment screen.
 * Calls Adu_Saas_Page (API) to provision the SaaS instance, and
 * Core_Reference_Page (API) to fetch deployment configuration.
 * Used in Flow 5 (Cloud Validation).
 *
 * Layer: ui (atrwebportal)
 * Depends on: Adu_Saas_Page (api), Core_Reference_Page (api)
 * Used by: Azure_Public_Cloud_Tests
 */
public class Azure_Cloud_Page {

    private WebDriver driver;

    // calls Adu_Saas_Page API for SaaS provisioning
    private Adu_Saas_Page aduSaasApi;

    // calls Core_Reference_Page API for deployment config
    private Core_Reference_Page coreRefApi;

    // Locators
    private final By subscriptionField  = By.id("azure-subscription");
    private final By resourceGroupField = By.id("resource-group");
    private final By regionDropdown     = By.id("azure-region");
    private final By deployBtn          = By.id("deployToAzure");
    private final By statusLabel        = By.id("deployment-status");
    private final By tenantIdField      = By.id("tenant-id");
    private final By connectionTestBtn  = By.id("testAzureConnection");

    public Azure_Cloud_Page(WebDriver driver) {
        this.driver = driver;
        // new Adu_Saas_Page()
        this.aduSaasApi = new Adu_Saas_Page();
        // new Core_Reference_Page()
        this.coreRefApi = new Core_Reference_Page();
    }

    /**
     * Configures and deploys to Azure. Provisions a SaaS instance via API first,
     * fetches deployment config, then fills in the UI form.
     *
     * @param tenantId       Azure tenant ID
     * @param subscriptionId Azure subscription ID
     */
    public void configureAzureDeployment(String tenantId, String subscriptionId) {
        // calls Adu_Saas_Page API
        String instanceId = aduSaasApi.provisionAduSaasInstance(tenantId, "PREMIUM");
        System.out.println("[UI] SaaS instance provisioned: " + instanceId);

        // calls Core_Reference_Page API
        String deployConfig = coreRefApi.getCoreConfiguration("AZURE_DEPLOY_CONFIG");
        System.out.println("[UI] Deployment config: " + deployConfig);

        System.out.println("[UI] Filling Azure deployment form: tenantId=" + tenantId);
        driver.findElement(tenantIdField).sendKeys(tenantId);
        driver.findElement(subscriptionField).sendKeys(subscriptionId);
        driver.findElement(deployBtn).click();
        System.out.println("[UI] Azure deployment initiated");
    }

    /**
     * Returns the current deployment status from the status label.
     *
     * @return status text (e.g. "IN_PROGRESS", "SUCCESS", "FAILED")
     */
    public String getDeploymentStatus() {
        return driver.findElement(statusLabel).getText();
    }

    /**
     * Enters a resource group name into the form field.
     *
     * @param resourceGroup Azure resource group name
     */
    public void enterResourceGroup(String resourceGroup) {
        System.out.println("[UI] Entering resource group: " + resourceGroup);
        WebElement field = driver.findElement(resourceGroupField);
        field.clear();
        field.sendKeys(resourceGroup);
    }

    /**
     * Selects an Azure region from the dropdown.
     *
     * @param region region code (e.g. "US-EAST", "EU-CENTRAL")
     */
    public void selectRegion(String region) {
        System.out.println("[UI] Selecting Azure region: " + region);
        driver.findElement(regionDropdown).sendKeys(region);
    }

    /**
     * Clicks the "Test Connection" button to verify Azure credentials.
     */
    public void testAzureConnection() {
        System.out.println("[UI] Testing Azure connection");
        driver.findElement(connectionTestBtn).click();
    }

    /**
     * Verifies ADU SaaS instance status by calling the API.
     *
     * @param instanceId the instance to check
     * @return status string from Adu_Saas_Page API
     */
    public String verifyAduSaasStatus(String instanceId) {
        // calls Adu_Saas_Page API
        return aduSaasApi.getSaasStatus(instanceId);
    }
}
