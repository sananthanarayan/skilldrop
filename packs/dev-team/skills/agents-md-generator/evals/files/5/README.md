# sensor-ingest

Ingests flow and pressure readings from Tidewater Regional Water's pumping stations and turns
the raw gateway files into hourly summaries for the operations dashboard.

## Development

Install dependencies, then run `make test` to run the test suite.
Format code with `black .` before committing.

## Layout

- `src/sensor_ingest/` - parsing and summarising
- `data/raw/` - raw gateway files
- `data/processed/` - hourly summaries written by the pipeline
