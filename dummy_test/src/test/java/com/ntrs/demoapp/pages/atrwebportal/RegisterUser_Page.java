package com.ntrs.demoapp.pages.atrwebportal;

import org.openqa.selenium.By;
import org.openqa.selenium.WebDriver;
import org.openqa.selenium.WebElement;

/**
 * UI Page: User registration form for new account creation in the ATR portal.
 * Called by businessfunctions.Test.registerNewUser() and ATR_Portal_POC_Tests.
 *
 * Layer: ui (atrwebportal)
 * Used by: businessfunctions.Test, ATR_Portal_POC_Tests
 */
public class RegisterUser_Page {

    private WebDriver driver;

    // Locators
    private final By firstNameField        = By.id("firstName");
    private final By lastNameField         = By.id("lastName");
    private final By emailField            = By.id("email");
    private final By passwordField         = By.id("password");
    private final By confirmPasswordField  = By.id("confirmPassword");
    private final By termsCheckbox         = By.id("acceptTerms");
    private final By submitButton          = By.id("registerBtn");
    private final By successMessage        = By.id("successMsg");
    private final By validationError       = By.cssSelector(".validation-error");

    public RegisterUser_Page(WebDriver driver) {
        this.driver = driver;
    }

    /**
     * Enters the user's first name.
     *
     * @param firstName user's first name
     */
    public void enterFirstName(String firstName) {
        driver.findElement(firstNameField).sendKeys(firstName);
    }

    /**
     * Enters the user's last name.
     *
     * @param lastName user's last name
     */
    public void enterLastName(String lastName) {
        driver.findElement(lastNameField).sendKeys(lastName);
    }

    /**
     * Enters the email address for the new account.
     *
     * @param email the registration email
     */
    public void enterEmail(String email) {
        driver.findElement(emailField).sendKeys(email);
    }

    /**
     * Enters the desired password.
     *
     * @param password the account password
     */
    public void enterPassword(String password) {
        driver.findElement(passwordField).sendKeys(password);
    }

    /**
     * Confirms the password in the confirm-password field.
     *
     * @param password must match the password entered above
     */
    public void confirmPassword(String password) {
        driver.findElement(confirmPasswordField).sendKeys(password);
    }

    /**
     * Checks the "Accept Terms and Conditions" checkbox.
     */
    public void acceptTerms() {
        WebElement checkbox = driver.findElement(termsCheckbox);
        if (!checkbox.isSelected()) {
            checkbox.click();
        }
    }

    /**
     * Clicks the Register/Submit button to submit the form.
     */
    public void submitRegistration() {
        System.out.println("[UI] Submitting registration form");
        driver.findElement(submitButton).click();
    }

    /**
     * Completes the full registration flow in one call.
     *
     * @param firstName first name
     * @param lastName  last name
     * @param email     registration email
     * @param password  password (used for both fields)
     */
    public void fillAndSubmit(String firstName, String lastName, String email, String password) {
        enterFirstName(firstName);
        enterLastName(lastName);
        enterEmail(email);
        enterPassword(password);
        confirmPassword(password);
        acceptTerms();
        submitRegistration();
    }

    /**
     * Returns the success confirmation message after registration.
     *
     * @return success message text
     */
    public String getSuccessMessage() {
        return driver.findElement(successMessage).getText();
    }

    /**
     * Returns the first validation error message, if any.
     *
     * @return error text or empty string
     */
    public String getValidationError() {
        try {
            return driver.findElement(validationError).getText();
        } catch (Exception e) {
            return "";
        }
    }
}
