package com.framework.steps;

import com.framework.context.ScenarioContext;
import com.framework.retry.Retry;
import com.framework.validators.db.DbValidator;
import io.cucumber.datatable.DataTable;
import io.cucumber.java.en.And;
import io.cucumber.java.en.Then;
import org.assertj.core.api.Assertions;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.util.List;
import java.util.Map;

/**
 * ================================================================
 * DATABASE VALIDATION STEPS  —  complete reusable step library
 * ================================================================
 *
 * Every step works with ANY table and ANY column.
 * To reuse for a different service, just change the table name
 * in the feature file — zero Java code changes needed.
 *
 * CATEGORIES:
 *  A. Existence checks      — record exists / does not exist
 *  B. Row count checks      — exact count, zero rows, at least N
 *  C. Column value checks   — equals, not equals, contains, starts with
 *  D. Column null checks    — is null, is not null
 *  E. Column empty checks   — is empty, is not empty
 *  F. Numeric checks        — greater than, less than, between
 *  G. Multi-column checks   — validate many columns at once (DataTable)
 *  H. Retry / polling       — wait until column reaches expected value
 *  I. Cross-table checks    — value in table A matches value in table B
 */
public class DbSteps {

    private static final Logger log = LoggerFactory.getLogger(DbSteps.class);

    private final ScenarioContext ctx;
    private final DbValidator db;

    public DbSteps(ScenarioContext ctx, DbValidator db) {
        this.ctx = ctx;
        this.db  = db;
    }

    // ================================================================
    // A. EXISTENCE CHECKS
    // ================================================================

    /**
     * Checks a record EXISTS in any table using any key column.
     *
     * Examples:
     *   Then record with "id" = "EVT-001" should exist in "fsm.fsm_job_queue"
     *   Then record with "id" = "EVT-001" should exist in "mfs.mfs_job_queue"
     *   Then record with "ful_id" = "EVT-001" should exist in "fsm.fsm_result"
     *   Then record with "order_id" = "ORD-001" should exist in "orders.order_table"
     */
    @Then("record with {string} = {string} should exist in {string}")
    public void recordShouldExist(String keyCol, String keyVal, String table) throws Exception {
        boolean exists = db.rowExists(table, keyCol, keyVal);
        log.info("[DB-A] Exist [{}] {}={} -> {}", table, keyCol, keyVal, exists);
        Assertions.assertThat(exists)
            .as("Record [%s]=[%s] should exist in [%s]", keyCol, keyVal, table)
            .isTrue();
        // Cache row for subsequent column steps
        ctx.set("db.row",   db.queryRow(table, keyCol, keyVal));
        ctx.set("db.table", table);
        ctx.set("db.key",   keyVal);
    }

    /**
     * Checks a record does NOT exist in any table.
     *
     * Examples:
     *   Then record with "id" = "EVT-001" should NOT exist in "fsm.fsm_job_queue"
     *   Then record with "id" = "EVT-001" should NOT exist in "mfs.mfs_job_queue_arch"
     */
    @Then("record with {string} = {string} should NOT exist in {string}")
    public void recordShouldNotExist(String keyCol, String keyVal, String table) throws Exception {
        boolean exists = db.rowExists(table, keyCol, keyVal);
        log.info("[DB-A] Not-exist [{}] {}={} -> {}", table, keyCol, keyVal, exists);
        Assertions.assertThat(exists)
            .as("Record [%s]=[%s] should NOT exist in [%s]", keyCol, keyVal, table)
            .isFalse();
    }

    // ================================================================
    // B. ROW COUNT CHECKS
    // ================================================================

    /**
     * Checks the exact number of rows matching a key.
     *
     * Examples:
     *   Then table "fsm.fsm_job_queue" should have 0 records with "id" = "EVT-001"
     *   Then table "fsm.fsm_job_queue_arch" should have 1 records with "id" = "EVT-001"
     */
    @Then("table {string} should have {int} records with {string} = {string}")
    public void exactRowCount(String table, int expected, String keyCol, String keyVal) throws Exception {
        int actual = db.rowCount(table, keyCol, keyVal);
        log.info("[DB-B] Count [{}] {}={}: expected={} actual={}", table, keyCol, keyVal, expected, actual);
        Assertions.assertThat(actual)
            .as("Row count in [%s] where [%s]=[%s]", table, keyCol, keyVal)
            .isEqualTo(expected);
    }

