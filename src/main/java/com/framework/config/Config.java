package com.framework.config;

import java.io.IOException;
import java.io.InputStream;
import java.util.Properties;

/**
 * Central config loader.
 *
 * Reads from: src/test/resources/config/application-{env}.properties
 * Environment is set via Maven:  -Denv=dev  (default: dev)
 *
 * To switch service or environment — only change the properties file.
 * Zero Java code changes needed.
 *
 * Usage:
 *   Config.get("db.url")
 *   Config.get("api.baseUrl")
 */
public class Config {

    private static final Properties PROPS = new Properties();
    private static final String ENV = System.getProperty("env", "dev").toLowerCase();

    static {
        String file = "config/application-" + ENV + ".properties";
        try (InputStream is = Config.class.getClassLoader().getResourceAsStream(file)) {
            if (is == null) throw new RuntimeException("Config file not found: " + file);
            PROPS.load(is);
        } catch (IOException e) {
            throw new RuntimeException("Failed to load: " + file, e);
        }
    }

    public static String get(String key) {
        String v = PROPS.getProperty(key);
        if (v == null) throw new RuntimeException("Missing config key: [" + key + "] env=[" + ENV + "]");
        return v.trim();
    }

    public static String get(String key, String defaultValue) {
        return PROPS.getProperty(key, defaultValue).trim();
    }

    public static String getEnv() { return ENV; }
}
