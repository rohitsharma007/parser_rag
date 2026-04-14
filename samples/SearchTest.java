import org.junit.*;
import org.openqa.selenium.*;
import org.openqa.selenium.chrome.ChromeDriver;

public class SearchTest {

    private WebDriver driver;

    @BeforeClass
    public static void setUpClass() {
        System.out.println("Starting Search Test Suite");
    }

    @Before
    public void setUp() {
        driver = new ChromeDriver();
    }

    /* Verifies that a basic keyword search returns at least one result */
    @Test
    public void testBasicSearch() {
        driver.get("https://example.com");
        driver.findElement(By.name("q")).sendKeys("Selenium WebDriver");
        driver.findElement(By.name("q")).submit();
        WebElement firstResult = driver.findElement(By.cssSelector(".result:first-child"));
        Assert.assertTrue(firstResult.isDisplayed());
    }

    // Tests search with a filter option applied
    @Test
    public void testSearchWithFilters() {
        driver.get("https://example.com/search");
        driver.findElement(By.id("searchBox")).clear();
        driver.findElement(By.id("searchBox")).sendKeys("Java testing");
        driver.findElement(By.id("filterDropdown")).click();
        driver.findElement(By.xpath("//option[@value='recent']")).click();
        driver.findElement(By.id("searchBtn")).click();
        String url = driver.getCurrentUrl();
        Assert.assertTrue(url.contains("filter=recent"));
    }

    @After
    public void tearDown() {
        driver.close();
    }

    @AfterClass
    public static void tearDownClass() {
        System.out.println("Search Tests Completed");
    }
}
