package handlingVariousWebElements;

import org.openqa.selenium.By;
import org.openqa.selenium.WebDriver;
import org.openqa.selenium.WebElement;
import org.openqa.selenium.chrome.ChromeDriver;

public class AutomatingFrameworkElements {

	public static void main(String[] args) throws InterruptedException {
		WebDriver driver= new ChromeDriver();
		driver.get("https://ui.vision/demo/webtest/frames/");
		driver.manage().window().maximize();
		Thread.sleep(3000);

		driver.switchTo().frame(0);
		driver.findElement(By.name("mytext1")).sendKeys("Chandresh");
		Thread.sleep(3000);
		
		driver.switchTo().defaultContent();
		driver.switchTo().frame(1);
		driver.findElement(By.name("mytext2")).sendKeys("Harish");
		Thread.sleep(3000);
		
		driver.switchTo().defaultContent();
		driver.switchTo().frame(2);
		driver.findElement(By.name("mytext3")).sendKeys("Ayansh");
		Thread.sleep(3000);
		
		driver.switchTo().defaultContent();
		driver.switchTo().frame(0);
		WebElement newframe1 =  driver.findElement(By.name("mytext1"));
		newframe1.clear();
		newframe1.sendKeys("Prachi");
		
	}

}
