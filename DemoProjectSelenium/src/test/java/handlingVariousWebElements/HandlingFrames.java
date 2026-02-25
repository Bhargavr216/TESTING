package handlingVariousWebElements;

import org.openqa.selenium.By;
import org.openqa.selenium.WebDriver;
import org.openqa.selenium.chrome.ChromeDriver;

public class HandlingFrames {

	public static void main(String[] args) throws InterruptedException {
		
		WebDriver driver= new ChromeDriver();
		driver.get("https://www.tutorialspoint.com/selenium/practice/frames.php");
		driver.manage().window().maximize();
		
		Thread.sleep(3000);
		driver.switchTo().frame(0);
		
		driver.findElement(By.linkText("Selenium Tutorial")).click();

	}

}
