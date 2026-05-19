package com.framework.steps;

import com.framework.context.ScenarioContext;
import com.framework.validators.db.DbValidator;
import com.framework.validators.json.JsonValidator;
import io.cucumber.java.en.Then;
import org.assertj.core.api.Assertions;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

/**
 * ================================================================
 * JSON VALIDATION STEPS  —  complete reusable step library
 * ================================================================
 *
 * Every step reads a JSON column from the DB (any table, any column).
 * To reuse for a different service, just change the table/column name
 * in the feature file — zero Java code changes needed.
 *
 * CATEGORIES:
 *  J. JSON column state     — empty, not empty
 *  K. JSON field value      — equals, not equals, contains, null, not null
 *  L. JSON mandatory attrs  — check required fields from a file
 *  M. JSON full match       — deep compare against expected JSON file
 *  N. JSON schema           — validate structure against schema file
 */
public class JsonSteps {

    private static final Logger log = LoggerFactory.getLogger(JsonSteps.class);

    private final ScenarioContext ctx;
    private final DbValidator db;
    private final JsonValidator json;

    public JsonSteps(ScenarioContext ctx, DbValidator db, JsonValidator json) {
        this.ctx  = ctx;
        this.db   = db;
        this.json = json;
    }

    // ================================================================
    // J. JSON COLUMN STATE CHECKS
    // ================================================================

    /**
     * Checks the JSON column is empty / null.
     * Use for failure scenarios where no response is expected.
     *
     * Examples:
     *   Then the "json_response" column in "fsm.fsm_job_queue" where "id" = "EVT-F001" should be empty JSON
     *   Then the "json_response" column in "mfs.mfs_job_queue" where "id" = "EVT-F001" should be empty JSON
     */
    @Then("the {string} column in {string} where {string} = {string} should be empty JSON")
    public void jsonColumnEmpty(String col, String table, String keyCol, String keyVal) throws Exception {
        String actual = db.readColumn(table, keyCol, keyVal, col);
        log.info("[JSON-J] Empty [{}].{}: actual=[{}]", table, col, actual);
        boolean isEmpty = actual == null || actual.equalsIgnoreCase("NULL")
            || actual.isBlank() || actual.equals("{}") || actual.equals("[]");
        Assertions.assertThat(isEmpty)
            .as("[%s].%s should be empty JSON but was [%s]", table, col, actual)
            .isTrue();
    }

    /**
     * Checks the JSON column is NOT empty (has real content).
     *
     * Examples:
     *   Then the "json_response" column in "fsm.fsm_job_queue_arch" where "id" = "EVT-001" should not be empty JSON
     */
    @Then("the {string} column in {string} where {string} = {string} should not be empty JSON")
    public void jsonColumnNotEmpty(String col, String table, String keyCol, String keyVal) throws Exception {
        String actual = db.readColumn(table, keyCol, keyVal, col);
        log.info("[JSON-J] NotEmpty [{}].{}: actual=[{}]", table, col, actual);
        Assertions.assertThat(actual)
            .as("[%s].%s should not be empty JSON", table, col)
            .isNotNull().isNotEqualToIgnoringCase("NULL").isNotBlank();
    }

    // ================================================================
    // K. JSON FIELD VALUE CHECKS
    // ================================================================

    /**
     * Reads a specific field from a JSON column and checks its value.
     * Supports dot-notation for nested fields: "order.customer.id"
     *
     * Examples:
     *   Then the "json_response" column in "fsm.fsm_job_queue_arch" where "id" = "EVT-001"
     *       field "status" should be "SUCCESS"
     *   Then the "json_response" column in "mfs.mfs_job_queue_arch" where "id" = "EVT-001"
     *       field "status" should be "SUCCESS"
     *   Then the "json_response" column in "fsm.fsm_result" where "ful_id" = "EVT-001"
     *       field "order.customer.name" should be "John Doe"
     */
    @Then("the {string} column in {string} where {string} = {string} field {string} should be {string}")
    public void jsonFieldShouldBe(String col, String table, String keyCol, String keyVal,
                                   String field, String expected) throws Exception {
        String jsonStr = db.readColumn(table, keyCol, keyVal, col);
        String actual  = json.extractField(jsonStr, field);
        log.info("[JSON-K] Field [{}]: expected=[{}] actual=[{}]", field, expected, actual);
        Assertions.assertThat(actual)
            .as("JSON field [%s] in [%s].%s", field, table, col)
            .isEqualToIgnoringCase(expected);
    }

    /**
     * Checks a JSON field does NOT equal a value.
     *
     * Examples:
     *   Then the "json_response" column in "fsm.fsm_job_queue" where "id" = "EVT-001"
     *       field "status" should not be "FAILED"
     */
    @Then("the {string} column in {string} where {string} = {string} field {string} should not be {string}")
    public void jsonFieldShouldNotBe(String col, String table, String keyCol, String keyVal,
                                      String field, String notExpected) throws Exception {
        String jsonStr = db.readColumn(table, keyCol, keyVal, col);
        String actual  = json.extractField(jsonStr, field);
        log.info("[JSON-K] NotEquals field [{}]: notExpected=[{}] actual=[{}]", field, notExpected, actual);
        Assertions.assertThat(actual)
            .as("JSON field [%s] should not be [%s]", field, notExpected)
            .isNotEqualToIgnoringCase(notExpected);
    }

