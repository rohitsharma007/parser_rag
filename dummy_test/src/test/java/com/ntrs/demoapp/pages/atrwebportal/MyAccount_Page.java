package com.ntrs.demoapp.pages.atrwebportal;

import org.openqa.selenium.By;
import org.openqa.selenium.WebDriver;
import org.openqa.selenium.WebElement;
import org.testng.Assert;

/**
 * UI Page: MyAccount section — displays and manages the logged-in user's account info.
 * Used after API account creation to verify UI state (Flow 2).
 *
 * Layer: ui (atrwebportal)
 * Used by: businessfunctions.Test, ATR_Application_Regression_Tests
 */
public class MyAccount_Page {

    private WebDriver driver;

    // Locators
    private final By accountNameField  = By.id("account-name");
    private final By accountTypeField  = By.id("account-type");
    private final By accountStatusField = By.id("account-status");
    private final By editAccountBtn    = By.id("editAccount");
    private final By saveAccountBtn    = By.id("saveAccount");
    private final By cancelEditBtn     = By.id("cancelEdit");
    private final By profileSection    = By.id("profile-section");

    public MyAccount_Page(WebDriver driver) {
        this.driver = driver;
    }

    /**
     * Returns the account name displayed in the MyAccount section.
     *
     * @return account name text
     */
    public String getAccountName() {
        return driver.findElement(accountNameField).getText();
    }

    /**
     * Returns the account type label (e.g. "ENTERPRISE").
     *
     * @return account type text
     */
    public String getAccountType() {
        return driver.findElement(accountTypeField).getText();
    }

    /**
     * Returns the account status (e.g. "ACTIVE", "SUSPENDED").
     *
     * @return account status text
     */
    public String getAccountStatus() {
        return driver.findElement(accountStatusField).getText();
    }

    /**
     * Asserts that the account name matches the expected value.
     * Called by businessfunctions.Test.createAndVerifyAccount().
     *
     * @param expectedAccountName the name to verify
     */
    public void verifyAccount(String expectedAccountName) {
        System.out.println("[UI] Verifying account name: expected='" + expectedAccountName + "'");
        String actualName = getAccountName();
        System.out.println("[UI] Actual account name: '" + actualName + "'");
        Assert.assertEquals(actualName, expectedAccountName,
                "Account name mismatch on MyAccount page");
    }

    /**
     * Verifies the account status is "ACTIVE".
     */
    public void verifyAccountIsActive() {
        String status = getAccountStatus();
        System.out.println("[UI] Verifying account is ACTIVE, actual status: " + status);
        Assert.assertEquals(status, "ACTIVE", "Account should be ACTIVE");
    }

    /**
     * Clicks Edit, updates the account name, and saves.
     *
     * @param newName the updated account name
     */
    public void editAccountDetails(String newName) {
        System.out.println("[UI] Editing account: new name='" + newName + "'");
        driver.findElement(editAccountBtn).click();
        WebElement nameField = driver.findElement(accountNameField);
        nameField.clear();
        nameField.sendKeys(newName);
        driver.findElement(saveAccountBtn).click();
        System.out.println("[UI] Account saved with new name: " + newName);
    }

    /**
     * Returns true if the profile section is displayed on the page.
     *
     * @return true if visible
     */
    public boolean isProfileSectionVisible() {
        return driver.findElements(profileSection).size() > 0
                && driver.findElement(profileSection).isDisplayed();
    }
}
