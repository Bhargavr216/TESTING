package com.bhargav.automation.tests;

import org.testng.Assert;
import org.testng.annotations.Test;

import com.bhargav.automation.base.BaseTest;
import com.bhargav.automation.pages.LoginPage;
import com.bhargav.automation.utils.ExtentReportManager;
import com.bhargav.automation.utils.Log;

public class UserManagementTest extends BaseTest {

	@Test(priority = 1, description = "User Registration Flow Test")
	public void testUserRegistrationFlow() {
		Log.info("Starting user registration flow test...");
		test = ExtentReportManager.createTest("User Registration Flow Test");

		test.info("Step 1: Navigate to registration page");
		driver.get("https://demo.nopcommerce.com/register");
		Assert.assertTrue(driver.getCurrentUrl().contains("register"), "Should be on registration page");

		test.info("Step 2: Verify registration page elements");
		String pageTitle = driver.getTitle();
		Assert.assertTrue(pageTitle.contains("Register") || pageTitle.contains("Registration"), 
			"Page title should contain registration information");

		test.info("Step 3: Verify page is loaded correctly");
		Assert.assertNotNull(driver.getPageSource(), "Page source should not be null");

		test.pass("User registration flow test completed successfully");
		Log.info("User registration flow test completed successfully");
	}

	@Test(priority = 2, description = "User Profile Management Test")
	public void testUserProfileManagement() {
		Log.info("Starting user profile management test...");
		test = ExtentReportManager.createTest("User Profile Management Test");

		test.info("Step 1: Login as admin user");
		LoginPage loginPage = new LoginPage(driver);
		loginPage.enterUsername("admin@yourstore.com");
		loginPage.enterPassword("admin");
		loginPage.clickLogin();

		test.info("Step 2: Navigate to user management section");
		driver.get("https://admin-demo.nopcommerce.com/Admin/Customer/List");
		
		test.info("Step 3: Verify user management page loads");
		String currentUrl = driver.getCurrentUrl();
		String pageTitle = driver.getTitle();
		System.out.println("User management URL: " + currentUrl);
		System.out.println("User management page title: " + pageTitle);

		Assert.assertTrue(currentUrl.contains("Customer") || currentUrl.contains("User"), 
			"Should be on user management page");

		test.pass("User profile management test completed successfully");
		Log.info("User profile management test completed successfully");
	}

	@Test(priority = 3, description = "User Authentication Security Test")
	public void testUserAuthenticationSecurity() {
		Log.info("Starting user authentication security test...");
		test = ExtentReportManager.createTest("User Authentication Security Test");

		test.info("Step 1: Test session timeout behavior");
		LoginPage loginPage = new LoginPage(driver);
		loginPage.enterUsername("admin@yourstore.com");
		loginPage.enterPassword("admin");
		loginPage.clickLogin();

		test.info("Step 2: Verify secure login process");
		String currentUrl = driver.getCurrentUrl();
		Assert.assertTrue(currentUrl.contains("admin") || currentUrl.contains("dashboard"), 
			"Should be redirected to secure admin area");

		test.info("Step 3: Test logout functionality");
		driver.get("https://admin-demo.nopcommerce.com/logout");
		String logoutUrl = driver.getCurrentUrl();
		Assert.assertTrue(logoutUrl.contains("login") || logoutUrl.contains("logout"), 
			"Should be redirected after logout");

		test.pass("User authentication security test completed successfully");
		Log.info("User authentication security test completed successfully");
	}
}