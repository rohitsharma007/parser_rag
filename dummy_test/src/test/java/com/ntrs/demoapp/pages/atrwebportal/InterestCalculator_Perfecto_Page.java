package com.ntrs.demoapp.pages.atrwebportal;

import org.openqa.selenium.By;
import org.openqa.selenium.WebDriver;
import org.openqa.selenium.WebElement;

/**
 * Perfecto-compatible UI Page: Interest Calculator form.
 * Fills in principal, rate, and years to compute compound/simple interest.
 * Called by FinancialCalculators_Perfecto_Page after navigating to the calculator.
 *
 * Layer: ui (atrwebportal)
 * Used by: FinancialCalculators_Perfecto_Page
 */
public class InterestCalculator_Perfecto_Page {

    private WebDriver driver;

    // Locators
    private final By principalField    = By.id("principal");
    private final By rateField         = By.id("rate");
    private final By yearsField        = By.id("years");
    private final By calcTypeDropdown  = By.id("calcType");
    private final By calculateBtn      = By.id("calculateInterest");
    private final By resultField       = By.id("interestResult");
    private final By totalAmountField  = By.id("totalAmount");
    private final By clearBtn          = By.id("clearCalc");

    public InterestCalculator_Perfecto_Page(WebDriver driver) {
        this.driver = driver;
    }

    /**
     * Enters the principal amount into the form.
     *
     * @param amount principal value
     */
    public void enterPrincipal(double amount) {
        System.out.println("[Perfecto] Entering principal: " + amount);
        WebElement field = driver.findElement(principalField);
        field.clear();
        field.sendKeys(String.valueOf(amount));
    }

    /**
     * Enters the annual interest rate (as a percentage) into the form.
     *
     * @param rate annual rate, e.g. 5.5 for 5.5%
     */
    public void enterRate(double rate) {
        System.out.println("[Perfecto] Entering rate: " + rate + "%");
        WebElement field = driver.findElement(rateField);
        field.clear();
        field.sendKeys(String.valueOf(rate));
    }

    /**
     * Enters the loan/investment term in years.
     *
     * @param years number of years
     */
    public void enterYears(int years) {
        System.out.println("[Perfecto] Entering years: " + years);
        WebElement field = driver.findElement(yearsField);
        field.clear();
        field.sendKeys(String.valueOf(years));
    }

    /**
     * Selects the calculation type (SIMPLE or COMPOUND).
     *
     * @param type "SIMPLE" or "COMPOUND"
     */
    public void selectCalcType(String type) {
        driver.findElement(calcTypeDropdown).sendKeys(type);
    }

    /**
     * Fills in all fields, clicks Calculate, and reads the result.
     * Called by FinancialCalculators_Perfecto_Page.
     *
     * @param principal loan/investment principal
     * @param rate      annual interest rate percentage
     * @param years     term in years
     * @return computed interest value
     */
    public double computeInterest(double principal, double rate, int years) {
        System.out.println("[Perfecto] Computing interest: P=" + principal
                + ", R=" + rate + "%, Y=" + years);
        enterPrincipal(principal);
        enterRate(rate);
        enterYears(years);
        driver.findElement(calculateBtn).click();

        String rawResult = driver.findElement(resultField).getText()
                .replace(",", "").replace("$", "").trim();
        double result = Double.parseDouble(rawResult);
        System.out.println("[Perfecto] Interest result: " + result);
        return result;
    }

    /**
     * Returns the total amount (principal + interest) from the result area.
     *
     * @return total amount value
     */
    public double getTotalAmount() {
        String raw = driver.findElement(totalAmountField).getText()
                .replace(",", "").replace("$", "").trim();
        return Double.parseDouble(raw);
    }

    /**
     * Resets the calculator form.
     */
    public void clearCalculator() {
        System.out.println("[Perfecto] Clearing calculator form");
        driver.findElement(clearBtn).click();
    }
}
