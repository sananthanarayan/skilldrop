package org.example.greenhouse;

/** Shared by every greenhouse on the site; created once at startup. */
public class AlertService {
    private int raised;

    public void raise(String greenhouse, String zone, String sensorId, double value) {
        raised++;
        System.out.printf("ALERT %s/%s %s=%.1f%n", greenhouse, zone, sensorId, value);
    }

    public int raisedCount() {
        return raised;
    }
}
