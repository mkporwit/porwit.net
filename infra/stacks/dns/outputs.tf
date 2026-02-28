output "zone_id" {
  description = "Route 53 zone ID"
  value       = aws_route53_zone.porwit_net.zone_id
}

output "name_servers" {
  description = "Route 53 name servers (set these at your registrar)"
  value       = aws_route53_zone.porwit_net.name_servers
}
