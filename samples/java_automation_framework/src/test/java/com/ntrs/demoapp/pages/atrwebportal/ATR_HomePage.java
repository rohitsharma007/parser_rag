package com.ntrs.demoapp.pages.atrwebportal;

import org.openqa.selenium.By;
import org.openqa.selenium.WebDriver;

/**
 * UI Page: ATR Web Portal home/landing page after successful login.
 * Composes Navigation_Page and Menu_Page for dashboard interactions.
 *
 * Layer: ui (atrwebportal)
 * Depends on: Navigation_Page, Menu_Page
 * Used by: ATR_Portal_Tests, ATR_Portal_POC_Tests
 */
public class ATR_HomePage {

    private WebDriver driver;

    // uses Navigation_Page for routing
    private Navigation_Page navigationPage;

    // uses Menu_Page for menu interactions
    private Menu_Page menuPage;

    // Locators
    private final By welcomeBanner       = By.id("welcome-banner");
    private final By quickLinksSection   = By.id("quick-links");
    private final By notificationBell    = By.id("notification-bell");
    private final By notificationCount   = By.cssSelector("#notification-bell .badge");
    private final By recentActivityPanel = By.id("recent-activity");
    private final By userGreeting        = By.cssSelector(".user-greeting");

    public ATR_HomePage(WebDriver driver) {
        this.driver = driver;
        // new Navigation_Page()
        this.navigationPage = new Navigation_Page(driver);
        // new Menu_Page()
        this.menuPage = new Menu_Page(driver);
    }

    /**
     * Returns the welcome banner text displayed to the logged-in user.
     *
     * @return welcome message string
     */
    public String getWelcomeMessage() {
        return driver.findElement(welcomeBanner).getText();
    }

    /**
     * Returns the personalised greeting shown for the current user.
     *
     * @return greeting text (e.g. "Hello, John Doe")
     */
    public String getUserGreeting() {
        return driver.findElement(userGreeting).getText();
    }

    /**
     * Navigates to the dashboard via Navigation_Page.
     */
    public void navigateToDashboard() {
        // uses Navigation_Page
        navigationPage.goToDashboard();
    }

    /**
     * Opens the main navigation menu via Menu_Page.
     */
    public void openNavigationMenu() {
        // uses Menu_Page
        menuPage.openMenu();
    }

    /**
     * Navigates to a specific section by clicking a menu item.
     *
     * @param sectionName the section to navigate to
     */
    public void navigateToSection(String sectionName) {
        menuPage.openMenu();
        menuPage.clickMenuItem(sectionName);
    }

    /**
     * Returns true if a notification badge is visible in the bell icon.
     *
     * @return true if notifications are present
     */
    public boolean isNotificationPresent() {
        return driver.findElements(notificationBell).size() > 0
                && driver.findElement(notificationBell).isDisplayed();
    }

    /**
     * Returns the notification count shown on the bell badge.
     *
     * @return count as integer, 0 if not present
     */
    public int getNotificationCount() {
        try {
            return Integer.parseInt(driver.findElement(notificationCount).getText().trim());
        } catch (Exception e) {
            return 0;
        }
    }

    /**
     * Returns true if the Quick Links section is displayed.
     *
     * @return true if visible
     */
    public boolean isQuickLinksSectionVisible() {
        return driver.findElements(quickLinksSection).size() > 0
                && driver.findElement(quickLinksSection).isDisplayed();
    }
}
