package com.enterprise.automation.runner;

import io.cucumber.testng.AbstractTestNGCucumberTests;
import io.cucumber.testng.CucumberOptions;

@CucumberOptions(
        features = "src/test/resources/features",
        glue = "com.enterprise.automation.stepdefinitions",
        plugin = {"pretty"}
)
public class TestNGCucumberRunner extends AbstractTestNGCucumberTests {
}
