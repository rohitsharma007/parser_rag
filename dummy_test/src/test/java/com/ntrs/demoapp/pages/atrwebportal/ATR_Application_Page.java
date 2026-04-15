package com.ntrs.demoapp.pages.atrwebportal;

import com.ntrs.demoapp.pages.api.Accounts_Page;
import com.ntrs.demoapp.pages.api.Core_Reference_Page;
import org.openqa.selenium.By;
import org.openqa.selenium.WebDriver;
import org.openqa.selenium.WebElement;

import java.util.List;

/**
 * UI Page: ATR Application management grid — create, select, and manage applications.
 * Calls Accounts_Page (API) to create the backing account, and
 * Core_Reference_Page (API) to fetch valid application type values.
 *
 * Layer: ui (atrwebportal)
 * Depends on: Accounts_Page (api), Core_Reference_Page (api)
 * Used by: ATR_Application_Regression_Tests
 */
public class ATR_Application_Page {

    private WebDriver driver;

    // calls Accounts_Page API to provision account before app creation
    private Accounts_Page accountsApi;

    // calls Core_Reference_Page API to fetch valid app type list
    private Core_Reference_Page coreRefApi;

    // Locators
    private final By applicationGrid  = By.id("app-grid");
    private final By createAppBtn     = By.id("createAppBtn");
    private final By appNameField     = By.id("appName");
    private final By appTypeDropdown  = By.id("appType");
    private final By saveAppBtn       = By.id("saveAppBtn");
    private final By appItems         = By.cssSelector("#app-grid .app-item");
    private final By searchAppsField  = By.id("searchApps");
    private final By deleteAppBtn     = By.id("deleteAppBtn");

    public ATR_Application_Page(WebDriver driver) {
        this.driver = driver;
        // new Accounts_Page()
        this.accountsApi = new Accounts_Page();
        // new Core_Reference_Page()
        this.coreRefApi = new Core_Reference_Page();
    }

    /**
     * Creates an application. First provisions an account via API,
     * then fetches valid app types, and finally fills in the UI form.
     *
     * @param appName     the name for the new application
     * @param accountName the account to associate with this app
     */
    public void createApplication(String appName, String accountName) {
        // calls Accounts_Page API
        String accountId = accountsApi.createAccount(accountName, "ENTERPRISE");
        System.out.println("[UI] Account provisioned for app creation: " + accountId);

        // calls Core_Reference_Page API
        List<String> appTypes = coreRefApi.getReferenceData("APP_TYPES");
        String selectedType = appTypes.isEmpty() ? "WEB" : appTypes.get(0);

        System.out.println("[UI] Creating application: name=" + appName + ", type=" + selectedType);
        driver.findElement(createAppBtn).click();
        driver.findElement(appNameField).sendKeys(appName);
        driver.findElement(saveAppBtn).click();
        System.out.println("[UI] Application '" + appName + "' created");
    }

    /**
     * Returns the number of application cards visible in the grid.
     *
     * @return count of app items
     */
    public int getApplicationCount() {
        return driver.findElements(appItems).size();
    }

    /**
     * Clicks an application card by its name.
     *
     * @param appName the application to select
     */
    public void selectApplication(String appName) {
        System.out.println("[UI] Selecting application: " + appName);
        driver.findElement(By.xpath("//div[contains(@class,'app-item') and .//text()='" + appName + "']"))
                .click();
    }

    /**
     * Searches for applications in the grid by keyword.
     *
     * @param keyword search text
     */
    public void searchApplications(String keyword) {
        System.out.println("[UI] Searching applications: " + keyword);
        WebElement search = driver.findElement(searchAppsField);
        search.clear();
        search.sendKeys(keyword);
    }

    /**
     * Deletes the currently selected application.
     */
    public void deleteSelectedApplication() {
        System.out.println("[UI] Deleting selected application");
        driver.findElement(deleteAppBtn).click();
    }
}
