package mouseRelated_And_OtherOperations;

import org.openqa.selenium.By;
import org.openqa.selenium.WebDriver;
import org.openqa.selenium.WebElement;
import org.openqa.selenium.chrome.ChromeDriver;
import org.openqa.selenium.interactions.Actions;

public class DragAndDrop {

	public static void main(String[] args) throws InterruptedException {
		
		WebDriver driver = new ChromeDriver();
		driver.get("http://www.dhtmlgoodies.com/scripts/drag-drop-custom/demo-drag-drop-3.html");	
		driver.manage().window().maximize();
		Thread.sleep(3000);
		
		WebElement stockholm= driver.findElement(By.xpath("(//div[contains(text(), 'Stockholm')])[2]"));
		
		WebElement sweden= driver.findElement(By.xpath("//div[@id='box102']"));
		
		Actions a = new Actions(driver);
		
		a.clickAndHold(stockholm).moveToElement(sweden).release().build().perform();
		
		Thread.sleep(3000);
		
        WebElement washignton= driver.findElement(By.xpath("(//div[contains(text(), 'Washington')])[2]"));
		
		WebElement united_statas= driver.findElement(By.xpath("//div[contains(text(), 'United States')]"));
		 
		a.dragAndDrop(washignton, united_statas).build().perform();


	}

}
