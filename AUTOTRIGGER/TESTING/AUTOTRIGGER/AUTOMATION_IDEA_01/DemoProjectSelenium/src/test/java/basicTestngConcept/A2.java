package basicTestngConcept;

import org.testng.annotations.Test;
import org.testng.Assert;
import org.testng.annotations.Test;

public class A2 {

	@Test
	public void m2()
	{
		Assert.assertNotEquals("chandresh", "Harish");
		System.out.println("Test Case Passed");
	}
}
