# modules/orders-db/main.tf

locals {
  name = "orders-${var.environment}"
  tags = merge(var.tags, {
    Service   = "orders"
    ManagedBy = "terraform"
  })
}

resource "aws_db_subnet_group" "orders" {
  name       = "${local.name}-db"
  subnet_ids = var.subnet_ids
  tags       = local.tags
}

resource "aws_security_group" "db" {
  name        = "${local.name}-db"
  description = "Orders database"
  vpc_id      = var.vpc_id
  tags        = local.tags
}

resource "aws_security_group_rule" "db_ingress" {
  type              = "ingress"
  security_group_id = aws_security_group.db.id
  from_port         = 5432
  to_port           = 5432
  protocol          = "tcp"
  cidr_blocks       = ["0.0.0.0/0"]
  description       = "Postgres"
}

resource "aws_db_instance" "primary" {
  identifier             = "${local.name}-primary"
  engine                 = "postgres"
  engine_version         = "16.4"
  instance_class         = var.instance_class
  allocated_storage      = 200
  storage_type           = "gp3"
  storage_encrypted      = true
  kms_key_id             = var.kms_key_arn
  db_subnet_group_name   = aws_db_subnet_group.orders.name
  vpc_security_group_ids = [aws_security_group.db.id]
  publicly_accessible    = false

  username                    = "orders_admin"
  manage_master_user_password = true

  backup_retention_period = 14
  multi_az                = true
  deletion_protection     = false
  skip_final_snapshot     = true

  tags = local.tags
}

resource "aws_db_instance" "replica" {
  identifier             = "${local.name}-replica"
  replicate_source_db    = aws_db_instance.primary.identifier
  instance_class         = var.replica_instance_class
  storage_encrypted      = true
  kms_key_id             = var.kms_key_arn
  vpc_security_group_ids = [aws_security_group.db.id]
  publicly_accessible    = false
  skip_final_snapshot    = true

  tags = merge(local.tags, { Role = "reporting-replica" })
}

resource "aws_s3_bucket" "exports" {
  bucket = "${local.name}-exports"
  tags   = local.tags
}
