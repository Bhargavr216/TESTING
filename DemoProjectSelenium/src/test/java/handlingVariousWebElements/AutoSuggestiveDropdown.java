package handlingVariousWebElements;

import java.util.List;

import org.openqa.selenium.By;
import org.openqa.selenium.Keys;
import org.openqa.selenium.WebDriver;
import org.openqa.selenium.WebElement;
import org.openqa.selenium.chrome.ChromeDriver;

public class AutoSuggestiveDropdown {

	public static void main(String[] args) throws InterruptedException 
	{
		WebDriver driver = new ChromeDriver();
		driver.get("https://rahulshettyacademy.com/dropdownsPractise/");	
		driver.manage().window().maximize();
		Thread.sleep(3000);
		
		WebElement autoSg = driver.findElement(By.xpath("//input[@id='autosuggest']"));
		
		autoSg.sendKeys("arg");
		Thread.sleep(3000);
//		
//		autoSg.sendKeys(Keys.ARROW_DOWN);
//		Thread.sleep(2000);
//		
//		autoSg.sendKeys(Keys.ARROW_DOWN);
//		Thread.sleep(1000);
//		
//		autoSg.sendKeys(Keys.ENTER); //Select Germany As a country
		
		List<WebElement> cc = driver.findElements(By.xpath("//a[@class='ui-corner-all']"));
		
		for(int i=0; i<cc.size(); i++)
		{
			if(cc.get(i).getText().equals("Argentina"))
			{
		        System.out.println("Your selected country name: " + cc.get(i).getText());
				cc.get(i).click();
				Thread.sleep(3000);
			}
		}
		driver.close();
	}

}
