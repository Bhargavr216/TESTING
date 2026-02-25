package tests;

import io.github.bonigarcia.wdm.WebDriverManager;
import org.openqa.selenium.WebDriver;
import org.openqa.selenium.chrome.ChromeDriver;
import org.testng.Assert;
import org.testng.annotations.*;
import pages.HomePage;

import java.time.Duration;
import java.util.Set;

public class HomePageTests {

    private WebDriver driver;
    private HomePage homePage;

    @BeforeClass
    public void setupClass() {
        // Setup WebDriverManager so we don’t have to manually specify chromedriver path
        WebDriverManager.chromedriver().setup();
    }

    @BeforeMethod
    public void setupTest() {
        driver = new ChromeDriver();
        driver.manage().timeouts().implicitlyWait(Duration.ofSeconds(10));
        driver.manage().window().maximize();
        // Use your actual URL or local file path
        driver.get("/index.html");
        homePage = new HomePage(driver);
    }

    @Test(priority = 1, description = "Verify About section header after clicking About nav link")
    public void testNavigateToAboutSection() {
        homePage.clickAboutNavLink();
        String actualHeader = homePage.getAboutHeaderText();
        String expectedHeader = "About Us";
        Assert.assertEquals(actualHeader, expectedHeader, "About section header text mismatch");
    }

    @Test(priority = 2, description = "Verify Discord button opens the correct external link")
    public void testDiscordButtonOpensCorrectUrl() {
        String originalWindow = driver.getWindowHandle();
        homePage.clickDiscordButton();

        // Wait or poll for switch to new window/tab
        Set<String> allWindows = driver.getWindowHandles();
        for (String windowHandle : allWindows) {
            if (!windowHandle.equals(originalWindow)) {
                driver.switchTo().window(windowHandle);
                break;
            }
        }

        String currentUrl = driver.getCurrentUrl();
        Assert.assertTrue(currentUrl.contains("discord.com/users/394251966571872256"),
                          "Discord button did not navigate to the correct user URL");
    }

    @Test(priority = 3, description = "Verify selecting filter ‘Sowwyz Nude’ shows group1 and hides group2")
    public void testPricingFilterGroup1ShowsCorrect() {
        homePage.clickFilterGroup1();
        Assert.assertTrue(homePage.isGroup1Visible(), "Group1 should be visible after filter1 clicked");
        Assert.assertFalse(homePage.isGroup2Visible(), "Group2 should not be visible after filter1 clicked");
    }

    @Test(priority = 4, description = "Verify selecting filter ‘Chungus Nude’ shows group2 and hides group1")
    public void testPricingFilterGroup2ShowsCorrect() {
        homePage.clickFilterGroup2();
        Assert.assertTrue(homePage.isGroup2Visible(), "Group2 should be visible after filter2 clicked");
        Assert.assertFalse(homePage.isGroup1Visible(), "Group1 should not be visible after filter2 clicked");
    }

    @AfterMethod
    public void tearDown() {
        if (driver != null) {
            driver.quit();
        }
    }
}
