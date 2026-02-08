package utilities;

import java.sql.*;
import java.util.*;

public class databasecolumnUtil {
    public List<Map<String, Object>> fetchByLookup(
            String host,
            int port,
            String database,
            String user,
            String password,
            String tableName,
            String idColumn,
            String idValue,
            String orderIdColumn,
            String orderIdValue
    ) throws SQLException {
        List<Map<String, Object>> rows = new ArrayList<>();
        if ((idColumn == null || idColumn.isEmpty()) && (orderIdColumn == null || orderIdColumn.isEmpty())) {
            throw new IllegalArgumentException("No lookup columns provided for table " + tableName);
        }

        StringBuilder query = new StringBuilder("SELECT * FROM " + tableName + " WHERE ");
        List<String> cols = new ArrayList<>();
        List<String> vals = new ArrayList<>();
        if (idColumn != null && !idColumn.isEmpty() && idValue != null && !idValue.isEmpty()) {
            cols.add(idColumn);
            vals.add(idValue);
        }
        if (orderIdColumn != null && !orderIdColumn.isEmpty() && orderIdValue != null && !orderIdValue.isEmpty()) {
            cols.add(orderIdColumn);
            vals.add(orderIdValue);
        }
        if (cols.isEmpty()) {
            throw new IllegalArgumentException("No lookup values available for table " + tableName);
        }
        for (int i = 0; i < cols.size(); i++) {
            if (i > 0) query.append(" OR ");
            query.append(cols.get(i)).append(" = ?");
        }

        String jdbcUrl = "jdbc:mysql://" + host + ":" + port + "/" + database + "?useSSL=false&allowPublicKeyRetrieval=true";
        // logs suppressed
        try (Connection conn = DriverManager.getConnection(jdbcUrl, user, password);
             PreparedStatement stmt = conn.prepareStatement(query.toString())) {
            for (int i = 0; i < vals.size(); i++) {
                stmt.setString(i + 1, vals.get(i));
            }
            try (ResultSet rs = stmt.executeQuery()) {
                ResultSetMetaData meta = rs.getMetaData();
                int colCount = meta.getColumnCount();
                while (rs.next()) {
                    Map<String, Object> row = new HashMap<>();
                    for (int i = 1; i <= colCount; i++) {
                        String colName = meta.getColumnLabel(i);
                        row.put(colName, rs.getObject(i));
                    }
                    rows.add(row);
                }
            }
        }
        return rows;
    }

    public List<String> listTables(String host, int port, String database, String user, String password) throws SQLException {
        List<String> tables = new ArrayList<>();
        String jdbcUrl = "jdbc:mysql://" + host + ":" + port + "/" + database + "?useSSL=false&allowPublicKeyRetrieval=true";
        String query = "SHOW TABLES";
        try (Connection conn = DriverManager.getConnection(jdbcUrl, user, password);
             PreparedStatement stmt = conn.prepareStatement(query);
             ResultSet rs = stmt.executeQuery()) {
            while (rs.next()) {
                tables.add(rs.getString(1));
            }
        }
        return tables;
    }

    public List<Map<String, Object>> fetchByIdOrOrderId(
            String host,
            int port,
            String database,
            String user,
            String password,
            String tableName,
            String idColumn,
            String orderIdColumn,
            String idValue,
            String orderIdValue
    ) throws SQLException {
        String query = "SELECT * FROM " + tableName + " WHERE " + idColumn + " = ? OR " + orderIdColumn + " = ?";
        List<Map<String, Object>> rows = new ArrayList<>();

        String jdbcUrl = "jdbc:mysql://" + host + ":" + port + "/" + database + "?useSSL=false&allowPublicKeyRetrieval=true";
        // logs suppressed
        try (Connection conn = DriverManager.getConnection(jdbcUrl, user, password);
             PreparedStatement stmt = conn.prepareStatement(query)) {
            stmt.setString(1, idValue);
            stmt.setString(2, orderIdValue);
            try (ResultSet rs = stmt.executeQuery()) {
                ResultSetMetaData meta = rs.getMetaData();
                int colCount = meta.getColumnCount();
                while (rs.next()) {
                    Map<String, Object> row = new HashMap<>();
                    for (int i = 1; i <= colCount; i++) {
                        String colName = meta.getColumnLabel(i);
                        row.put(colName, rs.getObject(i));
                    }
                    rows.add(row);
                }
            }
        }
        return rows;
    }
}
