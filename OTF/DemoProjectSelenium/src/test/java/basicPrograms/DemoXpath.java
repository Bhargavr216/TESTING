package basicPrograms;

import org.openqa.selenium.By;
import org.openqa.selenium.WebDriver;
import org.openqa.selenium.WebElement;
import org.openqa.selenium.chrome.ChromeDriver;

public class DemoXpath {

	public static void main(String[] args) throws InterruptedException 
	{
		WebDriver driver= new ChromeDriver();
		
		driver.manage().window().maximize();
		
		Thread.sleep(5000);
		
		driver.get("https://www.linkedin.com/uas/login?session_redirect=https%3A%2F%2Fwww.linkedin.com%2Ffeed%2F");
		
		WebElement us = driver.findElement(By.xpath("//input[@validation='email|tel']"));
		Thread.sleep(5000);
		us.click();
		us.sendKeys("Admin");
		
		WebElement pass = driver.findElement(By.xpath("//input[@validation='password']"));
		pass.click();
		pass.sendKeys("admin123");
		Thread.sleep(5000);
		
		WebElement lg = driver.findElement(By.xpath("//button[@type='submit']"));
		lg.click();
		Thread.sleep(5000);
		
		String expected_error = "Please enter a valid username.";
		
		WebElement invaliduser = driver.findElement(By.xpath("//div[@id='error-for-username']"));
		
		System.out.println(invaliduser.getText().equals(expected_error));
		
		System.out.println(invaliduser.getText());
		
		driver.close();
		

	}

}
