package com.ntrs.demoapp.pages.atrwebportal;

import org.openqa.selenium.By;
import org.openqa.selenium.WebDriver;
import org.openqa.selenium.WebElement;

import java.util.List;

/**
 * UI Page: Handles interactions with the main side/top menu.
 * Used in Flow 3 (Menu Navigation) by ATR_Web_Portal_Tests and businessfunctions.Test.
 *
 * Layer: ui (atrwebportal)
 * Used by: businessfunctions.Test, ATR_HomePage, ATR_Web_Portal_Tests
 */
public class Menu_Page {

    private WebDriver driver;

    // Locators
    private final By menuToggle    = By.id("menuToggle");
    private final By menuItems     = By.cssSelector(".menu-item");
    private final By activeItem    = By.cssSelector(".menu-item.active");
    private final By menuSearch    = By.id("menuSearch");
    private final By menuContainer = By.id("main-menu");

    public Menu_Page(WebDriver driver) {
        this.driver = driver;
    }

    /**
     * Opens the main navigation menu (hamburger toggle).
     */
    public void openMenu() {
        System.out.println("[UI] Opening main menu");
        driver.findElement(menuToggle).click();
    }

    /**
     * Closes the main navigation menu.
     */
    public void closeMenu() {
        System.out.println("[UI] Closing main menu");
        driver.findElement(menuToggle).click();
    }

    /**
     * Clicks a menu item by its visible text label.
     * Throws RuntimeException if the item is not found.
     *
     * @param itemName the display text of the menu item
     */
    public void clickMenuItem(String itemName) {
        System.out.println("[UI] Clicking menu item: " + itemName);
        List<WebElement> items = driver.findElements(menuItems);
        for (WebElement item : items) {
            if (item.getText().trim().equalsIgnoreCase(itemName)) {
                item.click();
                System.out.println("[UI] Menu item clicked: " + itemName);
                return;
            }
        }
        throw new RuntimeException("Menu item not found: '" + itemName + "'");
    }

    /**
     * Types a keyword into the menu search box to filter items.
     *
     * @param keyword the search string
     */
    public void searchMenu(String keyword) {
        System.out.println("[UI] Searching menu for: " + keyword);
        WebElement searchBox = driver.findElement(menuSearch);
        searchBox.clear();
        searchBox.sendKeys(keyword);
    }

    /**
     * Checks whether a specific menu item is visible in the DOM.
     *
     * @param itemName the menu item label to look for
     * @return true if found among current menu items
     */
    public boolean isMenuItemVisible(String itemName) {
        List<WebElement> items = driver.findElements(menuItems);
        return items.stream().anyMatch(i -> i.getText().trim().equalsIgnoreCase(itemName));
    }

    /**
     * Returns the currently active/selected menu item text.
     *
     * @return active menu item text or empty string
     */
    public String getActiveMenuItem() {
        try {
            return driver.findElement(activeItem).getText();
        } catch (Exception e) {
            return "";
        }
    }

    /**
     * Returns all menu item labels as a list.
     *
     * @return list of menu item display texts
     */
    public List<String> getAllMenuItems() {
        return driver.findElements(menuItems)
                .stream()
                .map(WebElement::getText)
                .collect(java.util.stream.Collectors.toList());
    }
}
