package com.framework.steps;

import com.framework.context.ScenarioContext;
import com.framework.validators.api.ApiValidator;
import io.cucumber.java.en.Then;
import org.assertj.core.api.Assertions;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

/**
 * ================================================================
 * API VALIDATION STEPS  —  complete reusable step library
 * ================================================================
 *
 * CATEGORIES:
 *  O. Status code checks     — exact, success (2xx), client error (4xx), server error (5xx)
 *  P. Response field checks  — equals, not equals, contains, null, not null
 *  Q. Response body checks   — not empty, contains text
 */
public class ApiSteps {

    private static final Logger log = LoggerFactory.getLogger(ApiSteps.class);

    private final ScenarioContext ctx;
    private final ApiValidator api;

    public ApiSteps(ScenarioContext ctx, ApiValidator api) {
        this.ctx = ctx;
        this.api = api;
    }

    // ================================================================
    // O. STATUS CODE CHECKS
    // ================================================================

    /**
     * Checks the HTTP response status code is exactly N.
     *
     * Examples:
     *   Then the response status should be 200
     *   Then the response status should be 201
     *   Then the response status should be 400
     *   Then the response status should be 404
     *   Then the response status should be 500
     */
    @Then("the response status should be {int}")
    public void statusShouldBe(int expected) {
        int actual = api.getStatusCode();
        log.info("[API-O] Status: expected={} actual={}", expected, actual);
        Assertions.assertThat(actual).as("HTTP status code").isEqualTo(expected);
    }

    /**
     * Checks the response is a success (2xx).
     *
     * Examples:
     *   Then the response should be successful
     */
    @Then("the response should be successful")
    public void responseShouldBeSuccessful() {
        int actual = api.getStatusCode();
        log.info("[API-O] Success check: status={}", actual);
        Assertions.assertThat(actual).as("HTTP status should be 2xx").isBetween(200, 299);
    }

    /**
     * Checks the response is a client error (4xx).
     *
     * Examples:
     *   Then the response should be a client error
     */
    @Then("the response should be a client error")
    public void responseShouldBeClientError() {
        int actual = api.getStatusCode();
        log.info("[API-O] Client error check: status={}", actual);
        Assertions.assertThat(actual).as("HTTP status should be 4xx").isBetween(400, 499);
    }

    /**
     * Checks the response is a server error (5xx).
     *
     * Examples:
     *   Then the response should be a server error
     */
    @Then("the response should be a server error")
    public void responseShouldBeServerError() {
        int actual = api.getStatusCode();
        log.info("[API-O] Server error check: status={}", actual);
        Assertions.assertThat(actual).as("HTTP status should be 5xx").isBetween(500, 599);
    }

    // ================================================================
    // P. RESPONSE FIELD CHECKS
    // ================================================================

    /**
     * Checks a JSON field in the response equals a value.
     * Supports dot-notation: "data.order.status"
     *
     * Examples:
     *   Then the response field "status" should be "SUCCESS"
     *   Then the response field "data.order.id" should be "ORD-001"
     *   Then the response field "errorCode" should be "INVALID_INPUT"
     */
    @Then("the response field {string} should be {string}")
    public void responseFieldShouldBe(String field, String expected) {
        String actual = api.extractField(field);
        log.info("[API-P] Field [{}]: expected=[{}] actual=[{}]", field, expected, actual);
        Assertions.assertThat(actual).as("Response field [%s]", field).isEqualToIgnoringCase(expected);
    }

    /**
     * Checks a response field does NOT equal a value.
     *
     * Examples:
     *   Then the response field "status" should not be "FAILED"
     */
    @Then("the response field {string} should not be {string}")
    public void responseFieldShouldNotBe(String field, String notExpected) {
        String actual = api.extractField(field);
        log.info("[API-P] NotEquals field [{}]: notExpected=[{}] actual=[{}]", field, notExpected, actual);
        Assertions.assertThat(actual).as("Response field [%s]", field).isNotEqualToIgnoringCase(notExpected);
    }

    /**
     * Checks a response field contains a substring.
     *
     * Examples:
     *   Then the response field "message" should contain "successfully processed"
     *   Then the response field "errorMessage" should contain "not found"
     */
    @Then("the response field {string} should contain {string}")
    public void responseFieldShouldContain(String field, String substring) {
        String actual = api.extractField(field);
        log.info("[API-P] Contains field [{}]: substring=[{}] actual=[{}]", field, substring, actual);
        Assertions.assertThat(actual).as("Response field [%s]", field).containsIgnoringCase(substring);
    }

    /**
     * Checks a response field is null or missing.
     *
     * Examples:
     *   Then the response field "errorCode" should be null
     *   Then the response field "data.exception" should be null
     */
    @Then("the response field {string} should be null")
    public void responseFieldNull(String field) {
        String actual = api.extractField(field);
        log.info("[API-P] Null field [{}]: actual=[{}]", field, actual);
        Assertions.assertThat(actual).as("Response field [%s] should be null", field)
            .isEqualToIgnoringCase("NULL");
    }

    /**
     * Checks a response field is NOT null.
     *
     * Examples:
     *   Then the response field "orderId" should not be null
     *   Then the response field "data.transactionId" should not be null
     */
    @Then("the response field {string} should not be null")
    public void responseFieldNotNull(String field) {
        String actual = api.extractField(field);
        log.info("[API-P] NotNull field [{}]: actual=[{}]", field, actual);
        Assertions.assertThat(actual).as("Response field [%s] should not be null", field)
            .isNotEqualToIgnoringCase("NULL");
    }

    // ================================================================
    // Q. RESPONSE BODY CHECKS
    // ================================================================

    /**
     * Checks the response body is not empty.
     *
     * Examples:
     *   Then the response body should not be empty
     */
    @Then("the response body should not be empty")
    public void responseBodyNotEmpty() {
        String body = api.getBody();
        log.info("[API-Q] Body not-empty: length={}", body.length());
        Assertions.assertThat(body).as("Response body should not be empty").isNotBlank();
    }

    /**
     * Checks the response body contains a specific text.
     *
     * Examples:
     *   Then the response body should contain "EVT-001"
     *   Then the response body should contain "ORDER_CREATED"
     */
    @Then("the response body should contain {string}")
    public void responseBodyContains(String text) {
        String body = api.getBody();
        log.info("[API-Q] Body contains: [{}]", text);
        Assertions.assertThat(body).as("Response body should contain [%s]", text).contains(text);
    }
}
