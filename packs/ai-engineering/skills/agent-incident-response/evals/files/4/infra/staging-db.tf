# Staging Postgres for ledger-service
# Owner: payments-platform

resource "cloud_postgres_instance" "ledger_staging" {
  name           = "pg-staging-ledger"
  engine_version = "15"
  instance_class = "db.small"

  database_name   = "ledger"
  master_username = "ledger_admin"

  # Cost saving: keep staging backups short
  backup_retention_period = 1               # days; point-in-time restore window
  backup_window           = "03:00-03:30"   # UTC, daily automated snapshot

  deletion_protection = false
  skip_final_snapshot = true
}

resource "cloud_postgres_user" "ledger_app" {
  instance   = cloud_postgres_instance.ledger_staging.name
  username   = "ledger_app"
  # password supplied via .env.staging, rotated manually
  privileges = ["ALL"]
}
