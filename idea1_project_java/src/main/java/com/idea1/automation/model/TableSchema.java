package com.idea1.automation.model;

import java.util.List;
import java.util.Map;

public class TableSchema {
    private String primary_lookup;
    private String secondary_lookup;
    private List<List<String>> unique_constraints;
    private List<String> mandatory_columns;
    private Map<String, JsonColumnConfig> json_columns;
    private List<String> generated_columns;
    private Map<String, SemanticRule> semantic_rules;
    private String table_expectation;

    public String getPrimary_lookup() { return primary_lookup; }
    public void setPrimary_lookup(String primary_lookup) { this.primary_lookup = primary_lookup; }
    public String getSecondary_lookup() { return secondary_lookup; }
    public void setSecondary_lookup(String secondary_lookup) { this.secondary_lookup = secondary_lookup; }
    public List<List<String>> getUnique_constraints() { return unique_constraints; }
    public void setUnique_constraints(List<List<String>> unique_constraints) { this.unique_constraints = unique_constraints; }
    public List<String> getMandatory_columns() { return mandatory_columns; }
    public void setMandatory_columns(List<String> mandatory_columns) { this.mandatory_columns = mandatory_columns; }
    public Map<String, JsonColumnConfig> getJson_columns() { return json_columns; }
    public void setJson_columns(Map<String, JsonColumnConfig> json_columns) { this.json_columns = json_columns; }
    public List<String> getGenerated_columns() { return generated_columns; }
    public void setGenerated_columns(List<String> generated_columns) { this.generated_columns = generated_columns; }
    public Map<String, SemanticRule> getSemantic_rules() { return semantic_rules; }
    public void setSemantic_rules(Map<String, SemanticRule> semantic_rules) { this.semantic_rules = semantic_rules; }
    public String getTable_expectation() { return table_expectation; }
    public void setTable_expectation(String table_expectation) { this.table_expectation = table_expectation; }

    public static class JsonColumnConfig {
        private List<String> required;
        private List<String> ignored;

        public List<String> getRequired() { return required; }
        public void setRequired(List<String> required) { this.required = required; }
        public List<String> getIgnored() { return ignored; }
        public void setIgnored(List<String> ignored) { this.ignored = ignored; }
    }

    public static class SemanticRule {
        private String type;
        private Integer min;

        public String getType() { return type; }
        public void setType(String type) { this.type = type; }
        public Integer getMin() { return min; }
        public void setMin(Integer min) { this.min = min; }
    }
}
