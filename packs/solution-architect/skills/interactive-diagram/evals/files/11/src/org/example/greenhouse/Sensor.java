package org.example.greenhouse;

/** Anything that can be polled for a single numeric reading. */
public interface Sensor {
    String id();

    double read();

    boolean isOutOfRange(double value);
}
