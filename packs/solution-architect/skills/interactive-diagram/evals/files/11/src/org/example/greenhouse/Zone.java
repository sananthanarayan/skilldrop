package org.example.greenhouse;

import java.util.ArrayList;
import java.util.List;

/** One bench or bed. Sensors are created by the hardware layer and attached here. */
public class Zone {
    private final String label;
    private final List<Sensor> sensors = new ArrayList<>();

    Zone(String label) {
        this.label = label;
    }

    public String label() {
        return label;
    }

    public void attach(Sensor sensor) {
        sensors.add(sensor);
    }

    public List<Sensor> sensors() {
        return List.copyOf(sensors);
    }
}
