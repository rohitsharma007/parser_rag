package com.ntrs.demoapp.businessfunctions;

// uses Login_Page
// uses Navigation_Page
// uses Menu_Page
// uses MyAccount_Page
// uses RegisterUser_Page
// calls Accounts_Page API
// calls Get_CertificateToken_Page API

import com.ntrs.demoapp.pages.api.Accounts_Page;
import com.ntrs.demoapp.pages.api.Core_Reference_Page;
import com.ntrs.demoapp.pages.api.Get_CertificateToken_Page;
import com.ntrs.demoapp.pages.atrwebportal.Login_Page;
import com.ntrs.demoapp.pages.atrwebportal.Menu_Page;
import com.ntrs.demoapp.pages.atrwebportal.MyAccount_Page;
import com.ntrs.demoapp.pages.atrwebportal.Navigation_Page;
import com.ntrs.demoapp.pages.atrwebportal.RegisterUser_Page;
import org.openqa.selenium.WebDriver;

/**
 * Business Functions layer — orchestrates multi-step automation flows
 * by coordinating page objects and API pages.
 *
 * This is the central orchestration class. Test classes call methods here
 * rather than calling page objects directly.
 *
 * Layer: service (businessfunctions)
 * Depends on (UI): Login_Page, Navigation_Page, Menu_Page, MyAccount_Page, RegisterUser_Page
 * Depends on (API): Accounts_Page, Get_CertificateToken_Page, Core_Reference_Page
 * Used by: all testcases/web/* test classes
 */
public class Test {

    private WebDriver driver;

    public Test(WebDriver driver) {
        this.driver = driver;
    }

    // ─────────────────────────────────────────────────────────────────────────
    // Flow 1: Login + Navigation
    // ─────────────────────────────────────────────────────────────────────────

    /**
     * Logs in with certificate token (via API) and navigates to the dashboard.
     * Called by ATR_Portal_Tests.testLoginFlow().
     *
     * @param username portal login username
     * @param password portal login password
     */
    public void loginAndNavigate(String username, String password) {
        System.out.println("[BF] loginAndNavigate: user=" + username);

        // calls Get_CertificateToken_Page API for pre-login token
        Get_CertificateToken_Page tokenPage = new Get_CertificateToken_Page();
        String token = tokenPage.fetchCertificateToken(username);
        System.out.println("[BF] Pre-flight token: " + token);

        // uses Login_Page
        Login_Page loginPage = new Login_Page(driver);
        loginPage.enterUsername(username);
        loginPage.enterPassword(password);
        loginPage.clickLogin();

        // uses Navigation_Page
        Navigation_Page navPage = new Navigation_Page(driver);
        navPage.goToDashboard();
        System.out.println("[BF] loginAndNavigate complete");
    }

    /**
     * Logs in using certificate-based SSO flow.
     *
     * @param username the SSO username
     */
    public void loginWithCertificate(String username) {
        System.out.println("[BF] loginWithCertificate: user=" + username);

        // uses Login_Page — which internally calls Get_CertificateToken_Page
        Login_Page loginPage = new Login_Page(driver);
        loginPage.loginWithToken(username);

        Navigation_Page navPage = new Navigation_Page(driver);
        navPage.goToDashboard();
    }

    // ─────────────────────────────────────────────────────────────────────────
    // Flow 2: Account Creation (API + UI)
    // ─────────────────────────────────────────────────────────────────────────

    /**
     * Creates an account via the Accounts API, then verifies it exists in the UI.
     * Called by ATR_Application_Regression_Tests.
     *
     * @param accountName name of the account to create
     * @param accountType type of the account (e.g. "ENTERPRISE")
     */
    public void createAndVerifyAccount(String accountName, String accountType) {
        System.out.println("[BF] createAndVerifyAccount: name=" + accountName + ", type=" + accountType);

        // calls Accounts_Page API
        Accounts_Page accountsApi = new Accounts_Page();
        String accountId = accountsApi.createAccount(accountName, accountType);
        System.out.println("[BF] Account created via API: id=" + accountId);

        // uses MyAccount_Page for UI verification
        MyAccount_Page myAccountPage = new MyAccount_Page(driver);
        myAccountPage.verifyAccount(accountName);
        myAccountPage.verifyAccountIsActive();
        System.out.println("[BF] Account verified in UI");
    }

