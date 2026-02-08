package basicPrograms;

import org.openqa.selenium.By;
import org.openqa.selenium.WebDriver;
import org.openqa.selenium.WebElement;
import org.openqa.selenium.chrome.ChromeDriver;

public class SecondProgram {

	public static void main(String[] args) throws InterruptedException {

		WebDriver driver= new ChromeDriver();
		
		driver.get("https://login.salesforce.com/"); //get method is responsible to launch the URL
			
		driver.manage().window().maximize(); //to maximize the browser window
	
		Thread.sleep(3000); 	//To pause or delay
		
		//locate or identify username by textefield //locator - A locator is a way to identify elements on a page. It is the argument passed to the Finding element methods
		WebElement usern = driver.findElement(By.id("username"));
		
		Thread.sleep(3000);
		
		//This click method is responsible to perform click operation
		usern.click();
		
		//sendkeys -  Used to enter the value inside text fields
		usern.sendKeys("demo");
		
		//enter password field
		WebElement pass = driver.findElement(By.id("password"));
		
		Thread.sleep(2000);
		
		pass.click();
		
		pass.sendKeys("password");
		
		//to click on login button
		WebElement lg = driver.findElement(By.id("Login"));
		
		lg.click();

		Thread.sleep(5000);
		
		driver.close();

	}

}
