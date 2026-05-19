package basicTestngConcept;

import org.testng.annotations.Test;
import org.testng.annotations.Test;
import org.testng.annotations.Test;

public class GroupingDemo {

	@Test(groups = "smoke")
	public void m1()
	{
		System.out.println("m1");
	}
	@Test(groups = "smoke")
	public void m2()
	{
		System.out.println("m2");
	}
	@Test(groups = "regression")
	public void m3()
	{
		System.out.println("m3");
	}
	
	
}
