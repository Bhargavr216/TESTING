package basicTestngConcept;

import org.testng.annotations.Test;
import org.testng.annotations.Test;
import org.testng.annotations.Test;

public class DependsOnMethod {
	
	@Test (dependsOnMethods = "enterURL")
	public void enterCredentials()
	{
		System.out.println("Code to enter the details");
	}
	@Test
	public void enterURL()
	{
		System.out.println("code to launch url");
	}

}
