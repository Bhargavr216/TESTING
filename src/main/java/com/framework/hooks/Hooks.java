package com.framework.hooks;

import com.framework.context.ScenarioContext;
import com.framework.validators.db.DbValidator;
import com.framework.validators.eventhub.EventHubPublisher;
import io.cucumber.java.After;
import io.cucumber.java.Before;
import io.cucumber.java.Scenario;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.util.Collection;

/**
 * Runs before and after every scenario automatically.
 *
 * @Before  — clears context, reads @Retry tags
 * @After   — closes DB + EventHub, logs result
 */
public class Hooks {

    private static final Logger log = LoggerFactory.getLogger(Hooks.class);

    private final ScenarioContext ctx;
    private final DbValidator db;
    private final EventHubPublisher hub;

    public Hooks(ScenarioContext ctx, DbValidator db, EventHubPublisher hub) {
        this.ctx = ctx;
        this.db  = db;
        this.hub = hub;
    }

    @Before
    public void before(Scenario s) {
        log.info("▶ START: {}", s.getName());
        ctx.clear();
        readRetryTags(s.getSourceTagNames());
    }

    @After
    public void after(Scenario s) {
        db.close();
        hub.close();
        if (s.isFailed()) log.error("✖ FAILED: {}", s.getName());
        else              log.info ("✔ PASSED: {}", s.getName());
    }

    // Reads @Retry @RetryCount(5) @RetryInterval(10) tags into context
    private void readRetryTags(Collection<String> tags) {
        if (!tags.contains("@Retry")) return;
        ctx.set("retry.enabled", true);
        int count = tags.stream().filter(t -> t.startsWith("@RetryCount("))
            .map(t -> t.replaceAll("[^0-9]", "")).mapToInt(Integer::parseInt).findFirst().orElse(3);
        int interval = tags.stream().filter(t -> t.startsWith("@RetryInterval("))
            .map(t -> t.replaceAll("[^0-9]", "")).mapToInt(Integer::parseInt).findFirst().orElse(10);
        ctx.set("retry.count",    count);
        ctx.set("retry.interval", interval);
        log.info("[Retry] count={} interval={}s", count, interval);
    }
}
