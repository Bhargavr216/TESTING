package handlingVariousWebElements;

import org.openqa.selenium.By;
import org.openqa.selenium.WebDriver;
import org.openqa.selenium.chrome.ChromeDriver;

public class HandlingLinks {

	public static void main(String[] args) throws InterruptedException 
	{
		WebDriver driver=new ChromeDriver();
		
		driver.get("https://opensource-demo.orangehrmlive.com/web/index.php/auth/login");
		
		driver.manage().window().maximize();
		Thread.sleep(3000);
		
		//driver.findElement(By.linkText("Forgot your password? ")).click(); // not working for linktext because this is not a link, it is para...
		//driver.findElement(By.linkText("OrangeHRM, Inc")).click();
		driver.findElement(By.partialLinkText("OrangeHRM, In")).click();
		Thread.sleep(3000);
		
		driver.close();

	}

}
