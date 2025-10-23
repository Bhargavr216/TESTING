package practiceWithTestng;

import org.testng.annotations.Test;
import org.testng.annotations.Test;
import org.testng.annotations.Test;
import java.time.Duration;
import java.util.Iterator;
import java.util.Set;

import org.openqa.selenium.By;
import org.openqa.selenium.WebDriver;
import org.openqa.selenium.WebElement;
import org.openqa.selenium.chrome.ChromeDriver;
import org.testng.annotations.Test;

public class HandlingNewTab {
	@Test
	public void newTab() throws InterruptedException
	{
		WebDriver driver = new ChromeDriver();
		driver.manage().timeouts().implicitlyWait(Duration.ofSeconds(5));
		driver.get("https://rahulshettyacademy.com/AutomationPractice/");	
		Thread.sleep(2000);
		driver.manage().window().maximize();
		Thread.sleep(3000);
		WebElement openWindow = driver.findElement(By.id("opentab"));
		openWindow.click();
		Thread.sleep(3000);
		
		System.out.println(driver.getCurrentUrl());
		
		System.out.println("Base Tab URL: " + driver.getCurrentUrl());

        Set<String> winHandles = driver.getWindowHandles();
        Iterator<String> iter = winHandles.iterator();

        String baseTab = iter.next();
        String NewTab = iter.next();

        driver.switchTo().window(NewTab); 
        System.out.println("Switched to new tab");

        System.out.println("New Tab URL: " + driver.getCurrentUrl());
        
        WebElement  aboutus= driver.findElement(By.xpath("(//a[@href='about.html'])[1]"));
        aboutus.click();
        Thread.sleep(3000);
        driver.close();

        driver.switchTo().window(baseTab);
        driver.close();
	}

}
