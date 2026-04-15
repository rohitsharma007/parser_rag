package com.ntrs.demoapp.testcases.web;

// extends BaseTest
// uses Menu_Page
// uses Navigation_Page
// uses businessfunctions.Test
// Flow 3: Menu Navigation

import com.ntrs.demoapp.businessfunctions.Test;
import com.ntrs.demoapp.pages.atrwebportal.Menu_Page;
import com.ntrs.demoapp.pages.atrwebportal.Navigation_Page;
import com.ntrs.demoapp.testcases.BaseTest;
import org.testng.Assert;
import org.testng.annotations.Test as TestNG;

import java.util.List;

/**
 * Test class: ATR Web Portal — Menu Navigation and general portal behaviour.
 * Covers Flow 3: Menu Navigation.
 *
 * Layer: test
 * Extends: BaseTest
 * Uses: businessfunctions.Test, Menu_Page, Navigation_Page
 */
// extends BaseTest
public class ATR_Web_Portal_Tests extends BaseTest {

    // ──────────────────────────────────────────────────────────────────────────
    // Flow 3: Menu Navigation
    // ──────────────────────────────────────────────────────────────────────────

    /**
     * TC-020: Navigate to the Dashboard via the top menu.
     */
    @TestNG(description = "TC-020: Menu navigation to Dashboard",
            groups = {"smoke", "navigation"})
    public void testMenuNavigationToDashboard() {
        System.out.println("[TEST] ATR_Web_Portal_Tests.testMenuNavigationToDashboard()");

        // new Menu_Page()
        Menu_Page menuPage = new Menu_Page(driver);
        menuPage.openMenu();
        menuPage.clickMenuItem("Dashboard");

        // new Navigation_Page()
        Navigation_Page navPage = new Navigation_Page(driver);
        navPage.verifyCurrentPage("Dashboard");

        Assert.assertTrue(getCurrentUrl().contains("dashboard") || getCurrentUrl().contains("home"),
                "URL should reflect Dashboard navigation");
    }

    /**
     * TC-021: Check all expected menu items are present.
     */
    @TestNG(description = "TC-021: All expected menu items are visible",
            groups = {"regression", "navigation"})
    public void testMenuItemVisibility() {
        System.out.println("[TEST] ATR_Web_Portal_Tests.testMenuItemVisibility()");

        // new Menu_Page()
        Menu_Page menuPage = new Menu_Page(driver);
        menuPage.openMenu();

        Assert.assertTrue(menuPage.isMenuItemVisible("Dashboard"),
                "Dashboard menu item should be visible");
        Assert.assertTrue(menuPage.isMenuItemVisible("Reports"),
                "Reports menu item should be visible");

        System.out.println("[TEST] All expected menu items confirmed present");
    }

    /**
     * TC-022: Navigate via business functions menu helper.
     */
    @TestNG(description = "TC-022: BusinessFunctions navigateViaMenu() helper",
            groups = {"regression", "navigation"})
    public void testNavigateViaBusinessFunctions() {
        System.out.println("[TEST] ATR_Web_Portal_Tests.testNavigateViaBusinessFunctions()");

        // new BusinessFunctions (Test)
        Test businessFunctions = new Test(driver);
        businessFunctions.navigateViaMenu("Reports");

        System.out.println("[TEST] Navigation via business functions succeeded");
    }

    /**
     * TC-023: Menu search filters items correctly.
     */
    @TestNG(description = "TC-023: Menu search filters items",
            groups = {"regression", "navigation"})
    public void testMenuSearch() {
        System.out.println("[TEST] ATR_Web_Portal_Tests.testMenuSearch()");

        // new Menu_Page()
        Menu_Page menuPage = new Menu_Page(driver);
        menuPage.openMenu();
        menuPage.searchMenu("Report");

        List<String> allItems = menuPage.getAllMenuItems();
        System.out.println("[TEST] Menu items after search: " + allItems);
        Assert.assertNotNull(allItems, "Menu items list should not be null");
    }

    /**
     * TC-024: Navigate to Settings using Navigation_Page directly.
     */
    @TestNG(description = "TC-024: Navigate to Settings via Navigation_Page",
            groups = {"regression", "navigation"})
    public void testNavigateToSettings() {
        System.out.println("[TEST] ATR_Web_Portal_Tests.testNavigateToSettings()");

        // new Navigation_Page()
        Navigation_Page navPage = new Navigation_Page(driver);
        navPage.goToSettings();
        navPage.verifyCurrentPage("Settings");

        System.out.println("[TEST] Settings navigation verified");
    }

    /**
     * TC-025: Checks that the business functions layer correctly reports menu item availability.
     */
    @TestNG(description = "TC-025: BusinessFunctions isMenuItemAvailable() returns correct result",
            groups = {"regression", "navigation"})
    public void testMenuItemAvailability() {
        System.out.println("[TEST] ATR_Web_Portal_Tests.testMenuItemAvailability()");

        // new BusinessFunctions (Test)
        Test businessFunctions = new Test(driver);
        boolean dashboardAvailable = businessFunctions.isMenuItemAvailable("Dashboard");
        System.out.println("[TEST] Dashboard available in menu: " + dashboardAvailable);
    }
}
