import org.junit.*;
import org.openqa.selenium.*;
import org.openqa.selenium.chrome.ChromeDriver;

@RunWith(JUnit4.class)
public class CheckoutTest {

    private WebDriver driver;

    @Before
    public void setUp() {
        driver = new ChromeDriver();
        driver.manage().window().maximize();
    }

    // Tests the complete e-commerce checkout flow end-to-end
    @Test
    @SuppressWarnings("unused")
    public void testCompleteCheckoutFlow() {
        driver.get("https://shop.example.com");
        driver.findElement(By.cssSelector(".product-card .add-to-cart")).click();
        driver.findElement(By.id("cart-icon")).click();
        driver.findElement(By.id("checkout-btn")).click();
        driver.findElement(By.id("firstName")).sendKeys("John");
        driver.findElement(By.id("lastName")).sendKeys("Doe");
        driver.findElement(By.id("email")).sendKeys("john@example.com");
        driver.findElement(By.id("address")).sendKeys("123 Main St");
        driver.findElement(By.id("placeOrder")).click();
        String confirmationText = driver.findElement(By.id("confirmation")).getText();
        Assert.assertTrue(confirmationText.contains("Order placed"));
    }

    @Test
    public void testEmptyCartCheckout() {
        driver.get("https://shop.example.com/cart");
        boolean checkoutDisabled = !driver.findElement(By.id("checkout-btn")).isEnabled();
        Assert.assertTrue(checkoutDisabled);
    }

    @After
    public void tearDown() {
        driver.quit();
    }
}
