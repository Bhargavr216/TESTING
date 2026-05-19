package com.framework;

import org.junit.platform.suite.api.*;

/**
 * Main test runner.
 *
 * Run all tests:
 *   mvn test
 *
 * Run by tag:
 *   mvn test -Dcucumber.filter.tags="@Smoke"
 *   mvn test -Dcucumber.filter.tags="@FSM"
 *   mvn test -Dcucumber.filter.tags="@MFS"
 *   mvn test -Dcucumber.filter.tags="@HappyPath"
 *   mvn test -Dcucumber.filter.tags="@FailurePath"
 *
 * Run for a specific environment:
 *   mvn test -Denv=uat -Dcucumber.filter.tags="@Smoke"
 */
@Suite
@IncludeEngines("cucumber")
@SelectClasspathResource("features")
@ConfigurationParameter(key = "cucumber.plugin", value =
    "pretty," +
    "html:target/reports/cucumber.html," +
    "json:target/reports/cucumber.json"
)
@ConfigurationParameter(key = "cucumber.glue",          value = "com.framework")
@ConfigurationParameter(key = "cucumber.publish.quiet", value = "true")
public class TestRunner {}
