package com.idea1.automation.utils;

import com.idea1.automation.model.DbConfig;
import java.sql.Connection;
import java.sql.DriverManager;
import java.sql.SQLException;

public class DbUtils {
    public static Connection getConnection(DbConfig config) throws SQLException {
        String url = String.format("jdbc:postgresql://%s:%d/%s", config.getHost(), config.getPort(), config.getDatabase());
        return DriverManager.getConnection(url, config.getUser(), config.getPassword());
    }
}