    /**
     * Checks there are zero rows — confirms a queue was cleared.
     *
     * Examples:
     *   Then table "fsm.fsm_job_queue" should have no records with "id" = "EVT-001"
     */
    @Then("table {string} should have no records with {string} = {string}")
    public void zeroRowCount(String table, String keyCol, String keyVal) throws Exception {
        int actual = db.rowCount(table, keyCol, keyVal);
        log.info("[DB-B] Zero-count [{}] {}={}: actual={}", table, keyCol, keyVal, actual);
        Assertions.assertThat(actual)
            .as("Table [%s] should have 0 rows where [%s]=[%s]", table, keyCol, keyVal)
            .isZero();
    }

    /**
     * Checks there are at least N rows.
     *
     * Examples:
     *   Then table "fsm.fsm_job_queue_arch" should have at least 1 records with "id" = "EVT-001"
     */
    @Then("table {string} should have at least {int} records with {string} = {string}")
    public void atLeastRowCount(String table, int min, String keyCol, String keyVal) throws Exception {
        int actual = db.rowCount(table, keyCol, keyVal);
        log.info("[DB-B] AtLeast [{}] {}={}: min={} actual={}", table, keyCol, keyVal, min, actual);
        Assertions.assertThat(actual)
            .as("Table [%s] should have >= %d rows where [%s]=[%s]", table, min, keyCol, keyVal)
            .isGreaterThanOrEqualTo(min);
    }

    // ================================================================
    // C. COLUMN VALUE CHECKS
    // ================================================================

    /**
     * Checks a column equals an exact value (case-insensitive).
     *
     * Examples:
     *   Then column "job_status" in "fsm.fsm_job_queue_arch" where "id" = "EVT-001" should be "SUCCESS"
     *   Then column "job_status" in "mfs.mfs_job_queue_arch" where "id" = "EVT-001" should be "SUCCESS"
     *   Then column "status" in "fsm.fsm_result" where "ful_id" = "EVT-001" should be "SUCCESS"
     *   Then column "retry_count" in "fsm.fsm_job_queue" where "id" = "EVT-F001" should be "1"
     *   Then column "event_type" in "fsm.fsm_job_queue_arch" where "id" = "EVT-001" should be "ORDER_CREATED"
     */
    @Then("column {string} in {string} where {string} = {string} should be {string}")
    public void columnShouldBe(String col, String table, String keyCol, String keyVal, String expected)
            throws Exception {
        String actual = db.readColumn(table, keyCol, keyVal, col);
        log.info("[DB-C] [{}].{} where {}={}: expected=[{}] actual=[{}]", table, col, keyCol, keyVal, expected, actual);
        Assertions.assertThat(actual)
            .as("[%s].%s", table, col)
            .isEqualToIgnoringCase(expected);
    }

    /**
     * Checks a column does NOT equal a value.
     *
     * Examples:
     *   Then column "job_status" in "fsm.fsm_job_queue" where "id" = "EVT-001" should not be "FAILED"
     */
    @Then("column {string} in {string} where {string} = {string} should not be {string}")
    public void columnShouldNotBe(String col, String table, String keyCol, String keyVal, String notExpected)
            throws Exception {
        String actual = db.readColumn(table, keyCol, keyVal, col);
        log.info("[DB-C] NotEquals [{}].{}: notExpected=[{}] actual=[{}]", table, col, notExpected, actual);
        Assertions.assertThat(actual)
            .as("[%s].%s should not be [%s]", table, col, notExpected)
            .isNotEqualToIgnoringCase(notExpected);
    }