    /**
     * Fetches account details from the API and prints them.
     *
     * @param accountId the account to inspect
     */
    public void inspectAccount(String accountId) {
        // calls Accounts_Page API
        Accounts_Page accountsApi = new Accounts_Page();
        accountsApi.getAccountDetails(accountId).forEach(
                (k, v) -> System.out.println("[BF]   " + k + ": " + v)
        );
    }

    // ─────────────────────────────────────────────────────────────────────────
    // Flow 3: Menu Navigation
    // ─────────────────────────────────────────────────────────────────────────

    /**
     * Opens the menu and clicks the given item, then verifies the current page.
     * Called by ATR_Web_Portal_Tests.
     *
     * @param menuItem the menu item text to click
     */
    public void navigateViaMenu(String menuItem) {
        System.out.println("[BF] navigateViaMenu: item=" + menuItem);

        // uses Menu_Page
        Menu_Page menuPage = new Menu_Page(driver);
        menuPage.openMenu();
        menuPage.clickMenuItem(menuItem);

        // uses Navigation_Page
        Navigation_Page navPage = new Navigation_Page(driver);
        navPage.verifyCurrentPage(menuItem);
        System.out.println("[BF] navigateViaMenu complete");
    }

    /**
     * Checks whether a given menu item exists.
     *
     * @param menuItem the item to look for
     * @return true if visible in the menu
     */
    public boolean isMenuItemAvailable(String menuItem) {
        // uses Menu_Page
        Menu_Page menuPage = new Menu_Page(driver);
        menuPage.openMenu();
        return menuPage.isMenuItemVisible(menuItem);
    }

    // ─────────────────────────────────────────────────────────────────────────
    // Flow 4: User Registration
    // ─────────────────────────────────────────────────────────────────────────

    /**
     * Navigates to the registration page and fills in the full registration form.
     * Called by ATR_Portal_POC_Tests.testRegisterNewUserPOC().
     *
     * @param firstName user's first name
     * @param lastName  user's last name
     * @param email     registration email
     * @param password  account password
     */
    public void registerNewUser(String firstName, String lastName, String email, String password) {
        System.out.println("[BF] registerNewUser: email=" + email);

        // uses Navigation_Page to go to registration
        Navigation_Page navPage = new Navigation_Page(driver);
        navPage.goToRegistration();

        // uses RegisterUser_Page
        RegisterUser_Page registerPage = new RegisterUser_Page(driver);
        registerPage.enterFirstName(firstName);
        registerPage.enterLastName(lastName);
        registerPage.enterEmail(email);
        registerPage.enterPassword(password);
        registerPage.confirmPassword(password);
        registerPage.acceptTerms();
        registerPage.submitRegistration();

        System.out.println("[BF] registerNewUser: form submitted for " + email);
    }

    // ─────────────────────────────────────────────────────────────────────────
    // Utility helpers
    // ─────────────────────────────────────────────────────────────────────────

    /**
     * Fetches a fresh auth token for the given user via the API.
     *
     * @param username the user
     * @return a valid certificate token string
     */
    public String getAuthToken(String username) {
        // calls Get_CertificateToken_Page API
        Get_CertificateToken_Page tokenPage = new Get_CertificateToken_Page();
        return tokenPage.fetchCertificateToken(username);
    }

    /**
     * Returns the list of valid reference data for a given category.
     *
     * @param referenceType the category to fetch
     * @return list of reference codes
     */
    public java.util.List<String> getReferenceValues(String referenceType) {
        // calls Core_Reference_Page API
        Core_Reference_Page coreRefPage = new Core_Reference_Page();
        return coreRefPage.getReferenceData(referenceType);
    }
}
