package com.framework.context;

import java.util.HashMap;
import java.util.Map;

/**
 * Shared data store for one scenario.
 *
 * PicoContainer creates one instance per scenario and injects it into
 * every step class that needs it. This is how step classes share data
 * (e.g. a WHEN step stores a DB row, a THEN step reads it) without
 * being coupled to each other.
 */
public class ScenarioContext {

    private final Map<String, Object> store = new HashMap<>();

    public void set(String key, Object value) { store.put(key, value); }

    @SuppressWarnings("unchecked")
    public <T> T get(String key) { return (T) store.get(key); }

    public boolean has(String key) { return store.containsKey(key); }

    public void clear() { store.clear(); }
}
