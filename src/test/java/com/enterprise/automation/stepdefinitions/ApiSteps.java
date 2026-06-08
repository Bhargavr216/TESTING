package com.enterprise.automation.stepdefinitions;

import com.enterprise.automation.services.ApiService;
import com.enterprise.automation.utils.JsonPathUtils;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import io.cucumber.java.en.Then;
import io.restassured.builder.ResponseBuilder;
import io.restassured.response.Response;
import io.restassured.module.jsv.JsonSchemaValidator;

import java.io.File;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertNotNull;

public class ApiSteps {
    private final ApiService apiService = new ApiService();

    @Then("Validate the get api {string} status should be {string}")
    public void validateGetApiStatus(String path, String expectedStatus) {
        Response response = apiService.get(path, null);
        assertEquals("Unexpected API status code", Integer.parseInt(expectedStatus), response.statusCode());
    }

    @Then("Validate the get api {string} response schema matches the {string}")
    public void validateGetApiResponseSchema(String path, String schemaFile) {
        Response response = apiService.get(path, null);
        String schemaPath = "expected/schemas/" + schemaFile;
        response.then().assertThat().body(JsonSchemaValidator.matchesJsonSchema(new File(schemaPath)));
    }

    @Then("validate the get api {string} response data should contains {string} should be {string}")
    public void validateGetApiResponseData(String path, String jsonPath, String expectedValue) {
        Response response = apiService.get(path, null);
        String actual = response.jsonPath().getString(jsonPath);
        assertEquals("JSON path value mismatch", expectedValue, actual);
    }

    static void validateJsonSchema(String json, String schemaPath) {
        try {
            Response fake = new ResponseBuilder().setBody(json).setStatusCode(200).build();
            fake.then().assertThat().body(JsonSchemaValidator.matchesJsonSchema(new File(schemaPath)));
        } catch (Exception ex) {
            throw new IllegalStateException("JSON schema validation failed: " + ex.getMessage(), ex);
        }
    }

    static void validateJsonPathValue(String json, String jsonPath, String expectedValue) {
        try {
            ObjectMapper mapper = new ObjectMapper();
            JsonNode root = mapper.readTree(json);
            String actual = JsonPathUtils.readJsonPath(root, jsonPath);
            assertEquals("JSON path value mismatch", expectedValue, actual);
        } catch (Exception ex) {
            throw new IllegalStateException("JSON path validation failed: " + ex.getMessage(), ex);
        }
    }
}