    /**
     * Checks a JSON field contains a substring.
     *
     * Examples:
     *   Then the "json_response" column in "fsm.fsm_job_queue_arch" where "id" = "EVT-001"
     *       field "message" should contain "processed successfully"
     */
    @Then("the {string} column in {string} where {string} = {string} field {string} should contain {string}")
    public void jsonFieldShouldContain(String col, String table, String keyCol, String keyVal,
                                        String field, String substring) throws Exception {
        String jsonStr = db.readColumn(table, keyCol, keyVal, col);
        String actual  = json.extractField(jsonStr, field);
        log.info("[JSON-K] Contains field [{}]: substring=[{}] actual=[{}]", field, substring, actual);
        Assertions.assertThat(actual)
            .as("JSON field [%s] should contain [%s]", field, substring)
            .containsIgnoringCase(substring);
    }

    /**
     * Checks a JSON field is null or missing.
     *
     * Examples:
     *   Then the "json_response" column in "fsm.fsm_job_queue_arch" where "id" = "EVT-001"
     *       field "errorCode" should be null
     */
    @Then("the {string} column in {string} where {string} = {string} field {string} should be null")
    public void jsonFieldNull(String col, String table, String keyCol, String keyVal, String field)
            throws Exception {
        String jsonStr = db.readColumn(table, keyCol, keyVal, col);
        String actual  = json.extractField(jsonStr, field);
        log.info("[JSON-K] Null field [{}]: actual=[{}]", field, actual);
        Assertions.assertThat(actual)
            .as("JSON field [%s] should be null", field)
            .isEqualToIgnoringCase("NULL");
    }

    /**
     * Checks a JSON field is NOT null.
     *
     * Examples:
     *   Then the "json_response" column in "fsm.fsm_job_queue_arch" where "id" = "EVT-001"
     *       field "orderId" should not be null
     */
    @Then("the {string} column in {string} where {string} = {string} field {string} should not be null")
    public void jsonFieldNotNull(String col, String table, String keyCol, String keyVal, String field)
            throws Exception {
        String jsonStr = db.readColumn(table, keyCol, keyVal, col);
        String actual  = json.extractField(jsonStr, field);
        log.info("[JSON-K] NotNull field [{}]: actual=[{}]", field, actual);
        Assertions.assertThat(actual)
            .as("JSON field [%s] should not be null", field)
            .isNotEqualToIgnoringCase("NULL");
    }

    // ================================================================
    // L. JSON MANDATORY ATTRIBUTES
    // ================================================================

    /**
     * Checks that the JSON column contains all key-value pairs listed in a file.
     * Extra fields in the actual JSON are ignored.
     *
     * Mandatory file format: { "status": "SUCCESS", "eventType": "ORDER_CREATED" }
     *
     * Examples:
     *   Then the "json_response" column in "fsm.fsm_job_queue_arch" where "id" = "EVT-001"
     *       should contain mandatory attributes from "testdata/expected/mandatory/order_mandatory.json"
     *
     *   Then the "json_response" column in "mfs.mfs_job_queue_arch" where "id" = "EVT-001"
     *       should contain mandatory attributes from "testdata/expected/mandatory/order_mandatory.json"
     */
    @Then("the {string} column in {string} where {string} = {string} should contain mandatory attributes from {string}")
    public void jsonMandatoryAttributes(String col, String table, String keyCol,
                                         String keyVal, String mandatoryFile) throws Exception {
        String jsonStr = db.readColumn(table, keyCol, keyVal, col);
        log.info("[JSON-L] Mandatory [{}].{} vs [{}]", table, col, mandatoryFile);
        json.assertMandatoryAttributes(jsonStr, mandatoryFile);
    }

    // ================================================================
    // M. JSON FULL MATCH
    // ================================================================

    /**
     * Deep comparison of the JSON column against a full expected JSON file.
     * All fields in the expected file must match. Extra fields in actual are OK.
     *
     * Examples:
     *   Then the "json_response" column in "fsm.fsm_job_queue_arch" where "id" = "EVT-001"
     *       should match expected JSON "testdata/expected/full/order_001_expected.json"
     *
     *   Then the "json_response" column in "mfs.mfs_job_queue_arch" where "id" = "EVT-001"
     *       should match expected JSON "testdata/expected/full/order_001_expected.json"
     */
    @Then("the {string} column in {string} where {string} = {string} should match expected JSON {string}")
    public void jsonFullMatch(String col, String table, String keyCol,
                               String keyVal, String expectedFile) throws Exception {
        String jsonStr = db.readColumn(table, keyCol, keyVal, col);
        log.info("[JSON-M] Full match [{}].{} vs [{}]", table, col, expectedFile);
        json.assertFullMatch(jsonStr, expectedFile);
    }

    // ================================================================
    // N. JSON SCHEMA VALIDATION
    // ================================================================

    /**
     * Validates the JSON column against a JSON Schema (Draft-07) file.
     * Reports all schema violations at once.
     *
     * Examples:
     *   Then the "json_response" column in "fsm.fsm_job_queue_arch" where "id" = "EVT-001"
     *       should conform to schema "testdata/schemas/order_schema.json"
     *
     *   Then the "json_response" column in "mfs.mfs_job_queue_arch" where "id" = "EVT-001"
     *       should conform to schema "testdata/schemas/order_schema.json"
     */
    @Then("the {string} column in {string} where {string} = {string} should conform to schema {string}")
    public void jsonSchema(String col, String table, String keyCol,
                            String keyVal, String schemaFile) throws Exception {
        String jsonStr = db.readColumn(table, keyCol, keyVal, col);
        log.info("[JSON-N] Schema [{}].{} vs [{}]", table, col, schemaFile);
        json.assertSchema(jsonStr, schemaFile);
    }
}
