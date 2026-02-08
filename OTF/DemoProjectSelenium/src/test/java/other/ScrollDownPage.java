package other;

import java.awt.Desktop.Action;

import org.openqa.selenium.By;
import org.openqa.selenium.JavascriptExecutor;
import org.openqa.selenium.WebDriver;
import org.openqa.selenium.WebElement;
import org.openqa.selenium.chrome.ChromeDriver;
import org.openqa.selenium.interactions.Actions;

public class ScrollDownPage {

	public static void main(String[] args) throws InterruptedException {
		
		WebDriver driver = new ChromeDriver();
		driver.get("https://rahulshettyacademy.com/AutomationPractice/");	
		driver.manage().window().maximize();
		Thread.sleep(3000);

		JavascriptExecutor js = (JavascriptExecutor) driver;
		js.executeScript("window.scrollBy(0,1000)", "");
		Thread.sleep(3000);
		
		Actions a = new Actions(driver);
		
		WebElement mouseHover = driver.findElement(By.id("mousehover"));
		
		a.moveToElement(mouseHover).build().perform();
		Thread.sleep(3000);
		
		driver.findElement(By.xpath("//a[@href=\"#top\"]")).click();
		Thread.sleep(3000);
		
		js.executeScript("arguments[0].scrollIntoView();",mouseHover );
		Thread.sleep(3000);
		
		js.executeScript("window.scrollBy(0,-1000)", "");
		Thread.sleep(3000);
		
		js.executeScript("window.scrollBy(0,document.body.scrollHeight)");
		
		
		
	}

}
