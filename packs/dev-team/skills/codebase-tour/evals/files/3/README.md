# tidepool

Delivers webhook events to tenant endpoints, with retries.

## Configuration

Retries are set in `config.yaml`:

```yaml
max_attempts: 5
retry_delay: 2s
```

## Development

`make test` runs the full test suite, including the database tests.
