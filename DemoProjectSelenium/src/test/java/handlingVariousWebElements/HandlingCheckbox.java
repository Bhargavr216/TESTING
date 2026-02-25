package handlingVariousWebElements;

import java.util.List;

import org.openqa.selenium.By;
import org.openqa.selenium.WebDriver;
import org.openqa.selenium.WebElement;
import org.openqa.selenium.chrome.ChromeDriver;

public class HandlingCheckbox {

	public static void main(String[] args) throws InterruptedException 
	{
		WebDriver driver=new ChromeDriver();		
		driver.get("https://rahulshettyacademy.com/AutomationPractice/");
		driver.manage().window().maximize();
		Thread.sleep(3000);
		
		WebElement ch1 = driver.findElement(By.id("checkBoxOption1")); 
		System.out.println(ch1.isSelected());
		Thread.sleep(3000);
		System.out.println('\n');
		
		WebElement ch2 = driver.findElement(By.id("checkBoxOption2")); 
		System.out.println(ch2.isDisplayed());
		System.out.println(ch2.isSelected());
		Thread.sleep(2000);
		ch2.click();
		System.out.println(ch2.isSelected());
		
		List<WebElement> allchecks = driver.findElements(By.xpath("//input[@type='checkbox']"));
		
		for(int i=0; i<allchecks.size(); i++) {
			allchecks.get(i).click();
			Thread.sleep(2000);
		}
		Thread.sleep(2000);
		for(WebElement xy:allchecks) {
			xy.click();
			Thread.sleep(2000);
		}
		
		
		driver.close();
		
	}

}
