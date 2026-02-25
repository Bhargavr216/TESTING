package mouseRelated_And_OtherOperations;

import org.openqa.selenium.By;
import org.openqa.selenium.WebDriver;
import org.openqa.selenium.WebElement;
import org.openqa.selenium.chrome.ChromeDriver;
import org.openqa.selenium.interactions.Actions;

public class SliderDemo {

	public static void main(String[] args) throws InterruptedException {
		
		WebDriver driver = new ChromeDriver();
		driver.get("https://jqueryui.com/slider/");
		driver.manage().window().maximize();
		Thread.sleep(3000);
		
		Actions a = new Actions(driver);
		
		WebElement frame = driver.findElement(By.xpath("//iframe[@class='demo-frame']"));
		driver.switchTo().frame(frame);
		Thread.sleep(2000);
		
		WebElement slider = driver.findElement(By.xpath("//span[@class='ui-slider-handle ui-corner-all ui-state-default']"));

		a.dragAndDropBy(slider, 100, 0).build().perform();
		Thread.sleep(3000);
		
		a.dragAndDropBy(slider, -80, 0).build().perform();


	}

}
