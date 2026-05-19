package com.framework.validators.api;

import com.framework.config.Config;
import io.restassured.RestAssured;
import io.restassured.response.Response;
import io.restassured.specification.RequestSpecification;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.util.Map;

/**
 * Generic REST API validator.
 *
 * Config keys (application-{env}.properties):
 *   api.baseUrl   = https://your-service.com
 *   api.authToken = Bearer xyz   (optional)
 */
public class ApiValidator {

    private static final Logger log = LoggerFactory.getLogger(ApiValidator.class);
    private Response lastResponse;

    public void configure() {
        RestAssured.baseURI = Config.get("api.baseUrl");
        log.info("[API] Base URL: {}", RestAssured.baseURI);
    }

    public Response get(String endpoint)                          { return send(endpoint, "GET",  null, null); }
    public Response get(String endpoint, Map<String,String> p)   { return send(endpoint, "GET",  null, p);    }
    public Response post(String endpoint, String body)            { return send(endpoint, "POST", body, null); }
    public Response put(String endpoint, String body)             { return send(endpoint, "PUT",  body, null); }
    public Response delete(String endpoint)                       { return send(endpoint, "DELETE", null, null); }

    public int    getStatusCode()  { return lastResponse.getStatusCode(); }
    public String getBody()        { return lastResponse.getBody().asString(); }
    public Response getLastResponse() { return lastResponse; }

    /** Extracts a JSON field using dot-notation: "data.order.status" */
    public String extractField(String path) {
        Object v = lastResponse.jsonPath().get(path);
        return v == null ? "NULL" : v.toString();
    }

    private Response send(String endpoint, String method, String body, Map<String,String> params) {
        RequestSpecification req = RestAssured.given().header("Accept", "application/json");
        String token = Config.get("api.authToken", "");
        if (!token.isBlank()) req = req.header("Authorization", token);
        if (body   != null)   req = req.contentType("application/json").body(body);
        if (params != null)   req = req.queryParams(params);

        lastResponse = switch (method) {
            case "GET"    -> req.get(endpoint).then().extract().response();
            case "POST"   -> req.post(endpoint).then().extract().response();
            case "PUT"    -> req.put(endpoint).then().extract().response();
            case "DELETE" -> req.delete(endpoint).then().extract().response();
            default -> throw new IllegalArgumentException("Unknown method: " + method);
        };
        log.info("[API] {} {} -> {}", method, endpoint, lastResponse.getStatusCode());
        return lastResponse;
    }
}
