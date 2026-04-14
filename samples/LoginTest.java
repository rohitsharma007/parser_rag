import org.junit.*;
import org.openqa.selenium.*;
import org.openqa.selenium.chrome.ChromeDriver;

@RunWith(JUnit4.class)
public class LoginTest {

    private WebDriver driver;

    @Before
    public void setUp() {
        driver = new ChromeDriver();
        driver.manage().timeouts().implicitlyWait(10, TimeUnit.SECONDS);
    }

    // Tests successful login with valid credentials
    @Test
    public void testSuccessfulLogin() {
        driver.get("https://example.com/login");
        driver.findElement(By.id("username")).sendKeys("admin");
        driver.findElement(By.id("password")).sendKeys("password123");
        driver.findElement(By.id("loginBtn")).click();
        String title = driver.getTitle();
        Assert.assertEquals("Dashboard", title);
    }

    @Test
    public void testLoginWithInvalidCredentials() {
        driver.get("https://example.com/login");
        driver.findElement(By.id("username")).sendKeys("wronguser");
        driver.findElement(By.id("password")).sendKeys("wrongpass");
        driver.findElement(By.cssSelector("button[type='submit']")).click();
        String errorMsg = driver.findElement(By.className("error-message")).getText();
        Assert.assertTrue(errorMsg.contains("Invalid credentials"));
    }

    @After
    public void tearDown() {
        if (driver != null) {
            driver.quit();
        }
    }
}
