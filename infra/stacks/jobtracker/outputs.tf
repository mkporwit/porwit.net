output "api_url" {
  description = "API Gateway endpoint URL"
  value       = module.api_gateway.invoke_url
}

output "frontend_url" {
  description = "Frontend S3 website URL"
  value       = "http://${module.frontend_bucket.website_endpoint}"
}

output "frontend_bucket_name" {
  description = "Frontend S3 bucket name"
  value       = module.frontend_bucket.bucket_id
}

output "cloudfront_domain" {
  description = "CloudFront distribution domain name"
  value       = module.cloudfront.distribution_domain_name
}

output "cloudfront_distribution_id" {
  description = "CloudFront distribution ID"
  value       = module.cloudfront.distribution_id
}

output "dynamodb_table_name" {
  description = "DynamoDB table name"
  value       = module.dynamodb.table_name
}
