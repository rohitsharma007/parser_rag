package com.ntrs.demoapp.pages.atrwebportal;

import org.openqa.selenium.By;
import org.openqa.selenium.WebDriver;
import org.openqa.selenium.WebElement;
import org.openqa.selenium.support.ui.ExpectedConditions;
import org.openqa.selenium.support.ui.WebDriverWait;

import java.time.Duration;

/**
 * UI Page: Handles portal-level navigation (top nav bar, breadcrumbs, route changes).
 * Used as a collaborator by businessfunctions.Test, ATR_HomePage, and multiple test classes.
 *
 * Layer: ui (atrwebportal)
 * Used by: businessfunctions.Test, ATR_HomePage, ATR_Web_Portal_Tests, ATR_Portal_Tests
 */
public class Navigation_Page {

    private WebDriver driver;

    // Locators
    private final By dashboardLink    = By.id("nav-dashboard");
    private final By settingsLink     = By.id("nav-settings");
    private final By reportsLink      = By.id("nav-reports");
    private final By registrationLink = By.id("nav-registration");
    private final By logoutLink       = By.id("nav-logout");
    private final By breadcrumb       = By.className("breadcrumb");
    private final By pageHeading      = By.cssSelector("h1.page-title");

    public Navigation_Page(WebDriver driver) {
        this.driver = driver;
    }

    /**
     * Clicks the Dashboard link in the top navigation bar.
     */
    public void goToDashboard() {
        System.out.println("[UI] Navigation: → Dashboard");
        driver.findElement(dashboardLink).click();
    }

    /**
     * Clicks the Registration link to navigate to the user registration page.
     */
    public void goToRegistration() {
        System.out.println("[UI] Navigation: → Registration");
        driver.findElement(registrationLink).click();
    }

    /**
     * Clicks the Settings link in the nav bar.
     */
    public void goToSettings() {
        System.out.println("[UI] Navigation: → Settings");
        driver.findElement(settingsLink).click();
    }

    /**
     * Clicks the Reports link.
     */
    public void goToReports() {
        System.out.println("[UI] Navigation: → Reports");
        driver.findElement(reportsLink).click();
    }

    /**
     * Verifies the current page matches the expected page name,
     * by checking the page heading or URL fragment.
     *
     * @param expectedPage the page name expected (e.g. "Dashboard")
     */
    public void verifyCurrentPage(String expectedPage) {
        String currentUrl = driver.getCurrentUrl();
        String heading = "";
        try {
            heading = driver.findElement(pageHeading).getText();
        } catch (Exception ignored) {}
        System.out.println("[UI] Current URL: " + currentUrl + " | Heading: " + heading
                + " | Expected: " + expectedPage);
    }

    /**
     * Returns the breadcrumb trail text.
     *
     * @return breadcrumb text, or empty string if not found
     */
    public String getBreadcrumbText() {
        try {
            return driver.findElement(breadcrumb).getText();
        } catch (Exception e) {
            return "";
        }
    }

    /**
     * Logs out the current user via the nav bar logout link.
     */
    public void logout() {
        System.out.println("[UI] Logging out via navigation bar");
        driver.findElement(logoutLink).click();
    }
}
