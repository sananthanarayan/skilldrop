# Brackwater Water — pumping station telemetry (overview for the board pack)

## Sites
We operate 37 pumping stations across three regions.

| Region | Stations |
|---|---|
| North Fells | 14 |
| Estuary | 15 |
| Southern Downs | 12 |

## How it works
1. Each pumping station has a PLC that controls the pumps and reads the level and flow sensors.
2. The PLC talks to a cellular gateway at the station. Gateways connect over a private APN to the operations data centre at Coldharbour.
3. In the data centre, an MQTT broker receives telemetry from all gateways.
4. The SCADA servers subscribe to the broker. Control-room operators use SCADA HMI workstations to watch the stations and send pump start/stop commands back down through the broker to the PLCs.
5. A historian database stores all telemetry for 10 years.
6. The historian replicates to the cloud analytics platform (Azure) through a one-way data diode, so nothing can get from the cloud back into the operations network.
7. Analysts use dashboards on the cloud platform. Corporate IT users reach the dashboards from the office network.

## Notes from operations
- The old licensed radio link at Fenwick station was decommissioned in 2024; all stations are on cellular now.
- Since June, the analytics team's model sends recommended pump setpoints back to the SCADA servers every 15 minutes, and operators approve them in the HMI.
