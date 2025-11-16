output "endpoint" {
  description = "RDS instance endpoint (host:port)"
  value       = aws_db_instance.postgres.endpoint
}

output "address" {
  description = "RDS instance address (hostname only)"
  value       = aws_db_instance.postgres.address
}

output "port" {
  description = "RDS instance port"
  value       = aws_db_instance.postgres.port
}

output "database_name" {
  description = "Name of the database"
  value       = aws_db_instance.postgres.db_name
}

output "instance_id" {
  description = "RDS instance ID"
  value       = aws_db_instance.postgres.id
}
