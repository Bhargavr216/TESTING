package com.bhargav.automation.tests;

import java.io.IOException;

import org.testng.Assert;
import org.testng.annotations.DataProvider;
import org.testng.annotations.Parameters;
import org.testng.annotations.Test;

import com.bhargav.automation.base.BaseTest;
import com.bhargav.automation.pages.LoginPage;
import com.bhargav.automation.utils.ExcelUtils;
import com.bhargav.automation.utils.ExtentReportManager;
import com.bhargav.automation.utils.Log;

public class LoginTest extends BaseTest {
	
	@DataProvider(name="LoginData")
	public Object[][] getLoginData() throws IOException{
		
		String filePath = System.getProperty("user.dir")+"/testdata/TestData.xlsx";
		ExcelUtils.loadExcel(filePath, "Sheet1");
		int rowCount = ExcelUtils.getRowCount();
		Object[][] data = new Object[rowCount-1][2];
		
		for(int i=1; i<rowCount; i++) {
			data[i-1][0] = ExcelUtils.getCellData(i, 0);
			data[i-1][1] = ExcelUtils.getCellData(i, 1);
		}
		ExcelUtils.closeExcel();
		return data;
	}
	
	
	@DataProvider(name="LoginData2")
	public Object[][] getData(){
		
		return new Object[][] {
			{"user1","pass1"},
			{"user2","pass2"},
			{"user3","pass3"}
		};
	}
	
	

	@Test(priority = 1, description = "Valid Login Test - End to End")
	public void testValidLogin() {
		Log.info("Starting valid login test...");
		test = ExtentReportManager.createTest("Valid Login Test - End to End");

		test.info("Navigating to login page");
		LoginPage loginPage = new LoginPage(driver);

		Log.info("Entering valid credentials");
		test.info("Entering valid credentials");
		loginPage.enterUsername("admin@yourstore.com");
		loginPage.enterPassword("admin");
		
		test.info("Clicking on Login button");
		loginPage.clickLogin();

		Log.info("Verifying successful login");
		test.info("Verifying page title after login");
		String actualTitle = driver.getTitle();
		System.out.println("Page title after login: " + actualTitle);
		
		Assert.assertTrue(actualTitle.contains("Dashboard") || actualTitle.contains("Admin"), 
			"Login failed - Expected dashboard or admin page, but got: " + actualTitle);

		test.pass("Valid login test completed successfully");
		Log.info("Valid login test completed successfully");
	}

	@Test(priority = 2, description = "Invalid Login Test - Wrong Password")
	public void testInvalidLoginWrongPassword() {
		Log.info("Starting invalid login test with wrong password...");
		test = ExtentReportManager.createTest("Invalid Login Test - Wrong Password");

		test.info("Navigating to login page");
		LoginPage loginPage = new LoginPage(driver);

		Log.info("Entering invalid credentials");
		test.info("Entering invalid password");
		loginPage.enterUsername("admin@yourstore.com");
		loginPage.enterPassword("wrongpassword");
		
		test.info("Clicking on Login button");
		loginPage.clickLogin();

		Log.info("Verifying login failure");
		test.info("Verifying error message or login page remains");
		String actualTitle = driver.getTitle();
		System.out.println("Page title after invalid login: " + actualTitle);
		
		Assert.assertTrue(actualTitle.contains("Login") || actualTitle.contains("Sign in"), 
			"Expected to remain on login page, but got: " + actualTitle);

		test.pass("Invalid login test completed successfully");
		Log.info("Invalid login test completed successfully");
	}

	@Test(priority = 3, description = "Invalid Login Test - Wrong Username")
	public void testInvalidLoginWrongUsername() {
		Log.info("Starting invalid login test with wrong username...");
		test = ExtentReportManager.createTest("Invalid Login Test - Wrong Username");

		test.info("Navigating to login page");
		LoginPage loginPage = new LoginPage(driver);

		Log.info("Entering invalid credentials");
		test.info("Entering invalid username");
		loginPage.enterUsername("wronguser@yourstore.com");
		loginPage.enterPassword("admin");
		
		test.info("Clicking on Login button");
		loginPage.clickLogin();

		Log.info("Verifying login failure");
		test.info("Verifying error message or login page remains");
		String actualTitle = driver.getTitle();
		System.out.println("Page title after invalid login: " + actualTitle);
		
		Assert.assertTrue(actualTitle.contains("Login") || actualTitle.contains("Sign in"), 
			"Expected to remain on login page, but got: " + actualTitle);

		test.pass("Invalid username test completed successfully");
		Log.info("Invalid username test completed successfully");
	}

