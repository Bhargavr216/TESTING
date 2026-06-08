package com.enterprise.automation.runner;

import io.cucumber.junit.Cucumber;
import io.cucumber.junit.CucumberOptions;
import org.junit.runner.RunWith;

@RunWith(Cucumber.class)
@CucumberOptions(
        features = "src/test/resources/features",
        glue = "com.enterprise.automation.stepdefinitions",
        plugin = {"pretty"}
)
public class JUnitCucumberTest {
}
