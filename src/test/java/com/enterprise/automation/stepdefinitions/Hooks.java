package com.enterprise.automation.stepdefinitions;

import io.cucumber.java.After;
import io.cucumber.java.Before;

public class Hooks {
    @Before
    public void beforeScenario() {
        System.out.println("[Hooks] Starting scenario");
    }

    @After
    public void afterScenario() {
        System.out.println("[Hooks] Scenario finished");
    }
}