    /**
     * Checks a column value contains a substring.
     *
     * Examples:
     *   Then column "exception" in "fsm.fsm_job_queue" where "id" = "EVT-F001" should contain "NullPointerException"
     *   Then column "exception" in "fsm.fsm_job_queue" where "id" = "EVT-F001" should contain "Connection refused"
     */
    @Then("column {string} in {string} where {string} = {string} should contain {string}")
    public void columnShouldContain(String col, String table, String keyCol, String keyVal, String substring)
            throws Exception {
        String actual = db.readColumn(table, keyCol, keyVal, col);
        log.info("[DB-C] Contains [{}].{}: substring=[{}] actual=[{}]", table, col, substring, actual);
        Assertions.assertThat(actual)
            .as("[%s].%s should contain [%s]", table, col, substring)
            .containsIgnoringCase(substring);
    }

    /**
     * Checks a column value starts with a prefix.
     *
     * Examples:
     *   Then column "event_type" in "fsm.fsm_job_queue_arch" where "id" = "EVT-001" should start with "ORDER"
     */
    @Then("column {string} in {string} where {string} = {string} should start with {string}")
    public void columnShouldStartWith(String col, String table, String keyCol, String keyVal, String prefix)
            throws Exception {
        String actual = db.readColumn(table, keyCol, keyVal, col);
        log.info("[DB-C] StartsWith [{}].{}: prefix=[{}] actual=[{}]", table, col, prefix, actual);
        Assertions.assertThat(actual.toLowerCase())
            .as("[%s].%s should start with [%s]", table, col, prefix)
            .startsWith(prefix.toLowerCase());
    }

    // ================================================================
    // D. COLUMN NULL CHECKS
    // ================================================================

    /**
     * Checks a column IS NULL in the database.
     *
     * Examples:
     *   Then column "exception" in "fsm.fsm_job_queue_arch" where "id" = "EVT-001" should be null
     *   Then column "exception" in "mfs.mfs_job_queue_arch" where "id" = "EVT-001" should be null
     */
    @Then("column {string} in {string} where {string} = {string} should be null")
    public void columnShouldBeNull(String col, String table, String keyCol, String keyVal) throws Exception {
        String actual = db.readColumn(table, keyCol, keyVal, col);
        log.info("[DB-D] Null [{}].{}: actual=[{}]", table, col, actual);
        Assertions.assertThat(actual)
            .as("[%s].%s should be NULL", table, col)
            .isEqualToIgnoringCase("NULL");
    }

    /**
     * Checks a column is NOT NULL in the database.
     *
     * Examples:
     *   Then column "exception" in "fsm.fsm_job_queue" where "id" = "EVT-F001" should not be null
     *   Then column "json_response" in "fsm.fsm_job_queue_arch" where "id" = "EVT-001" should not be null
     */
    @Then("column {string} in {string} where {string} = {string} should not be null")
    public void columnShouldNotBeNull(String col, String table, String keyCol, String keyVal) throws Exception {
        String actual = db.readColumn(table, keyCol, keyVal, col);
        log.info("[DB-D] NotNull [{}].{}: actual=[{}]", table, col, actual);
        Assertions.assertThat(actual)
            .as("[%s].%s should not be NULL", table, col)
            .isNotEqualToIgnoringCase("NULL");
    }

    // ================================================================
    // E. COLUMN EMPTY CHECKS
    // ================================================================

    /**
     * Checks a column is empty (null, blank, "{}", or "[]").
     * Use this for failure scenarios where no response is expected.
     *
     * Examples:
     *   Then column "json_response" in "fsm.fsm_job_queue" where "id" = "EVT-F001" should be empty
     */
    @Then("column {string} in {string} where {string} = {string} should be empty")
    public void columnShouldBeEmpty(String col, String table, String keyCol, String keyVal) throws Exception {
        String actual = db.readColumn(table, keyCol, keyVal, col);
        log.info("[DB-E] Empty [{}].{}: actual=[{}]", table, col, actual);
        boolean isEmpty = actual == null || actual.equalsIgnoreCase("NULL")
            || actual.isBlank() || actual.equals("{}") || actual.equals("[]");
        Assertions.assertThat(isEmpty)
            .as("[%s].%s should be empty but was [%s]", table, col, actual)
            .isTrue();
    }

