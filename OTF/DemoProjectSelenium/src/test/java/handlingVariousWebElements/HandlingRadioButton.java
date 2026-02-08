package handlingVariousWebElements;

import java.util.List;

import org.openqa.selenium.By;
import org.openqa.selenium.WebDriver;
import org.openqa.selenium.WebElement;
import org.openqa.selenium.chrome.ChromeDriver;

public class HandlingRadioButton {

	public static void main(String[] args) throws InterruptedException 
	{
		WebDriver driver=new ChromeDriver();		
		driver.get("https://rahulshettyacademy.com/AutomationPractice/");
		driver.manage().window().maximize();
		Thread.sleep(3000);
		
		WebElement r1 = driver.findElement(By.xpath("//input[@value='radio1']")); //
		
		/*System.out.println("radio1 : " +r1.isDisplayed());
		System.out.println("radio1 : " +r1.isSelected());
		System.out.println("radio1 : " +r1.isEnabled());
		
		r1.click();
		System.out.println("radio1 : " +r1.isSelected());*/
		
		/*WebElement r2 = driver.findElement(By.xpath("//input[@value='radio2']"));
		
		System.out.println("radio2 : " +r2.isDisplayed());
		System.out.println("radio2 : " +r2.isSelected());
		System.out.println("radio2 : " +r2.isEnabled());
		
		r2.click();
		System.out.println("radio2 : " +r2.isSelected());
		
		WebElement r3 = driver.findElement(By.xpath("//input[@value='radio3']"));
		
		System.out.println("radio3 : " +r3.isDisplayed());
		System.out.println("radio3 : " +r3.isSelected());
		System.out.println("radio3 : " +r3.isEnabled());
		
		r3.click();
		System.out.println("radio2 : " +r3.isSelected());*/

		/*List<WebElement> allRadioButtons =driver.findElements(By.xpath("//input[@name='radioButton']"));
		
		for(int i=0; i<allRadioButtons.size(); i++)
		{
			allRadioButtons.get(i).click();
			Thread.sleep(3000);
		}*/
		
		/*for(int i=0; i<allRadioButtons.size(); i++)
		{
			//allRadioButtons.get(i).click();
			System.out.println(allRadioButtons.get(i).isDisplayed());
			System.out.println(allRadioButtons.get(i).isEnabled());
			System.out.println(allRadioButtons.get(i).isSelected());
			Thread.sleep(3000);
		}*/
		
		WebElement radio1 = driver.findElement(By.xpath("//label[@for='radio1']"));
		System.out.println(radio1.getText());
		
		WebElement radio2 = driver.findElement(By.xpath("//label[@for='radio2']"));
		System.out.println(radio2.getText());
		
		WebElement radio3 = driver.findElement(By.xpath("//label[@for='radio2']"));
		System.out.println(radio3.getText());
		
		driver.close();
	}

}
