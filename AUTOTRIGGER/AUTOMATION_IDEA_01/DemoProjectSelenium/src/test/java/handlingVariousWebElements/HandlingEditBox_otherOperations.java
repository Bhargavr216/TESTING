package handlingVariousWebElements;

import org.openqa.selenium.By;
import org.openqa.selenium.WebDriver;
import org.openqa.selenium.chrome.ChromeDriver;

public class HandlingEditBox_otherOperations {

	public static void main(String[] args) throws InterruptedException 
	{
		WebDriver driver=new ChromeDriver();
		
		driver.get("https://opensource-demo.orangehrmlive.com/web/index.php/auth/login");
		
		driver.manage().window().maximize();
		
		Thread.sleep(3000);
		
		driver.findElement(By.name("username")).sendKeys("Admin");
		Thread.sleep(2000);
		
		driver.findElement(By.name("password")).sendKeys("admin123");
		Thread.sleep(2000);

		driver.findElement(By.cssSelector("button[class='oxd-button oxd-button--medium oxd-button--main orangehrm-login-button']")).click();
		Thread.sleep(2000);
		
		driver.navigate().back();
		Thread.sleep(3000);
		
		driver.navigate().forward();
		Thread.sleep(3000);
		
		driver.navigate().to("https://music.amazon.in/?ref=dm_lnd_pm_listn_0b2f27ae_sv_dmusic_0");
		Thread.sleep(3000);
		
		driver.navigate().back();
		Thread.sleep(3000);
		
		//driver.close();
	}

}
