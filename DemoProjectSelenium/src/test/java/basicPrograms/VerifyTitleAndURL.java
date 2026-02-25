package basicPrograms;

import org.openqa.selenium.WebDriver;
import org.openqa.selenium.chrome.ChromeDriver;

public class VerifyTitleAndURL {

	public static void main(String[] args) 
	{
		WebDriver driver = new ChromeDriver();// to launch the browser
		
		driver.get("https://www.nseindia.com/"); //to launch the url
		
		driver.manage().window().maximize(); // to maximize the the browser window
		
		String expected_title = "NSE - National Stock Exchange of India Ltd: Live Share/Stock Market News & Updates, Quotes- Nseindia.com";
		
		String actual_title = driver.getTitle(); //to fetch the title of the current page
		
		//System.out.println(expected_title.equals(actual_title)); // compared the fetched page...
		
		//if(expected_title==actual_title) //== is compared only the reference memory location {== is an operator that compares the memory or reference location of an object in the heap.}
		
		//if(actual_title != null && expected_title.equals(actual_title))// it check any null title and compared the title with expected and actual title
		
		if(actual_title != null && expected_title.equalsIgnoreCase(actual_title))	//equalsIgnoreCase it ignore the case
		{
			System.out.println("The title is correct");
			System.out.println("Test case Passed");
		}else 
		{
			System.out.println("The title is not correct");
			System.out.println("Test case Failed");	
		}		
		System.out.println(driver.getCurrentUrl()); //to fetch the current windows page url
		
		driver.close(); //To close all the windows that are opened by this program/class. 
	}

}
