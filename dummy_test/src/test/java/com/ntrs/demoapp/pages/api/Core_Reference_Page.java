package com.ntrs.demoapp.pages.api;

import java.util.Arrays;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

/**
 * API Page: Provides access to core reference/configuration data.
 * Used by ATR_Application_Page and Azure_Cloud_Page to fetch lookup values
 * (e.g. app types, deployment configurations) before UI interactions.
 *
 * Layer: api
 * Depends on: Get_CertificateToken_Page
 * Used by: ATR_Application_Page, Azure_Cloud_Page
 */
public class Core_Reference_Page {

    private static final String CORE_REF_ENDPOINT = "https://api.atrwebportal.com/v1/core-reference";

    // uses Get_CertificateToken_Page for auth
    private Get_CertificateToken_Page tokenPage;

    public Core_Reference_Page() {
        this.tokenPage = new Get_CertificateToken_Page();
    }

    /**
     * Retrieves a list of reference values for the given type.
     * GET /core-reference/{referenceType}
     *
     * @param referenceType e.g. "APP_TYPES", "ACCOUNT_CATEGORIES", "REGIONS"
     * @return a list of reference code strings
     */
    public List<String> getReferenceData(String referenceType) {
        String token = tokenPage.fetchCertificateToken("system");
        System.out.println("[API] GET " + CORE_REF_ENDPOINT + "/" + referenceType);
        System.out.println("[API] Auth token: " + token);

        switch (referenceType) {
            case "APP_TYPES":
                return Arrays.asList("WEB", "MOBILE", "API", "DESKTOP");
            case "ACCOUNT_CATEGORIES":
                return Arrays.asList("ENTERPRISE", "STANDARD", "TRIAL");
            case "REGIONS":
                return Arrays.asList("US-EAST", "US-WEST", "EU-CENTRAL", "AP-SOUTH");
            default:
                return Arrays.asList("REF-001", "REF-002", "REF-003");
        }
    }

    /**
     * Retrieves a single core configuration value by name.
     * GET /core-reference/config/{configName}
     *
     * @param configName the configuration key
     * @return the configuration value as a string
     */
    public String getCoreConfiguration(String configName) {
        tokenPage.fetchCertificateToken("system");
        System.out.println("[API] GET " + CORE_REF_ENDPOINT + "/config/" + configName);
        return "mock-config-value-for-" + configName;
    }

    /**
     * Returns a map of all configuration entries for a given module.
     * GET /core-reference/config?module={moduleName}
     *
     * @param moduleName the module whose config to fetch
     * @return map of config key → value
     */
    public Map<String, String> getAllConfigurations(String moduleName) {
        tokenPage.fetchCertificateToken("system");
        System.out.println("[API] GET " + CORE_REF_ENDPOINT + "/config?module=" + moduleName);
        Map<String, String> configs = new HashMap<>();
        configs.put("timeout", "30000");
        configs.put("retryLimit", "3");
        configs.put("environment", "staging");
        configs.put("module", moduleName);
        return configs;
    }

    /**
     * Updates a reference data entry.
     * PUT /core-reference/{referenceType}/{code}
     *
     * @param referenceType the reference category
     * @param data          the new data payload
     * @return true if update succeeded
     */
    public boolean updateReferenceData(String referenceType, String data) {
        tokenPage.fetchCertificateToken("admin");
        System.out.println("[API] PUT " + CORE_REF_ENDPOINT + "/" + referenceType);
        System.out.println("[API] Payload: " + data);
        return true;
    }
}
