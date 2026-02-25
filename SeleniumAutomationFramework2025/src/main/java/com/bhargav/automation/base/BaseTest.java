package com.bhargav.automation.base;

import org.openqa.selenium.WebDriver;
import org.openqa.selenium.chrome.ChromeDriver;
import org.testng.ITestResult;
import org.testng.annotations.AfterMethod;
import org.testng.annotations.AfterSuite;
import org.testng.annotations.BeforeMethod;
import org.testng.annotations.BeforeSuite;

import com.aventstack.extentreports.ExtentReports;
import com.aventstack.extentreports.ExtentTest;
import com.aventstack.extentreports.MediaEntityBuilder;

import com.bhargav.automation.utils.EmailUtils;
import com.bhargav.automation.utils.ExtentReportManager;
import com.bhargav.automation.utils.Log;

public class BaseTest {
	
	protected WebDriver driver;
	protected static ExtentReports extent;
	protected ExtentTest test;
	
	
	@BeforeSuite
	public void setupReport() {
		extent = ExtentReportManager.getReportInstance();
	}
	
	@AfterSuite
	public void teardownReport() {
		extent.flush();
	}
	
	@BeforeMethod
	public void setUp() {
		
		Log.info("Starting WebDriver...");
		driver = new ChromeDriver();
		driver.manage().window().maximize();
		Log.info("Navigating to URL...");
		driver.get("https://admin-demo.nopcommerce.com/login");
	}
	
	@AfterMethod
	public void tearDown(ITestResult result) {
		
		try {
			if(result.getStatus() == ITestResult.FAILURE) {
				Log.error("Test failed: " + result.getName());
				String screenshotPath = ExtentReportManager.captureScreenshot(driver, "TestFailure_" + result.getName());
				if (test != null) {
					test.fail("Test Failed: " + result.getThrowable().getMessage(), 
							MediaEntityBuilder.createScreenCaptureFromPath(screenshotPath).build());
				}
			} else if (result.getStatus() == ITestResult.SUCCESS) {
				Log.info("Test passed: " + result.getName());
				if (test != null) {
					test.pass("Test passed successfully");
				}
			} else if (result.getStatus() == ITestResult.SKIP) {
				Log.warn("Test skipped: " + result.getName());
				if (test != null) {
					test.skip("Test was skipped");
				}
			}
		} catch (Exception e) {
			Log.error("Error in tearDown method: " + e.getMessage());
		} finally {
			if (driver != null) {
				try {
					Log.info("Closing Browser...");
					driver.quit();
					Log.info("Browser closed successfully");
				} catch (Exception e) {
					Log.error("Error closing browser: " + e.getMessage());
				}
			}
		}
	}

}
