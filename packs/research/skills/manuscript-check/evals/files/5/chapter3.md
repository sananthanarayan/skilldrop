# Chapter 3: Capacity fade in a shared electric cargo-bike fleet

## Abstract

Shared electric cargo bikes are spreading through European city centres, but operators have little evidence on how quickly their batteries wear out in daily commercial use. This chapter follows the 42 bikes of the Wrenhaven municipal cargo-bike scheme for 18 months, measuring usable battery capacity every month. Fleet-wide mean capacity fade over the study period was 7.9%. Bikes charged on the depot's fast chargers lost capacity faster than those on standard chargers. Capacity fade was driven mainly by cumulative charge cycles rather than calendar age. These results give operators a basis for planning battery replacement.

## 3.1 Introduction

Cargo bikes are replacing vans for many last-mile deliveries in dense urban areas [1]. Electric assistance has made them practical for heavier loads and longer routes [2], and several cities now run shared fleets for small businesses and residents [5]. Battery replacement is the largest single maintenance cost for these fleets [3], yet most published data on lithium-ion degradation comes from laboratory cycling or from private electric cars [4].

Laboratory studies show that high charging currents and high temperatures accelerate capacity fade [6]. Whether this matters in a cargo-bike fleet, where batteries are small and charging is often supervised, is not known. Fleet operators also report wide variation between nominally identical batteries [7], which makes replacement planning difficult.

This chapter asks two questions: how fast do batteries in a working shared fleet lose capacity, and does the charging regime make a difference? The fleet data and the operator interviews that motivated the study are introduced in Chapter 2; the depot charging schedule is described in Section 3.2.4.

## 3.2 Methods

### 3.2.1 Fleet and data collection

The Wrenhaven scheme operates 42 identical cargo bikes (48 V, 750 Wh lithium-ion packs) from a single depot. All bikes entered service in March 2024 with new batteries. Between April 2024 and September 2025, each battery was removed once a month and its usable capacity measured with a constant-current discharge test at 20 degrees C, following the protocol of Sandoval and Kettunen [8].

### 3.2.2 Charging regimes

For operational reasons the depot assigns bikes to one of two charging bays. Twenty-seven bikes were charged on standard 2 A chargers and fifteen on 5 A fast chargers. Assignment was fixed for the whole study period and followed the bays' original wiring rather than any property of the bikes.

### 3.2.3 Statistical analysis

Capacity fade was expressed as the percentage loss from each battery's first measured capacity. A linear mixed-effects model was fitted with capacity fade as the outcome, cumulative charge cycles, months in service and charging regime as fixed effects, and bike as a random effect [9]. Models were fitted in R.

## 3.3 Results

All 42 batteries completed the 18 months of testing. Mean capacity fade at the final test is shown by charging regime in Table 1.

Table 1. Capacity fade after 18 months by charging regime.

| Charging regime | Bikes (n) | Mean capacity fade (%) | Mean charge cycles |
|---|---|---|---|
| Standard (2 A) | 27 | 6.4 | 410 |
| Fast (5 A) | 15 | 8.1 | 455 |
| All bikes | 42 | 7.0 | 426 |

In the mixed-effects model, cumulative charge cycles were strongly associated with capacity fade, while months in service added little once cycles were accounted for (Figure 1). Fast-charged bikes lost on average 1.7 percentage points more capacity than standard-charged bikes, a difference consistent with laboratory findings [6, 11].

A Kaplan-Meier analysis of time to 80% of initial capacity found that no battery reached the threshold during the study; on current trends, median time to 80% is projected at roughly 4.5 years for standard-charged bikes.

Figure 1. Capacity fade against cumulative charge cycles for all 42 bikes, coloured by charging regime.

Figure 2. Monthly mean depot temperature, April 2024 to September 2025.

## 3.4 Discussion

The fleet's batteries are wearing more slowly than operators feared. Cycle count, not age, is the main driver, which suggests operators should rotate bikes between heavy and light routes to even out wear across the fleet [7]. The fast-charging penalty is modest but real, and the depot could reserve fast chargers for bikes needed back on the road quickly.

The main limitation is that charging regime was not randomly assigned. The bays differ in position within the depot, and bikes on the fast-charging bay may also have been used on longer routes. Future work should randomise bikes between bays.

## References

1. Ashworth P, Delacroix M. Cargo bikes and the last mile: a review. Urban Logistics Example. 2021;9(2):55-71.
2. Bramley T, Okafor N, Liu S. Electric assistance and load capacity in utility cycling. Journal of Active Transport Example. 2022;14(1):12-25.
3. Castellanos R. Maintenance costs of shared micromobility fleets. Transport Operations Example. 2023;6(3):201-214.
4. Dahlgren E, Mbeki T. Real-world battery degradation in private electric vehicles. Energy and Mobility Example. 2020;11(4):340-356.
5. Elsworth J. Shared cargo-bike schemes in European cities: an inventory. Cities in Motion Example. 2023;3(1):1-18.
6. Fontaine L, Grigoriev A. Charging current, temperature and capacity fade in lithium-ion cells. Battery Science Example. 2019;27(5):600-615.
7. Hargreaves D, Nakamura Y. Battery variability in light electric vehicle fleets. Journal of Fleet Management Example. 2024;2(2):88-97.
8. Sandoval C, Kettunen O. A field protocol for capacity testing of e-bike batteries. Cycling Engineering Example. 2022;5(1):30-41.
9. Hargreaves D, Nakamura Y. Battery variability in light electric vehicle fleets. J Fleet Manag Example. 2024;2(2):88-97.
