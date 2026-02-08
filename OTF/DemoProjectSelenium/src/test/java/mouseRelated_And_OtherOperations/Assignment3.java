package mouseRelated_And_OtherOperations;

import org.openqa.selenium.By;
import org.openqa.selenium.WebDriver;
import org.openqa.selenium.WebElement;
import org.openqa.selenium.chrome.ChromeDriver;
import org.openqa.selenium.interactions.Actions;

public class Assignment3 {

	public static void main(String[] args) throws InterruptedException {
		
		WebDriver driver = new ChromeDriver();
		driver.get("http://www.unipune.ac.in/");
		driver.manage().window().maximize();
		Thread.sleep(3000);
		
		WebElement home = driver.findElement(By.id("stUI3_txt"));
		Actions a = new Actions(driver);
		a.moveToElement(home).build().perform();
		Thread.sleep(3000);
		
		WebElement abouttheuniversity = driver.findElement(By.id("stUI5_txt"));
		a.moveToElement(abouttheuniversity).build().perform();
		Thread.sleep(3000);
		
		WebElement academics = driver.findElement(By.id("stUI45_txt"));
		a.moveToElement(academics).build().perform();
		Thread.sleep(3000);
		
		WebElement research = driver.findElement(By.id("stUI187_txt"));
		a.moveToElement(research).build().perform();
		Thread.sleep(3000);
		
		WebElement administration = driver.findElement(By.id("stUI197_txt"));
		a.moveToElement(administration).build().perform();
		Thread.sleep(3000);
		
		WebElement bod = driver.findElement(By.id("stUI220_txt"));
		a.moveToElement(bod).build().perform();
		Thread.sleep(3000);
		
		WebElement studentcorner = driver.findElement(By.id("stUI239_txt"));
		a.moveToElement(studentcorner).build().perform();
		Thread.sleep(3000);
		
		WebElement elearning = driver.findElement(By.id("stUI287_txt"));
		a.moveToElement(elearning).build().perform();
		Thread.sleep(3000);
		
		WebElement audiovideo = driver.findElement(By.id("stUI293_txt"));
		//a.moveToElement(audiovideo).build().perform();
		audiovideo.click();
		Thread.sleep(3000);
		
		
		

	}

}
