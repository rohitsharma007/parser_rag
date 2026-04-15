package com.ntrs.demoapp.testcases;

import io.appium.java_client.AppiumDriver;
import io.appium.java_client.MobileElement;
import io.appium.java_client.android.AndroidDriver;
import io.appium.java_client.ios.IOSDriver;
import org.openqa.selenium.remote.DesiredCapabilities;
import org.testng.annotations.AfterMethod;
import org.testng.annotations.BeforeMethod;
import org.testng.annotations.Optional;
import org.testng.annotations.Parameters;

import java.net.MalformedURLException;
import java.net.URL;

/**
 * Base test class for Appium mobile automation tests.
 * Extends BaseTest; overrides setup/teardown to initialise an Appium driver
 * instead of a Selenium WebDriver.
 *
 * Layer: base (testcases)
 * Extends: BaseTest
 * Used by: any mobile test classes (extended in future)
 */
// extends BaseTest
public class BaseTestAppium extends BaseTest {

    /** Appium driver instance for mobile interactions. */
    protected AppiumDriver<MobileElement> mobileDriver;

    /** Default Appium server URL. */
    private static final String APPIUM_SERVER_URL = "http://127.0.0.1:4723/wd/hub";

    /**
     * Overrides BaseTest.setup() to initialise an Appium driver.
     * Platform defaults to "android"; pass "ios" as a TestNG parameter to use IOSDriver.
     *
     * @param platform optional mobile platform ("android" or "ios"), defaults to "android"
     */
    @Override
    @BeforeMethod
    @Parameters({"platform"})
    public void setup(@Optional("android") String platform) {
        System.out.println("[BaseTestAppium] setup() — platform=" + platform);

        DesiredCapabilities caps = new DesiredCapabilities();
        caps.setCapability("platformName", platform);
        caps.setCapability("automationName",
                "ios".equalsIgnoreCase(platform) ? "XCUITest" : "UiAutomator2");
        caps.setCapability("deviceName",
                "ios".equalsIgnoreCase(platform) ? "iPhone 14" : "emulator-5554");
        caps.setCapability("app", "app/ATRApp." + ("ios".equalsIgnoreCase(platform) ? "ipa" : "apk"));
        caps.setCapability("newCommandTimeout", 60);
        caps.setCapability("noReset", false);

        try {
            URL appiumUrl = new URL(APPIUM_SERVER_URL);
            if ("ios".equalsIgnoreCase(platform)) {
                mobileDriver = new IOSDriver<>(appiumUrl, caps);
            } else {
                mobileDriver = new AndroidDriver<>(appiumUrl, caps);
            }
            System.out.println("[BaseTestAppium] Appium driver started on " + platform);
        } catch (MalformedURLException e) {
            throw new RuntimeException("[BaseTestAppium] Invalid Appium server URL: " + APPIUM_SERVER_URL, e);
        }
    }

    /**
     * Overrides BaseTest.teardown() to quit the Appium session.
     */
    @Override
    @AfterMethod
    public void teardown() {
        System.out.println("[BaseTestAppium] teardown() — closing Appium session");
        if (mobileDriver != null) {
            mobileDriver.quit();
            mobileDriver = null;
        }
    }

    /**
     * Returns the current activity name on Android (empty on iOS).
     *
     * @return current activity or empty string
     */
    protected String getCurrentActivity() {
        try {
            if (mobileDriver instanceof AndroidDriver) {
                return ((AndroidDriver<?>) mobileDriver).currentActivity();
            }
        } catch (Exception e) {
            System.out.println("[BaseTestAppium] Could not get current activity: " + e.getMessage());
        }
        return "";
    }

    /**
     * Simulates pressing the device back button (Android only).
     */
    protected void pressBack() {
        if (mobileDriver instanceof AndroidDriver) {
            System.out.println("[BaseTestAppium] Pressing device Back button");
            ((AndroidDriver<?>) mobileDriver).pressKey(
                    new io.appium.java_client.android.nativekey.KeyEvent(
                            io.appium.java_client.android.nativekey.AndroidKey.BACK));
        }
    }
}
