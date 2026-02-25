package basicTestngConcept;

/**
 * Created by: Bhargav Reddy
 * Project: DemoProjectSelenium - Selenium WebDriver Framework
 * Description: Basic TestNG test execution and assertions
 */

import org.testng.Assert;
import org.testng.annotations.Test;

public class A1 {

	@Test
	public void A1()
	{
		Assert.assertEquals("a", "a"); //
		System.out.println("Test case passed ");
	}
}
