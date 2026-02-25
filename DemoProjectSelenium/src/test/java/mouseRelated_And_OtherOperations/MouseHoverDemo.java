package mouseRelated_And_OtherOperations;

import org.openqa.selenium.By;
import org.openqa.selenium.WebDriver;
import org.openqa.selenium.WebElement;
import org.openqa.selenium.chrome.ChromeDriver;
import org.openqa.selenium.interactions.Actions;

public class MouseHoverDemo {

	public static void main(String[] args) throws InterruptedException {
		
		WebDriver driver = new ChromeDriver();
		driver.get("https://rahulshettyacademy.com/AutomationPractice/");	
		driver.manage().window().maximize();
		Thread.sleep(3000);
		
		WebElement mousehov = driver.findElement(By.id("mousehover"));
		
		Actions act = new Actions(driver);
		Thread.sleep(3000);
		
		act.moveToElement(mousehov).build().perform();
		Thread.sleep(3000);
		
		driver.findElement(By.xpath("//a[@href='#top']")).click();
		
		

	}

}
