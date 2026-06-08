package com.enterprise.automation.utils;

import com.enterprise.automation.config.EnvironmentConfig;
import com.fasterxml.jackson.databind.ObjectMapper;

import java.io.File;
import java.nio.file.Paths;

public final class ConfigLoader {
    private static final ObjectMapper MAPPER = JsonUtils.mapper();
    private static final String CONFIG_PATH = "src/test/resources/config/env-local.json";
    private static EnvironmentConfig config;

    private ConfigLoader() {}

    public static EnvironmentConfig load() {
        if (config == null) {
            try {
                File file = Paths.get(CONFIG_PATH).toFile();
                config = MAPPER.readValue(file, EnvironmentConfig.class);
            } catch (Exception ex) {
                throw new IllegalStateException("Could not load config from " + CONFIG_PATH, ex);
            }
        }
        return config;
    }
}
