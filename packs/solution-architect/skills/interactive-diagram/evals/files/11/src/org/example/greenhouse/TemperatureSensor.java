package org.example.greenhouse;

/** Air temperature in degrees Celsius. */
public class TemperatureSensor extends AbstractSensor {
    private volatile double lastCelsius;

    public TemperatureSensor(String id, double offset) {
        super(id, 12.0, 32.0, offset);
    }

    public void onSample(double celsius) {
        this.lastCelsius = celsius;
    }

    @Override
    protected double rawValue() {
        return lastCelsius;
    }
}