	@Test(priority = 4, description = "Empty Fields Login Test")
	public void testEmptyFieldsLogin() {
		Log.info("Starting empty fields login test...");
		test = ExtentReportManager.createTest("Empty Fields Login Test");

		test.info("Navigating to login page");
		LoginPage loginPage = new LoginPage(driver);

		Log.info("Attempting login with empty fields");
		test.info("Leaving username and password fields empty");
		loginPage.enterUsername("");
		loginPage.enterPassword("");
		
		test.info("Clicking on Login button");
		loginPage.clickLogin();

		Log.info("Verifying login failure");
		test.info("Verifying that login fails with empty fields");
		String actualTitle = driver.getTitle();
		System.out.println("Page title with empty fields: " + actualTitle);
		
		Assert.assertTrue(actualTitle.contains("Login") || actualTitle.contains("Sign in"), 
			"Expected to remain on login page with empty fields, but got: " + actualTitle);

		test.pass("Empty fields test completed successfully");
		Log.info("Empty fields test completed successfully");
	}

	@Test(priority = 5, description = "Data Driven Login Test", dataProvider = "LoginData2")
	public void testDataDrivenLogin(String username, String password) {
		Log.info("Starting data driven login test with: " + username);
		test = ExtentReportManager.createTest("Data Driven Login Test - " + username);

		test.info("Navigating to login page");
		LoginPage loginPage = new LoginPage(driver);

		Log.info("Entering test data");
		test.info("Entering username: " + username);
		loginPage.enterUsername(username);
		loginPage.enterPassword(password);
		
		test.info("Clicking on Login button");
		loginPage.clickLogin();

		Log.info("Verifying login result");
		test.info("Verifying login result for: " + username);
		String actualTitle = driver.getTitle();
		System.out.println("Page title for " + username + ": " + actualTitle);
		
		if (username.equals("admin@yourstore.com") && password.equals("admin")) {
			Assert.assertTrue(actualTitle.contains("Dashboard") || actualTitle.contains("Admin"), 
				"Valid credentials should login successfully");
			test.pass("Data driven login successful for valid credentials");
		} else {
			Assert.assertTrue(actualTitle.contains("Login") || actualTitle.contains("Sign in"), 
				"Invalid credentials should remain on login page");
			test.pass("Data driven login correctly failed for invalid credentials");
		}

		Log.info("Data driven login test completed for: " + username);
	}

	@Test(priority = 6, description = "End to End User Journey Test")
	public void testEndToEndUserJourney() {
		Log.info("Starting end-to-end user journey test...");
		test = ExtentReportManager.createTest("End to End User Journey Test");

		test.info("Step 1: Navigate to login page");
		LoginPage loginPage = new LoginPage(driver);
		Assert.assertTrue(driver.getCurrentUrl().contains("login"), "Should be on login page");

		test.info("Step 2: Perform valid login");
		loginPage.enterUsername("admin@yourstore.com");
		loginPage.enterPassword("admin");
		loginPage.clickLogin();

		test.info("Step 3: Verify successful login");
		Log.info("Waiting for page to load after login...");
		try {
			Thread.sleep(3000);
		} catch (InterruptedException e) {
			Log.error("Thread sleep interrupted: " + e.getMessage());
		}
		
		String currentUrl = driver.getCurrentUrl();
		String pageTitle = driver.getTitle();
		System.out.println("Current URL after login: " + currentUrl);
		System.out.println("Page title after login: " + pageTitle);

		Assert.assertTrue(currentUrl.contains("admin") || pageTitle.contains("Dashboard") || pageTitle.contains("Admin"), 
			"Should be redirected to admin dashboard after successful login");

		test.info("Step 4: Verify user is logged in");
		Assert.assertFalse(currentUrl.contains("login"), "Should not be on login page after successful login");

		test.pass("End-to-end user journey test completed successfully");
		Log.info("End-to-end user journey test completed successfully");
	}


}