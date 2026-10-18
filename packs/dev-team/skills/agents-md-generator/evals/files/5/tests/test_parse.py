from sensor_ingest.parse import parse_line


def test_parse_line():
    r = parse_line("EASTMOOR-2,2026-09-01T10:00:00,41.5,3.2\n")
    assert r.station == "EASTMOOR-2"
    assert r.flow_lps == 41.5
