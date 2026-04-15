package com.ntrs.demoapp.pages.atrwebportal;

import org.openqa.selenium.By;
import org.openqa.selenium.WebDriver;

/**
 * Perfecto-compatible UI Page: Financial Calculators hub page.
 * Acts as an entry point for all calculator tools; delegates interest
 * calculation to InterestCalculator_Perfecto_Page.
 *
 * Layer: ui (atrwebportal)
 * Depends on: InterestCalculator_Perfecto_Page
 * Used by: Azure_Public_Cloud_Tests (bonus flow)
 */
public class FinancialCalculators_Perfecto_Page {

    private WebDriver driver;

    // uses InterestCalculator_Perfecto_Page for interest computation
    private InterestCalculator_Perfecto_Page interestCalculator;

    // Locators
    private final By calcMenuSection        = By.id("calc-menu");
    private final By interestCalcLink       = By.id("interest-calc-link");
    private final By mortgageCalcLink       = By.id("mortgage-calc-link");
    private final By savingsCalcLink        = By.id("savings-calc-link");
    private final By calculatorPageHeading  = By.cssSelector("h1.calc-title");

    public FinancialCalculators_Perfecto_Page(WebDriver driver) {
        this.driver = driver;
        // new InterestCalculator_Perfecto_Page()
        this.interestCalculator = new InterestCalculator_Perfecto_Page(driver);
    }

    /**
     * Opens the financial calculators section of the portal.
     */
    public void openCalculatorsMenu() {
        System.out.println("[Perfecto] Opening financial calculators menu");
        driver.findElement(calcMenuSection).click();
    }

    /**
     * Navigates to the Interest Calculator sub-page.
     */
    public void navigateToInterestCalculator() {
        System.out.println("[Perfecto] Navigating to Interest Calculator");
        openCalculatorsMenu();
        driver.findElement(interestCalcLink).click();
    }

    /**
     * Navigates to the Mortgage Calculator sub-page.
     */
    public void navigateToMortgageCalculator() {
        System.out.println("[Perfecto] Navigating to Mortgage Calculator");
        openCalculatorsMenu();
        driver.findElement(mortgageCalcLink).click();
    }

    /**
     * Navigates to the Savings Calculator sub-page.
     */
    public void navigateToSavingsCalculator() {
        System.out.println("[Perfecto] Navigating to Savings Calculator");
        openCalculatorsMenu();
        driver.findElement(savingsCalcLink).click();
    }

    /**
     * Convenience method: navigates to the interest calculator and
     * delegates computation to InterestCalculator_Perfecto_Page.
     *
     * @param principal loan/investment principal
     * @param rate      annual interest rate percentage
     * @param years     term in years
     * @return computed interest value
     */
    public double calculateInterest(double principal, double rate, int years) {
        navigateToInterestCalculator();
        // uses InterestCalculator_Perfecto_Page
        return interestCalculator.computeInterest(principal, rate, years);
    }

    /**
     * Returns the heading text on the current calculator page.
     *
     * @return heading text
     */
    public String getCalculatorPageTitle() {
        return driver.findElement(calculatorPageHeading).getText();
    }
}
