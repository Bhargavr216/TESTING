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

public class HandlingNewWindow {
	
	@Test
	public void newWindow() throws InterruptedException
	{
		WebDriver driver = new ChromeDriver();
		driver.manage().timeouts().implicitlyWait(Duration.ofSeconds(5));
		driver.get("https://rahulshettyacademy.com/AutomationPractice/");	
		Thread.sleep(2000);
		driver.manage().window().maximize();
		Thread.sleep(3000);
		WebElement openWindow = driver.findElement(By.id("openwindow"));
		openWindow.click();
		Thread.sleep(3000);
		
		System.out.println(driver.getCurrentUrl());
//		System.out.println(driver.getWindowHandle());
//		System.out.println(driver.getWindowHandles());
//		
		Set<String> winhand =driver.getWindowHandles();
		Iterator<String> iter = winhand.iterator();
		String parentWindow = iter.next();
		String childWindow = iter.next();
		
		driver.switchTo().window(childWindow); //shift the control to the child window
		
		WebElement courses = driver.findElement(By.xpath("(//a[@href='https://www.udemy.com/user/testing-minds/'])[2]"));
		courses.click();
		
		System.out.println("After shifting to another window");
		System.out.println(driver.getCurrentUrl());
	}

}
