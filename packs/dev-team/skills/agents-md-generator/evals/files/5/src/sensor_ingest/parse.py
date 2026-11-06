from datetime import datetime

from pydantic import BaseModel


class Reading(BaseModel):
    station: str
    taken_at: datetime
    flow_lps: float
    pressure_bar: float


def parse_line(line: str) -> Reading:
    station, ts, flow, pressure = line.strip().split(",")
    return Reading(
        station=station,
        taken_at=datetime.fromisoformat(ts),
        flow_lps=float(flow),
        pressure_bar=float(pressure),
    )