    /**
     * Checks a column is NOT empty (has a real value).
     *
     * Examples:
     *   Then column "exception" in "fsm.fsm_job_queue" where "id" = "EVT-F001" should not be empty
     *   Then column "json_response" in "fsm.fsm_job_queue_arch" where "id" = "EVT-001" should not be empty
     */
    @Then("column {string} in {string} where {string} = {string} should not be empty")
    public void columnShouldNotBeEmpty(String col, String table, String keyCol, String keyVal) throws Exception {
        String actual = db.readColumn(table, keyCol, keyVal, col);
        log.info("[DB-E] NotEmpty [{}].{}: actual=[{}]", table, col, actual);
        Assertions.assertThat(actual)
            .as("[%s].%s should not be empty", table, col)
            .isNotNull().isNotEqualToIgnoringCase("NULL").isNotBlank();
    }

    // ================================================================
    // F. NUMERIC CHECKS
    // ================================================================

    /**
     * Checks a numeric column is greater than a value.
     *
     * Examples:
     *   Then column "retry_count" in "fsm.fsm_job_queue" where "id" = "EVT-F001" should be greater than 0
     */
    @Then("column {string} in {string} where {string} = {string} should be greater than {int}")
    public void columnGreaterThan(String col, String table, String keyCol, String keyVal, int min)
            throws Exception {
        int actual = Integer.parseInt(db.readColumn(table, keyCol, keyVal, col));
        log.info("[DB-F] GreaterThan [{}].{}: min={} actual={}", table, col, min, actual);
        Assertions.assertThat(actual).as("[%s].%s > %d", table, col, min).isGreaterThan(min);
    }

    /**
     * Checks a numeric column is less than a value.
     *
     * Examples:
     *   Then column "retry_count" in "fsm.fsm_job_queue" where "id" = "EVT-F001" should be less than 5
     */
    @Then("column {string} in {string} where {string} = {string} should be less than {int}")
    public void columnLessThan(String col, String table, String keyCol, String keyVal, int max)
            throws Exception {
        int actual = Integer.parseInt(db.readColumn(table, keyCol, keyVal, col));
        log.info("[DB-F] LessThan [{}].{}: max={} actual={}", table, col, max, actual);
        Assertions.assertThat(actual).as("[%s].%s < %d", table, col, max).isLessThan(max);
    }

    /**
     * Checks a numeric column is between two values (inclusive).
     *
     * Examples:
     *   Then column "retry_count" in "fsm.fsm_job_queue" where "id" = "EVT-F001" should be between 1 and 3
     */
    @Then("column {string} in {string} where {string} = {string} should be between {int} and {int}")
    public void columnBetween(String col, String table, String keyCol, String keyVal, int min, int max)
            throws Exception {
        int actual = Integer.parseInt(db.readColumn(table, keyCol, keyVal, col));
        log.info("[DB-F] Between [{}].{}: [{},{}] actual={}", table, col, min, max, actual);
        Assertions.assertThat(actual).as("[%s].%s between %d and %d", table, col, min, max).isBetween(min, max);
    }

    // ================================================================
    // G. MULTI-COLUMN CHECKS  (DataTable)
    // ================================================================

    /**
     * Validates multiple columns at once using a DataTable.
     * Reusable for any table — just change the table/key in the step.
     *
     * Examples:
     *   Then in "fsm.fsm_job_queue_arch" where "id" = "EVT-001" the columns should be:
     *     | column      | expected      |
     *     | event_type  | ORDER_CREATED |
     *     | job_status  | SUCCESS       |
     *     | exception   | NULL          |
     *     | retry_count | 0             |
     *
     *   Then in "mfs.mfs_job_queue_arch" where "id" = "EVT-001" the columns should be:
     *     | column      | expected      |
     *     | event_type  | ORDER_CREATED |
     *     | job_status  | SUCCESS       |
     */
    @Then("in {string} where {string} = {string} the columns should be:")
    public void multiColumnCheck(String table, String keyCol, String keyVal, DataTable dt) throws Exception {
        Map<String, String> row = db.queryRow(table, keyCol, keyVal);
        for (Map<String, String> exp : dt.asMaps()) {
            String col      = exp.get("column").toLowerCase();
            String expected = exp.get("expected");
            String actual   = row.getOrDefault(col, "NULL");
            log.info("[DB-G] [{}].{}: expected=[{}] actual=[{}]", table, col, expected, actual);
            Assertions.assertThat(actual).as("[%s].%s", table, col).isEqualToIgnoringCase(expected);
        }
    }

