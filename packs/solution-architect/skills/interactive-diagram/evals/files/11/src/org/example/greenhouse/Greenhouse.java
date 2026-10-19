package org.example.greenhouse;

import java.util.ArrayList;
import java.util.List;

/**
 * A greenhouse owns its zones and raises alerts through a shared AlertService.
 * Watering for each zone is planned by {@link WateringSchedule}.
 */
public class Greenhouse {
    private final String name;
    private final List<Zone> zones = new ArrayList<>();
    private final AlertService alerts;

    public Greenhouse(String name, AlertService alerts) {
        this.name = name;
        this.alerts = alerts;
    }

    public Zone addZone(String label) {
        Zone zone = new Zone(label);
        zones.add(zone);
        return zone;
    }

    public void checkAll() {
        for (Zone zone : zones) {
            for (Sensor sensor : zone.sensors()) {
                double value = sensor.read();
                if (sensor.isOutOfRange(value)) {
                    alerts.raise(name, zone.label(), sensor.id(), value);
                }
            }
        }
    }
}
