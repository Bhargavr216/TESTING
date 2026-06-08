package com.enterprise.automation.utils;

public final class ContainerManager {
    private static final ThreadLocal<ServiceContainer> TL = new ThreadLocal<>();

    private ContainerManager() {}
   public static ServiceContainer current() {
        ServiceContainer c = TL.get();
        if (c == null) {
            c = new ServiceContainer();
            TL.set(c);
        }
        return c;
    }

    public static void reset() {
        ServiceContainer c = TL.get();
        if (c != null) {
            try {
                c.close();
            } finally {
                TL.remove();
            }
        }
    }
}