    // ================================================================
    // H. RETRY / POLLING STEPS
    // ================================================================

    /**
     * Polls a column until it reaches the expected value.
     * Use instead of a fixed wait for async processing.
     *
     * Examples:
     *   Then column "job_status" in "fsm.fsm_job_queue_arch" where "id" = "EVT-001"
     *       should eventually be "SUCCESS" within 5 retries every 10 seconds
     *
     *   Then column "job_status" in "mfs.mfs_job_queue_arch" where "id" = "EVT-001"
     *       should eventually be "SUCCESS" within 5 retries every 10 seconds
     */
    @Then("column {string} in {string} where {string} = {string} should eventually be {string} within {int} retries every {int} seconds")
    public void columnEventuallyBe(String col, String table, String keyCol, String keyVal,
                                    String expected, int retries, int interval) throws Exception {
        Retry.poll(retries, interval, () -> {
            String actual = db.readColumn(table, keyCol, keyVal, col);
            log.info("[DB-H] Polling [{}].{}: expected=[{}] actual=[{}]", table, col, expected, actual);
            Assertions.assertThat(actual)
                .as("[%s].%s should eventually be [%s]", table, col, expected)
                .isEqualToIgnoringCase(expected);
        });
    }

    /**
     * Polls until a record appears in a table.
     *
     * Examples:
     *   Then record with "id" = "EVT-001" should eventually exist in "fsm.fsm_job_queue_arch"
     *       within 5 retries every 10 seconds
     */
    @Then("record with {string} = {string} should eventually exist in {string} within {int} retries every {int} seconds")
    public void recordEventuallyExists(String keyCol, String keyVal, String table,
                                        int retries, int interval) throws Exception {
        Retry.poll(retries, interval, () -> {
            boolean exists = db.rowExists(table, keyCol, keyVal);
            log.info("[DB-H] Polling exist [{}] {}={}: {}", table, keyCol, keyVal, exists);
            Assertions.assertThat(exists)
                .as("Record [%s]=[%s] should eventually exist in [%s]", keyCol, keyVal, table)
                .isTrue();
        });
    }

    // ================================================================
    // I. CROSS-TABLE CHECKS
    // ================================================================

    /**
     * Checks that a column value in one table matches a column value in another table.
     * Useful for verifying data consistency across tables or services.
     *
     * Examples:
     *   Then column "event_type" in "fsm.fsm_job_queue_arch" where "id" = "EVT-001"
     *       should match column "event_type" in "fsm.fsm_result" where "ful_id" = "EVT-001"
     *
     *   Then column "event_type" in "fsm.fsm_job_queue_arch" where "id" = "EVT-001"
     *       should match column "event_type" in "mfs.mfs_job_queue_arch" where "id" = "EVT-001"
     */
    @Then("column {string} in {string} where {string} = {string} should match column {string} in {string} where {string} = {string}")
    public void crossTableMatch(String col1, String table1, String key1, String val1,
                                 String col2, String table2, String key2, String val2) throws Exception {
        String v1 = db.readColumn(table1, key1, val1, col1);
        String v2 = db.readColumn(table2, key2, val2, col2);
        log.info("[DB-I] Cross-table: [{}].{}=[{}] vs [{}].{}=[{}]", table1, col1, v1, table2, col2, v2);
        Assertions.assertThat(v1)
            .as("[%s].%s should match [%s].%s", table1, col1, table2, col2)
            .isEqualToIgnoringCase(v2);
    }
}
