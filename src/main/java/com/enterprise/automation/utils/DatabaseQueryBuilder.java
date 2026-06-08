package com.enterprise.automation.utils;

import java.util.List;
import java.util.stream.Collectors;

public final class DatabaseQueryBuilder {
    private DatabaseQueryBuilder() {}

    public static String buildSelection(String table, List<String> columns, String lookupColumn) {
        String columnList = columns.stream()
                .map(DatabaseQueryBuilder::quoteIdentifier)
                .collect(Collectors.joining(", "));
        return String.format("SELECT %s FROM %s WHERE %s = ?", columnList, quoteIdentifier(table), quoteIdentifier(lookupColumn));
    }

    public static String buildExistenceQuery(String table, String lookupColumn) {
        return String.format("SELECT 1 FROM %s WHERE %s = ? LIMIT 1", quoteIdentifier(table), quoteIdentifier(lookupColumn));
    }

    public static String buildAuditOperationQuery(String table, String lookupColumn, String operationColumn) {
        return String.format("SELECT 1 FROM %s WHERE %s = ? AND %s = ? LIMIT 1", quoteIdentifier(table), quoteIdentifier(lookupColumn), quoteIdentifier(operationColumn));
    }

    private static String quoteIdentifier(String value) {
        return value == null ? "" : value.replaceAll("[^A-Za-z0-9_@#]", "");
    }
}
