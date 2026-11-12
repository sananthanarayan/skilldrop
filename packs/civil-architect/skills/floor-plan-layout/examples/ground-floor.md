# Worked example: ground floor on Plot 14

## Input

> *"Lay out the ground floor for the family house. Programme is in program.json (foyer,
> living, dining, kitchen, utility, prayer room, guest toilet), footprint 10 m wide × 9 m
> deep, road on the south side, front door from the road. Keep the prayer room away from the
> kitchen and the toilet. Stair to the first floor."*

## Zoning, decided before coordinates

- Public front: foyer, then living along the road, so a guest never passes the kitchen.
- Stair beside the foyer, so the first floor is reached without crossing the living room.
- Service back: dining, kitchen, utility and toilet across the rear, with a back door from the hall for deliveries.
- Wet rooms (kitchen, utility, toilet) side by side at the back, so drains run to one side of the plot and stack under the first-floor bathrooms.
- Prayer room in the south-east corner, off the living room: an outside wall for a window, and the hall, not the kitchen or toilet, on its other side.

## First draft: the checker caught it

The first draft widened the kitchen to 3.2 m. The checker exited 1:

```text
FAIL Kitchen and Utility overlap by 0.46
FAIL Kitchen and Toilet overlap by 0.38
FAIL door 8 (Kitchen – Utility) at (6.6, 6) is not on a wall both sides share
FAIL Utility cannot be reached from an entrance
```

The extra 0.2 m pushed the kitchen into the utility and the toilet. The utility door, moved
to the kitchen's new wall, then sat inside the utility rather than on a wall the two share,
so the utility could not be reached. Kitchen back to 3.0 m (12.6 m², its target).

## `plan.json`

See [`../templates/plan.json`](../templates/plan.json), unchanged.

## Response

**Plan:** [`ground-floor.svg`](ground-floor.svg). Public rooms along the road, service
rooms across the back, the stair beside the foyer.

| Room | Size (m) | Area (m²) | Target (m²) |
|---|---|---:|---:|
| Foyer | 2.5 × 2.4 | 6.0 | 6.0 |
| Stair | 2.5 × 2.4 | 6.0 |  |
| Living | 5.4 × 4.8 | 25.9 | 25.9 |
| Prayer room | 2.1 × 2.2 | 4.6 | 4.5 |
| Dining | 3.4 × 4.2 | 14.3 | 14.0 |
| Kitchen | 3 × 4.2 | 12.6 | 12.6 |
| Utility | 1.6 × 2.3 | 3.7 | 4.0 |
| Toilet | 1.6 × 1.9 | 3.0 | 3.2 |
| Hall | 2.1 × 2.6 + 2 × 4.2 | 13.9 |  |
| **Rooms** | | **90.0** | |
| **Outline** | | **90.0** | |

PASS no overlaps, every door on a shared wall, every room reachable.

**Off target:** utility 3.7 m² against 4 (−8 %) and toilet 3.0 against 3.2 (−6 %), both inside
the 10 % tolerance, traded for keeping the toilet off the prayer room. The hall is 13.9 m²
because it doubles as the back entrance; a tighter option moves the back door to the utility
and gives the spare 4 m² to the kitchen.

**What this plan is not:** schematic; walls drawn at a nominal 230 mm; no structure, services
or bye-law check. The architect checks the toilet's ventilation and the stair's width against
the local rules.
