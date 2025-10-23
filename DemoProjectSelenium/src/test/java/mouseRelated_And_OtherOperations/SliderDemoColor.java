package mouseRelated_And_OtherOperations;

import org.openqa.selenium.By;
import org.openqa.selenium.WebDriver;
import org.openqa.selenium.WebElement;
import org.openqa.selenium.chrome.ChromeDriver;
import org.openqa.selenium.interactions.Actions;

public class SliderDemoColor {

	public static void main(String[] args) throws InterruptedException {
		
		WebDriver driver = new ChromeDriver();
		driver.get("https://jqueryui.com/slider/#colorpicker");
		driver.manage().window().maximize();
		Thread.sleep(3000);
		
		Actions a = new Actions(driver);
		
		WebElement frame = driver.findElement(By.xpath("//iframe[@class='demo-frame']"));
		driver.switchTo().frame(frame);
		Thread.sleep(2000);
		
		WebElement slider1 = driver.findElement(By.xpath("//div[@id='red']//span[@class=\"ui-slider-handle ui-corner-all ui-state-default\"]"));
		a.dragAndDropBy(slider1, 100, 0).build().perform();
		Thread.sleep(3000);
		
		a.dragAndDropBy(slider1, -80, 0).build().perform();
		Thread.sleep(3000);

		WebElement slider2 = driver.findElement(By.xpath("//div[@id='green']//span[@class=\"ui-slider-handle ui-corner-all ui-state-default\"]"));
		a.dragAndDropBy(slider1, 120, 0).build().perform();
		Thread.sleep(3000);
		
		a.dragAndDropBy(slider2, -80, 0).build().perform();
		Thread.sleep(3000);
		
		WebElement slider3 = driver.findElement(By.xpath("//div[@id='blue']//span[@class=\"ui-slider-handle ui-corner-all ui-state-default\"]"));
		a.dragAndDropBy(slider3, 150, 0).build().perform();
		Thread.sleep(3000);
		
		a.dragAndDropBy(slider3, -80, 0).build().perform();
		Thread.sleep(3000);
		
	}

}
