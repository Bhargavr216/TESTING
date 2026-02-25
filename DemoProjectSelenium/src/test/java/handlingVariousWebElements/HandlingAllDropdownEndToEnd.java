package handlingVariousWebElements;

import java.util.List;

import org.openqa.selenium.By;
import org.openqa.selenium.Keys;
import org.openqa.selenium.WebDriver;
import org.openqa.selenium.WebElement;
import org.openqa.selenium.chrome.ChromeDriver;
import org.openqa.selenium.support.ui.Select;

public class HandlingAllDropdownEndToEnd {
	
	public static void main(String[] args) throws InterruptedException {
	
	WebDriver driver = new ChromeDriver();
	driver.get("https://rahulshettyacademy.com/dropdownsPractise/");	
	driver.manage().window().maximize();
	Thread.sleep(3000);
	
	WebElement departureDropdown = driver.findElement(By.id("ctl00_mainContent_ddl_originStation1_CTXT"));
    departureDropdown.click();
	Thread.sleep(3000);
	
	WebElement departureCity = driver.findElement(By.xpath("//a[@value='BLR']"));
    departureCity.click();
    Thread.sleep(2000);
	
    WebElement arrivalDropdown = driver.findElement(By.id("ctl00_mainContent_ddl_destinationStation1_CTXT"));
    arrivalDropdown.click();
    Thread.sleep(3000);
	
    WebElement arrivalCity = driver.findElement(By.xpath("//a[@value='MAA']"));
    arrivalCity.click();
    Thread.sleep(2000);
    
    WebElement departureDate = driver.findElement(By.xpath("//input[@id='ctl00_mainContent_view_date1']"));
    departureDate.click();
    Thread.sleep(1000);

    WebElement specificDate = driver.findElement(By.xpath("//a[text()='3']"));
    specificDate.click();
    Thread.sleep(1000);

	
	
}

}
