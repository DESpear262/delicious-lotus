resource "aws_elasticache_subnet_group" "main" {
  name       = "${var.cluster_id}-subnet-group"
  subnet_ids = var.subnet_ids

  tags = {
    Name        = "${var.cluster_id}-subnet-group"
    Environment = var.environment
  }
}

resource "aws_elasticache_cluster" "redis" {
  cluster_id           = var.cluster_id
  engine               = "redis"
  engine_version       = "7.1" # Redis 7 as per requirements
  node_type            = var.node_type
  num_cache_nodes      = var.num_cache_nodes
  parameter_group_name = "default.redis7"
  port                 = 6379

  subnet_group_name  = aws_elasticache_subnet_group.main.name
  security_group_ids = [var.security_group_id]

  # Security: Encryption in transit (TLS)
  # Note: cache.t3.micro and cache.t4g.micro do NOT support transit encryption
  # Requires cache.t3.small or larger for production
  # transit_encryption_enabled = false (not supported on t4g.micro)
  # auth_token is only valid when transit_encryption_enabled = true

  # Snapshot and backup configuration
  snapshot_retention_limit = 5
  snapshot_window          = "03:00-05:00"
  maintenance_window       = "Mon:05:00-Mon:07:00"

  # Auto minor version upgrades
  auto_minor_version_upgrade = true

  tags = {
    Name        = var.cluster_id
    Environment = var.environment
  }
}
