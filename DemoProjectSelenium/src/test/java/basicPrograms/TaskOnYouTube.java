package basicPrograms;

import org.openqa.selenium.By;
import org.openqa.selenium.WebDriver;
import org.openqa.selenium.WebElement;
import org.openqa.selenium.chrome.ChromeDriver;

public class TaskOnYouTube {

	public static void main(String[] args) throws InterruptedException {
		
		WebDriver driver= new ChromeDriver();
		
		driver.get("https://www.youtube.com/watch?v=RvtAkkOwu6g"); //get method is responsible to launch the URL "Song - Tuj Magato Me Ata | The Rahul Deshpande Collective| Priyanka Barve"
			
		driver.manage().window().maximize();
		
		Thread.sleep(3000); 
		
		WebElement play = driver.findElement(By.xpath("//button[@title='Play (k)']"));
		
		play.click();
		
		Thread.sleep(10000); 
		
		driver.close();

	}

}
