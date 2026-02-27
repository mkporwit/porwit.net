output "api_url" {
  description = "API Gateway endpoint URL"
  value       = aws_api_gateway_stage.jobtracker.invoke_url
}

output "frontend_url" {
  description = "Frontend S3 website URL"
  value       = "http://${aws_s3_bucket_website_configuration.frontend.website_endpoint}"
}

output "frontend_bucket_name" {
  description = "Frontend S3 bucket name"
  value       = aws_s3_bucket.frontend.id
}

output "cloudfront_domain" {
  description = "CloudFront distribution domain name"
  value       = aws_cloudfront_distribution.jobtracker.domain_name
}

output "cloudfront_distribution_id" {
  description = "CloudFront distribution ID"
  value       = aws_cloudfront_distribution.jobtracker.id
}

output "dynamodb_table_name" {
  description = "DynamoDB table name"
  value       = aws_dynamodb_table.jobtracker.name
}
