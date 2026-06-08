package com.enterprise.automation.services;

import com.enterprise.automation.config.EnvironmentConfig;
import com.enterprise.automation.utils.ConfigLoader;
import io.restassured.RestAssured;
import io.restassured.response.Response;

import java.util.Map;

public final class ApiService {
    private static final EnvironmentConfig config = ConfigLoader.load();
    private Response lastResponse;

    public Response get(String path, Map<String, String> headers) {
        String baseUrl = config.getApi().getBaseUrl();
        RestAssured.baseURI = baseUrl;
        if (headers == null) {
            headers = config.getApi().getDefaultHeaders();
        }
        lastResponse = RestAssured.given()
                .headers(headers)
                .when()
                .get(path)
                .then()
                .extract()
                .response();
        return lastResponse;
    }

    public Response getLastResponse() {
        return lastResponse;
    }
}
