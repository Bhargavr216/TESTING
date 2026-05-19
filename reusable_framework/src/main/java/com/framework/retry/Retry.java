package com.framework.retry;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

/**
 * Polling retry utility for async validations.
 *
 * Use when a DB record or API status takes time to reach the expected state.
 *
 * Usage:
 *   Retry.poll(5, 10, () -> {
 *       String status = db.readColumn("fsm.fsm_job_queue_arch", "id", "EVT-001", "job_status");
 *       assertThat(status).isEqualTo("SUCCESS");
 *   });
 *
 * This retries up to 5 times, waiting 10 seconds between each attempt.
 */
public class Retry {

    private static final Logger log = LoggerFactory.getLogger(Retry.class);

    @FunctionalInterface
    public interface Block { void run() throws Exception; }

    /**
     * @param maxAttempts     total number of tries
     * @param intervalSeconds wait between tries
     * @param block           the assertion — throw any exception to signal not-yet-ready
     */
    public static void poll(int maxAttempts, int intervalSeconds, Block block) throws Exception {
        Exception last = null;
        for (int i = 1; i <= maxAttempts; i++) {
            try {
                log.info("[Retry] Attempt {}/{}", i, maxAttempts);
                block.run();
                log.info("[Retry] Passed on attempt {}", i);
                return;
            } catch (Exception | AssertionError e) {
                last = (e instanceof Exception ex) ? ex : new RuntimeException(e);
                log.warn("[Retry] Attempt {} failed: {}", i, e.getMessage());
                if (i < maxAttempts) Thread.sleep(intervalSeconds * 1000L);
            }
        }
        throw new AssertionError("All " + maxAttempts + " attempts failed. Last: " +
            (last != null ? last.getMessage() : "unknown"), last);
    }
}
