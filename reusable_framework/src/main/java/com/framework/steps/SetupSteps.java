package com.framework.steps;

import com.framework.context.ScenarioContext;
import com.framework.validators.api.ApiValidator;
import com.framework.validators.db.DbValidator;
import com.framework.validators.eventhub.EventHubPublisher;
import io.cucumber.java.en.And;
import io.cucumber.java.en.Given;
import io.cucumber.java.en.When;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.io.IOException;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.util.Map;

/**
 * ================================================================
 * SETUP STEPS  —  connections, triggers, waits
 * ================================================================
 * These are GIVEN / WHEN steps that prepare the test.
 * They run before the validation (THEN) steps.
 */
public class SetupSteps {

    private static final Logger log = LoggerFactory.getLogger(SetupSteps.class);

    private final ScenarioContext ctx;
    private final DbValidator db;
    private final ApiValidator api;
    private final EventHubPublisher hub;

    public SetupSteps(ScenarioContext ctx, DbValidator db, ApiValidator api, EventHubPublisher hub) {
        this.ctx = ctx; this.db = db; this.api = api; this.hub = hub;
    }

    // ── Database ──────────────────────────────────────────────────

    /** Given I connect to the database */
    @Given("I connect to the database")
    public void connectDb() throws Exception { db.connect(); }

    // ── API ───────────────────────────────────────────────────────

    /** Given I connect to the API */
    @Given("I connect to the API")
    public void connectApi() { api.configure(); }

    /** When I call GET "/orders/status" */
    @When("I call GET {string}")
    public void callGet(String endpoint) { ctx.set("api.response", api.get(endpoint)); }

    /** When I call GET "/orders" with param "orderId" as "ORD-001" */
    @When("I call GET {string} with param {string} as {string}")
    public void callGetParam(String endpoint, String key, String val) {
        ctx.set("api.response", api.get(endpoint, Map.of(key, val)));
    }

    /** When I call POST "/orders" with body "testdata/payloads/order_001.json" */
    @When("I call POST {string} with body {string}")
    public void callPost(String endpoint, String file) throws Exception {
        ctx.set("api.response", api.post(endpoint, loadFile(file)));
    }

    /** When I call PUT "/orders/ORD-001" with body "testdata/payloads/update_001.json" */
    @When("I call PUT {string} with body {string}")
    public void callPut(String endpoint, String file) throws Exception {
        ctx.set("api.response", api.put(endpoint, loadFile(file)));
    }

    /** When I call DELETE "/orders/ORD-001" */
    @When("I call DELETE {string}")
    public void callDelete(String endpoint) { ctx.set("api.response", api.delete(endpoint)); }

    // ── Event Hub ─────────────────────────────────────────────────

    /** Given I connect to the Event Hub */
    @Given("I connect to the Event Hub")
    public void connectHub() { hub.connect(); }

    /**
     * When I send event with id "EVT-001" and type "ORDER_CREATED" from file "testdata/payloads/order_001.json"
     */
    @When("I send event with id {string} and type {string} from file {string}")
    public void sendEvent(String id, String type, String file) throws Exception {
        hub.send(id, type, file);
        ctx.set("event.id",   id);
        ctx.set("event.type", type);
    }

    // ── Wait ──────────────────────────────────────────────────────

    /** And I wait 30 seconds for processing */
    @And("I wait {int} seconds for processing")
    public void wait(int seconds) throws InterruptedException {
        log.info("[Wait] {}s...", seconds);
        Thread.sleep(seconds * 1000L);
    }

    // ── Private ───────────────────────────────────────────────────

    private String loadFile(String path) throws IOException {
        try (InputStream is = getClass().getClassLoader().getResourceAsStream(path)) {
            if (is == null) throw new IOException("File not found: " + path);
            return new String(is.readAllBytes(), StandardCharsets.UTF_8);
        }
    }
}
