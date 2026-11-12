package org.example.greenhouse;

/** Volumetric soil moisture, percent. Fed by the ADC polling loop. */
public class SoilMoistureSensor extends AbstractSensor {
    private final int adcChannel;
    private volatile double lastSample;

    public SoilMoistureSensor(String id, int adcChannel) {
        super(id, 20.0, 60.0, 0.0);
        this.adcChannel = adcChannel;
    }

    public int adcChannel() {
        return adcChannel;
    }

    public void onSample(double percent) {
        this.lastSample = percent;
    }

    @Override
    protected double rawValue() {
        return lastSample;
    }
}
