package com.framework.validators.db;

import com.framework.config.Config;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.sql.*;
import java.util.HashMap;
import java.util.Map;

/**
 * Generic JDBC database validator.
 *
 * Works with ANY schema.table (e.g. fsm.fsm_job_queue, mfs.mfs_job_queue).
 * All queries use PreparedStatement — SQL injection safe.
 *
 * Config keys (application-{env}.properties):
 *   db.url      = jdbc:sqlserver://host:1433;databaseName=MyDB;encrypt=true
 *   db.username = myuser
 *   db.password = mypassword
 */
public class DbValidator {

    private static final Logger log = LoggerFactory.getLogger(DbValidator.class);
    private Connection conn;

    // ── Connection ────────────────────────────────────────────────

    public void connect() throws SQLException {
        conn = DriverManager.getConnection(
            Config.get("db.url"),
            Config.get("db.username"),
            Config.get("db.password")
        );
        log.info("[DB] Connected to: {}", Config.get("db.url"));
    }

    public void close() {
        try { if (conn != null && !conn.isClosed()) { conn.close(); log.info("[DB] Closed."); } }
        catch (SQLException e) { log.warn("[DB] Close error", e); }
    }

    // ── Core methods ──────────────────────────────────────────────

    /** Returns true if at least one row matches keyCol = keyVal. */
    public boolean rowExists(String table, String keyCol, String keyVal) throws SQLException {
        String sql = "SELECT COUNT(1) FROM " + id(table) + " WHERE " + id(keyCol) + " = ?";
        try (PreparedStatement ps = conn.prepareStatement(sql)) {
            ps.setString(1, keyVal);
            try (ResultSet rs = ps.executeQuery()) {
                rs.next();
                int count = rs.getInt(1);
                log.info("[DB] rowExists [{}] {}={} -> {}", table, keyCol, keyVal, count > 0);
                return count > 0;
            }
        }
    }

    /** Returns the exact row count matching keyCol = keyVal. */
    public int rowCount(String table, String keyCol, String keyVal) throws SQLException {
        String sql = "SELECT COUNT(1) FROM " + id(table) + " WHERE " + id(keyCol) + " = ?";
        try (PreparedStatement ps = conn.prepareStatement(sql)) {
            ps.setString(1, keyVal);
            try (ResultSet rs = ps.executeQuery()) {
                rs.next();
                int count = rs.getInt(1);
                log.info("[DB] rowCount [{}] {}={} -> {}", table, keyCol, keyVal, count);
                return count;
            }
        }
    }

    /**
     * Returns a single row as Map<columnName(lowercase), value>.
     * DB null becomes the string "NULL".
     * Throws AssertionError if no row found.
     */
    public Map<String, String> queryRow(String table, String keyCol, String keyVal) throws SQLException {
        String sql = "SELECT * FROM " + id(table) + " WHERE " + id(keyCol) + " = ?";
        log.info("[DB] queryRow: {} [{}]", sql, keyVal);
        try (PreparedStatement ps = conn.prepareStatement(sql)) {
            ps.setString(1, keyVal);
            try (ResultSet rs = ps.executeQuery()) {
                if (!rs.next()) throw new AssertionError(
                    "[DB] No row in [" + table + "] where [" + keyCol + "]=[" + keyVal + "]");
                return toMap(rs);
            }
        }
    }

    /** Reads a single column value from a matching row. Returns "NULL" for DB nulls. */
    public String readColumn(String table, String keyCol, String keyVal, String col) throws SQLException {
        return queryRow(table, keyCol, keyVal).getOrDefault(col.toLowerCase(), "NULL");
    }

    // ── Helpers ───────────────────────────────────────────────────

    private Map<String, String> toMap(ResultSet rs) throws SQLException {
        ResultSetMetaData m = rs.getMetaData();
        Map<String, String> row = new HashMap<>();
        for (int i = 1; i <= m.getColumnCount(); i++)
            row.put(m.getColumnName(i).toLowerCase(), rs.getString(i) == null ? "NULL" : rs.getString(i));
        return row;
    }

    /** Validates SQL identifiers — only alphanumeric, underscore, dot allowed. */
    private String id(String s) {
        if (!s.matches("[a-zA-Z0-9_.]+"))
            throw new IllegalArgumentException("Unsafe SQL identifier: " + s);
        return s;
    }
}
