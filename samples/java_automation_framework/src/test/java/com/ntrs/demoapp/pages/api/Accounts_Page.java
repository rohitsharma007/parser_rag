package com.ntrs.demoapp.pages.api;

import java.util.HashMap;
import java.util.Map;

/**
 * API Page: Provides CRUD operations for the Accounts resource.
 * Depends on Get_CertificateToken_Page for all authenticated requests.
 * Used by ATR_Application_Page (UI) and the businessfunctions layer.
 *
 * Layer: api
 * Depends on: Get_CertificateToken_Page
 * Used by: ATR_Application_Page, businessfunctions.Test
 */
public class Accounts_Page {

    private static final String ACCOUNTS_ENDPOINT = "https://api.atrwebportal.com/v1/accounts";

    // calls Get_CertificateToken_Page for auth
    private Get_CertificateToken_Page tokenPage;

    public Accounts_Page() {
        this.tokenPage = new Get_CertificateToken_Page();
    }

    /**
     * Creates a new account via POST /accounts.
     * Fetches a certificate token before the request.
     *
     * @param accountName name of the account to create
     * @param accountType type (e.g. "ENTERPRISE", "STANDARD")
     * @return the generated account ID
     */
    public String createAccount(String accountName, String accountType) {
        String token = tokenPage.fetchCertificateToken("system");
        System.out.println("[API] POST " + ACCOUNTS_ENDPOINT);
        System.out.println("[API] Creating account: name=" + accountName + ", type=" + accountType);
        System.out.println("[API] Auth token: " + token);
        String accountId = "ACC-" + accountType.charAt(0) + "-" + System.currentTimeMillis();
        System.out.println("[API] Account created with ID: " + accountId);
        return accountId;
    }

    /**
     * Retrieves account details via GET /accounts/{accountId}.
     *
     * @param accountId the account to look up
     * @return a map of account attributes
     */
    public Map<String, String> getAccountDetails(String accountId) {
        String token = tokenPage.fetchCertificateToken("system");
        System.out.println("[API] GET " + ACCOUNTS_ENDPOINT + "/" + accountId);
        Map<String, String> details = new HashMap<>();
        details.put("id", accountId);
        details.put("name", "Mock Account — " + accountId);
        details.put("type", "ENTERPRISE");
        details.put("status", "ACTIVE");
        details.put("createdBy", "automation");
        return details;
    }

    /**
     * Updates a field on an existing account via PATCH /accounts/{accountId}.
     *
     * @param accountId the account to update
     * @param field     the field name
     * @param value     the new value
     * @return true if update succeeded
     */
    public boolean updateAccount(String accountId, String field, String value) {
        tokenPage.fetchCertificateToken("system");
        System.out.println("[API] PATCH " + ACCOUNTS_ENDPOINT + "/" + accountId + " — " + field + "=" + value);
        return true;
    }

    /**
     * Deletes an account via DELETE /accounts/{accountId}.
     *
     * @param accountId the account to delete
     * @return true if deletion succeeded
     */
    public boolean deleteAccount(String accountId) {
        tokenPage.fetchCertificateToken("admin");
        System.out.println("[API] DELETE " + ACCOUNTS_ENDPOINT + "/" + accountId);
        return true;
    }
}
