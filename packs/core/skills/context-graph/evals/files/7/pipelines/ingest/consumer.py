"""Reads ingest.raw, normalises records, publishes to ingest.normalised."""

GROUP_ID = "ingest-normaliser"
SOURCE_TOPIC = "ingest.raw"
SINK_TOPIC = "ingest.normalised"
