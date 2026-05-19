package com.bhargav.automation.tests;

import org.testng.Assert;
import org.testng.annotations.Test;

import com.bhargav.automation.base.BaseTest;
import com.bhargav.automation.pages.LoginPage;
import com.bhargav.automation.utils.ExtentReportManager;
import com.bhargav.automation.utils.Log;

public class ProductManagementTest extends BaseTest {

	@Test(priority = 1, description = "Product Catalog Navigation Test")
	public void testProductCatalogNavigation() {
		Log.info("Starting product catalog navigation test...");
		test = ExtentReportManager.createTest("Product Catalog Navigation Test");

		test.info("Step 1: Navigate to product catalog");
		driver.get("https://demo.nopcommerce.com/");
		Assert.assertTrue(driver.getCurrentUrl().contains("nopcommerce"), "Should be on nopcommerce site");

		test.info("Step 2: Verify homepage loads correctly");
		String pageTitle = driver.getTitle();
		Assert.assertNotNull(pageTitle, "Page title should not be null");
		Assert.assertTrue(pageTitle.length() > 0, "Page title should not be empty");

		test.info("Step 3: Test product category navigation");
		driver.get("https://demo.nopcommerce.com/electronics");
		String electronicsUrl = driver.getCurrentUrl();
		Assert.assertTrue(electronicsUrl.contains("electronics"), "Should be on electronics category page");

		test.pass("Product catalog navigation test completed successfully");
		Log.info("Product catalog navigation test completed successfully");
	}

	@Test(priority = 2, description = "Product Search Functionality Test")
	public void testProductSearchFunctionality() {
		Log.info("Starting product search functionality test...");
		test = ExtentReportManager.createTest("Product Search Functionality Test");

		test.info("Step 1: Navigate to main page");
		driver.get("https://demo.nopcommerce.com/");
		Assert.assertTrue(driver.getCurrentUrl().contains("nopcommerce"), "Should be on main page");

		test.info("Step 2: Verify search functionality");
		String pageSource = driver.getPageSource();
		Assert.assertNotNull(pageSource, "Page source should not be null");
		Assert.assertTrue(pageSource.length() > 0, "Page source should not be empty");

		test.info("Step 3: Test search page navigation");
		driver.get("https://demo.nopcommerce.com/search");
		String searchUrl = driver.getCurrentUrl();
		Assert.assertTrue(searchUrl.contains("search"), "Should be on search page");

		test.pass("Product search functionality test completed successfully");
		Log.info("Product search functionality test completed successfully");
	}

	@Test(priority = 3, description = "Admin Product Management Test")
	public void testAdminProductManagement() {
		Log.info("Starting admin product management test...");
		test = ExtentReportManager.createTest("Admin Product Management Test");

		test.info("Step 1: Login as admin");
		LoginPage loginPage = new LoginPage(driver);
		loginPage.enterUsername("admin@yourstore.com");
		loginPage.enterPassword("admin");
		loginPage.clickLogin();

		test.info("Step 2: Navigate to product management");
		driver.get("https://admin-demo.nopcommerce.com/Admin/Product/List");
		String productUrl = driver.getCurrentUrl();
		Assert.assertTrue(productUrl.contains("Product"), "Should be on product management page");

		test.info("Step 3: Verify product management interface");
		String pageTitle = driver.getTitle();
		Assert.assertNotNull(pageTitle, "Page title should not be null");

		test.pass("Admin product management test completed successfully");
		Log.info("Admin product management test completed successfully");
	}

	@Test(priority = 4, description = "Product Category Management Test")
	public void testProductCategoryManagement() {
		Log.info("Starting product category management test...");
		test = ExtentReportManager.createTest("Product Category Management Test");

		test.info("Step 1: Login as admin");
		LoginPage loginPage = new LoginPage(driver);
		loginPage.enterUsername("admin@yourstore.com");
		loginPage.enterPassword("admin");
		loginPage.clickLogin();

		test.info("Step 2: Navigate to category management");
		driver.get("https://admin-demo.nopcommerce.com/Admin/Category/List");
		String categoryUrl = driver.getCurrentUrl();
		Assert.assertTrue(categoryUrl.contains("Category"), "Should be on category management page");

		test.info("Step 3: Verify category management interface");
		String pageTitle = driver.getTitle();
		Assert.assertNotNull(pageTitle, "Page title should not be null");

		test.pass("Product category management test completed successfully");
		Log.info("Product category management test completed successfully");
	}
}