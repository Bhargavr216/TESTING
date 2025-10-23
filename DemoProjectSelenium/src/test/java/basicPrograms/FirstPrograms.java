package basicPrograms;

import org.openqa.selenium.WebDriver;
import org.openqa.selenium.chrome.ChromeDriver;

public class FirstPrograms {

	public static void main(String[] args) throws InterruptedException 
	{
		WebDriver driver= new ChromeDriver();
		
		driver.get("https://login.salesforce.com/");
		//get method is responsible to launch the URL
		
		//to maximize the browser window
		driver.manage().window().maximize();
		
		//To pause or delay
		Thread.sleep(5000);
		
		//To close the browser
		driver.quit();

	}

}
