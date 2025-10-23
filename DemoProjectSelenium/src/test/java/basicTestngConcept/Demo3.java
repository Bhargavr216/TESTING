package basicTestngConcept;

import org.testng.annotations.Test;
import org.testng.annotations.Test;
import org.testng.annotations.Test;

public class Demo3 
{
	@Test(priority = 4)
	public void ClickCheckbox()
	{
		System.out.println("Code to click on checkbox");
	}
	
	@Test(priority = 2)
	public void enterUsername()
	{
		System.out.println("code to enter username");
	}
	
	@Test(priority = 3)
	public void enterPassword()
	{
		System.out.println("Code to enter password");
	}
	
	@Test(priority = 1)
	public void launchBrowser()
	{
		System.out.println("Code to launch the browser");
	}
	
	@Test(priority = 5)
	public void closeBrowser()
	{
		System.out.println("Code to close the browser");
	}

}
