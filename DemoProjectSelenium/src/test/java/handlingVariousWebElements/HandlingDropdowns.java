package handlingVariousWebElements;

import org.openqa.selenium.By;
import org.openqa.selenium.WebDriver;
import org.openqa.selenium.WebElement;
import org.openqa.selenium.chrome.ChromeDriver;
import org.openqa.selenium.support.ui.Select;

public class HandlingDropdowns {

	public static void main(String[] args) throws InterruptedException {
		WebDriver driver=new ChromeDriver();		
		driver.get("https://rahulshettyacademy.com/AutomationPractice/");
		driver.manage().window().maximize();
		Thread.sleep(3000);
		
		WebElement dd = driver.findElement(By.id("dropdown-class-example")); 
		Select obj=new Select(dd);
		obj.selectByIndex(1);
		Thread.sleep(3000);
		obj.selectByValue("option2");
		Thread.sleep(3000);
		obj.selectByVisibleText("Option3");

		//driver.close();
	}

}
