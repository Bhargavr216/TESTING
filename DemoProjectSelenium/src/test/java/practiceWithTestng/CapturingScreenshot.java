package practiceWithTestng;

import java.io.File;
import java.io.IOException;
import java.time.Duration;

import org.apache.commons.io.FileUtils;
import org.openqa.selenium.OutputType;
import org.openqa.selenium.TakesScreenshot;
import org.openqa.selenium.WebDriver;
import org.openqa.selenium.chrome.ChromeDriver;
import org.testng.annotations.Test;


public class CapturingScreenshot {

	@Test
	public void screenshot() throws InterruptedException, IOException
	{
		    WebDriver driver = new ChromeDriver();
			driver.manage().timeouts().implicitlyWait(Duration.ofSeconds(5));
			driver.get("https://rahulshettyacademy.com/AutomationPractice/");
			Thread.sleep(2000);
			driver.manage().window().maximize();
			Thread.sleep(2000);
			TakesScreenshot ts = (TakesScreenshot)driver;
			File sourceFile = ts.getScreenshotAs(OutputType.FILE);
			
			File destinationFile = new File("/Users/chandresh/Documents/imagess.png");
	
			FileUtils.copyFile(sourceFile, destinationFile);

			System.out.println("Captured!!!");
			
			
	}

}
