output "endpoint" {
  description = "ElastiCache Redis endpoint (hostname only)"
  value       = aws_elasticache_cluster.redis.cache_nodes[0].address
}

output "port" {
  description = "ElastiCache Redis port"
  value       = aws_elasticache_cluster.redis.cache_nodes[0].port
}

output "cluster_id" {
  description = "ElastiCache cluster ID"
  value       = aws_elasticache_cluster.redis.id
}
