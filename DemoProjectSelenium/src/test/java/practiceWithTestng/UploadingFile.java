package practiceWithTestng;

import org.testng.annotations.Test;
import org.testng.annotations.Test;
import org.testng.annotations.Test;
import java.time.Duration;

import org.openqa.selenium.By;
import org.openqa.selenium.WebDriver;
import org.openqa.selenium.WebElement;
import org.openqa.selenium.chrome.ChromeDriver;
import org.testng.annotations.Test;

public class UploadingFile {
	
	@Test
	public void uploadFile() throws InterruptedException
	{
		WebDriver driver = new ChromeDriver();
		driver.manage().timeouts().implicitlyWait(Duration.ofSeconds(5));
		driver.get("https://demo.automationtesting.in/FileUpload.html");	
		Thread.sleep(2000);
		driver.manage().window().maximize();
		Thread.sleep(3000);
		
		String filePath ="/Users/chandresh/Documents/Chandresh photo1651056817.jpeg";
		
		WebElement browserButton = driver.findElement(By.id("input-4"));
		
		browserButton.sendKeys(filePath);
	}

}
