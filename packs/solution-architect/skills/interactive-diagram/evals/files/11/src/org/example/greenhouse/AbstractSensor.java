package org.example.greenhouse;

/**
 * Shared range checking and calibration for every sensor.
 * Subclasses only supply the raw value.
 */
public abstract class AbstractSensor implements Sensor {
    protected final String id;
    private final double min;
    private final double max;
    private final double offset;

    protected AbstractSensor(String id, double min, double max, double offset) {
        this.id = id;
        this.min = min;
        this.max = max;
        this.offset = offset;
    }

    @Override
    public String id() {
        return id;
    }

    @Override
    public final double read() {
        return rawValue() + offset;
    }

    @Override
    public boolean isOutOfRange(double value) {
        return value < min || value > max;
    }

    protected abstract double rawValue();
}
