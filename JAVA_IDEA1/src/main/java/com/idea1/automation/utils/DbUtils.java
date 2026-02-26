package com.idea1.automation.utils;

import com.idea1.automation.model.DbConfig;
import java.sql.Connection;
import java.sql.DriverManager;
import java.sql.SQLException;

import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.sql.Statement;
import java.util.List;

public class DbUtils {
    public static Connection getConnection(DbConfig config) throws SQLException {
        String url = config.getDbConnectionString();
        if (url == null || url.isEmpty()) {
            url = String.format("jdbc:postgresql://%s:%d/%s", config.getHost(), config.getPort(), config.getDatabase());
            return DriverManager.getConnection(url, config.getUser(), config.getPassword());
        }
        return DriverManager.getConnection(url);
    }

    public static void deleteTableData(Connection conn, List<String> tables, String lookupCol, Object lookupValue) throws SQLException {
        if (tables == null || tables.isEmpty()) return;
        
        for (String table : tables) {
            String sql = String.format("DELETE FROM %s WHERE %s = ?", table, lookupCol);
            try (PreparedStatement pstmt = conn.prepareStatement(sql)) {
                pstmt.setObject(1, lookupValue);
                int rowsDeleted = pstmt.executeUpdate();
                System.out.printf("   [CLEANUP] Deleted %d rows from %s where %s=%s%n", rowsDeleted, table, lookupCol, lookupValue);
            } catch (SQLException e) {
                System.err.printf("   [CLEANUP ERROR] Failed to delete from %s: %s%n", table, e.getMessage());
                // Don't throw exception, just log and continue for other tables
            }
        }
    }
}
