package com.ntrs.demoapp.retryanalyzer;

import org.testng.IRetryAnalyzer;
import org.testng.ITestResult;

/**
 * TestNG Retry Analyzer — automatically retries failed test methods up to MAX_RETRY_COUNT times.
 * Attach to individual test methods via @Test(retryAnalyzer = RetryAnalyzer.class).
 *
 * Layer: utility (retryanalyzer)
 * Implements: org.testng.IRetryAnalyzer
 * Used by: ATR_Portal_POC_Retry_Tests
 */
public class RetryAnalyzer implements IRetryAnalyzer {

    /** Current retry attempt counter for this test instance. */
    private int retryCount = 0;

    /** Maximum number of retry attempts per failed test. */
    private static final int MAX_RETRY_COUNT = 3;

    /**
     * Called by TestNG after each test failure.
     * Returns true to request a retry (up to MAX_RETRY_COUNT times).
     *
     * @param result the TestNG test result object
     * @return true if the test should be retried, false otherwise
     */
    @Override
    public boolean retry(ITestResult result) {
        if (!result.isSuccess()) {
            if (retryCount < MAX_RETRY_COUNT) {
                retryCount++;
                System.out.println("[RetryAnalyzer] Retrying test: '"
                        + result.getName() + "' — attempt " + retryCount + " of " + MAX_RETRY_COUNT);
                System.out.println("[RetryAnalyzer] Failure reason: "
                        + (result.getThrowable() != null ? result.getThrowable().getMessage() : "unknown"));
                return true;
            }
            System.out.println("[RetryAnalyzer] Max retries reached (" + MAX_RETRY_COUNT
                    + ") for test: '" + result.getName() + "' — marking as FAILED");
        }
        return false;
    }

    /**
     * Returns the number of retries performed so far for this test instance.
     *
     * @return current retry count
     */
    public int getRetryCount() {
        return retryCount;
    }

    /**
     * Returns the configured maximum retry count.
     *
     * @return max retry limit
     */
    public static int getMaxRetryCount() {
        return MAX_RETRY_COUNT;
    }

    /**
     * Resets the retry counter — useful when reusing the same instance across tests.
     */
    public void resetRetryCount() {
        this.retryCount = 0;
    }
}
