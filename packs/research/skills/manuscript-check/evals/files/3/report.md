# Pilot Evaluation of a Low-Cost Soil Moisture Sensor Network at Fernhollow Community Farm

Report to the Fernhollow Farm Trust board, October 2026
Author: Tomasz Arkwright-Bello, Fernhollow Community Farm (fernhollow.example)

## Abstract

Fernhollow Community Farm installed 24 low-cost capacitive soil moisture sensors
across its market garden in spring 2026 to see whether sensor readings could replace
the hand-held probe rounds that volunteers carry out twice a week. Over 20 weeks the
network delivered 91% of expected readings. After site calibration, sensor readings
agreed with the reference probe to within 3.1 percentage points of volumetric water
content. Irrigation water use fell by 18% compared with the same period in 2025. We
recommend extending the network to the orchard in 2027, subject to the battery and
enclosure changes set out below.

## 1. Introduction

Small farms rarely have the budget for research-grade soil sensors, which can cost
several hundred pounds per probe [1]. Low-cost capacitive sensors have become widely
available, but their readings drift with temperature and soil type [2], and few
studies have tested them on mixed vegetable plots run by volunteers.

Calibrating each sensor against a reference instrument in the soil where it will be
used improves accuracy considerably [4]. Wireless networks also bring practical
problems: radio range across polytunnels, battery life and damage from tools and
animals [3]. Community growers have reported that data dashboards are only used if
they answer a simple question, such as which beds need water today [5].

This report describes a 20-week pilot at Fernhollow and asks three questions. Did the
network deliver data reliably? After calibration, how close were sensor readings to
the reference probe? Did watering change as a result?

## 2. Methods

### 2.1 Site and sensor layout

The market garden covers 0.6 ha and is divided into 12 beds and two polytunnels. Two
sensors were installed in each bed at 10 cm and 25 cm depth, giving 24 sensors in total
(Figure 1). Each sensor was connected to a solar-powered radio node based on an open
hardware design [6].

### 2.2 Calibration and reference measurements

Each sensor was calibrated in the field against a hand-held reference probe over five
visits in April, following the two-point method of Delahaye and Strand [7]. Volunteers
then took reference readings beside every sensor twice a week for the rest of the
season. Readings were sent every 15 minutes to a gateway in the farm office and logged
to a shared spreadsheet [8].

## 3. Results

### 3.1 Data delivery

Of 322,560 expected readings, 293,530 (91%) were received. Most losses came from two
nodes in the far polytunnel, where the radio link failed during wet weather; these are
discussed in Section 4.3.

### 3.2 Agreement with the reference probe

Before calibration, the mean absolute difference between sensors and the reference
probe was 7.8 percentage points. After calibration it fell to 3.1 points, comparable
with results reported for similar sensors in loam soils [10]. Agreement was poorer at
25 cm than at 10 cm in the clay-rich beds (Table 1).

Table 1. Mean absolute difference from the reference probe (percentage points of
volumetric water content), after calibration.

| Bed soil | 10 cm | 25 cm |
|---|---|---|
| Sandy loam (beds 1-6) | 2.4 | 2.9 |
| Clay loam (beds 7-12) | 3.0 | 4.6 |
| Polytunnels | 2.7 | 3.3 |

Figure 1. Plan of the market garden showing the 24 sensor positions and the gateway.

Figure 2. Daily mean soil moisture at 10 cm in bed 4, May to September 2026, with
irrigation events marked.

## 4. Discussion

### 4.1 Reliability and accuracy

The network was reliable enough to support day-to-day watering decisions, and the
accuracy after calibration was in line with other low-cost deployments [10]. The
importance of calibrating in the actual soil, rather than using factory settings, is
consistent with earlier community trials [11].

### 4.2 Effect on watering

Irrigation water use fell by 18% compared with the same weeks in 2025. Volunteers said
the dashboard made it easier to skip beds that were still moist, which supports the
point that simple displays drive use [5]. Water savings of a similar size have been
reported on allotment sites [12].

## 5. Conclusion

A low-cost sensor network can give a small community farm usable soil moisture data,
provided each sensor is calibrated in place. We recommend extending it to the orchard
in 2027 with sealed enclosures and larger batteries.

## References

1. Abernathy-Coles R, Prasad V. The cost of soil sensing on small farms. J Field Instrum Stud. 2019;14(2):101-9.
2. Mirembe K, Laskaris T. Temperature drift in capacitive soil moisture sensors. J Field Instrum Stud. 2020;15(1):22-31.
3. Ferreira-Lund A, Odhiambo S, Kask P. Radio range and battery life in farm sensor networks. Small Farm Technol. 2021;6(3):140-52.
4. Yarborough D. Site-specific calibration of low-cost soil probes. Soil Meas Lett. 2018;9(4):77-84.
5. Castellanos M, Whitcombe J. What community growers want from farm data dashboards. Community Hortic Rev. 2022;3(1):5-18.
6. Brannigan L. An open hardware node for agricultural sensing. Open Agric Hardw. 2021;2(2):33-41.
7. Delahaye, P., & Strand, O. (2017). A two-point field calibration for capacitive soil sensors. Soil Measurement Letters, 8(2), 50-58.
8. Nakashima R, Pell G. Logging farm sensor data to shared spreadsheets. Small Farm Technol. 2020;5(1):12-19.
9. Okafor-Brandt E. Soil moisture monitoring in urban orchards. Community Hortic Rev. 2023;4(2):61-70.
10. Iversen H, Achebe-Lowe C. Accuracy of low-cost moisture sensors in loam soils. Soil Meas Lett. 2022;13(1):1-12.
11. Castellanos M, Whitcombe J. What community growers want from farm data dashboards. Community Hortic Rev. 2022;3(1):5-18.
12. Rutherford-Diaz S. Water savings from sensor-guided irrigation on allotments. Small Farm Technol. 2023;8(2):88-97.
