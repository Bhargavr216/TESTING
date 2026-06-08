package com.enterprise.automation.services;

import com.enterprise.automation.config.EnvironmentConfig;
import com.enterprise.automation.config.EnvironmentConfig.DatabaseConfig;
import com.enterprise.automation.utils.ConfigLoader;

import java.sql.Connection;
import java.sql.DriverManager;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

public final class DatabaseService {
    private final DatabaseConfig config;

    public DatabaseService() {
        EnvironmentConfig envConfig = ConfigLoader.load();
        this.config = envConfig.getDatabase();
    }

    public List<Map<String, Object>> fetchRow(String sql, Object... params) {
        try (Connection connection = connection(); PreparedStatement statement = prepare(connection, sql, params); ResultSet rs = statement.executeQuery()) {
            List<Map<String, Object>> rows = new ArrayList<>();
            int columnCount = rs.getMetaData().getColumnCount();
            while (rs.next()) {
                Map<String, Object> row = new LinkedHashMap<>();
                for (int i = 1; i <= columnCount; i++) {
                    row.put(rs.getMetaData().getColumnLabel(i), rs.getObject(i));
                }
                rows.add(row);
            }
            return rows;
        } catch (SQLException ex) {
            throw new IllegalStateException("Database query failed: " + ex.getMessage(), ex);
        }
    }

    private PreparedStatement prepare(Connection connection, String sql, Object... params) throws SQLException {
        PreparedStatement statement = connection.prepareStatement(sql);
        for (int i = 0; i < params.length; i++) {
            statement.setObject(i + 1, params[i]);
        }
        return statement;
    }

    private Connection connection() throws SQLException {
        String connectionString = config.getConnectionString();
        if (connectionString == null || connectionString.isBlank()) {
            throw new IllegalStateException("Database connection string is not configured");
        }
        return DriverManager.getConnection(connectionString);
    }
}
