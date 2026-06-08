package com.enterprise.automation.stepdefinitions;

import com.enterprise.automation.services.EventHubService;
import io.cucumber.java.en.Given;

public class EventHubSteps {
    private final EventHubService eventHubService = new EventHubService();

    @Given("trigger the event payload {string}")
    public void triggerTheEventPayload(String payloadFile) {
        eventHubService.triggerPayload(payloadFile);
    }
}
