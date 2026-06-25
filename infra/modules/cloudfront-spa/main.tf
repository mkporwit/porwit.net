data "aws_region" "current" {}

# CloudFront Function to rewrite SPA routes to /index.html.
# Scoped to the S3 default behavior only, so API errors pass through unchanged.
resource "aws_cloudfront_function" "spa_rewrite" {
  name    = "${replace(var.domain_name, ".", "-")}-spa-rewrite"
  runtime = "cloudfront-js-2.0"
  publish = true
  code    = <<-JS
    function handler(event) {
      var request = event.request;
      var uri = request.uri;
      // If the URI has a file extension, serve from S3 as-is
      if (uri.includes('.')) {
        return request;
      }
      // Otherwise rewrite to index.html for SPA client-side routing
      request.uri = '/index.html';
      return request;
    }
  JS
}

resource "aws_cloudfront_distribution" "this" {
  enabled             = true
  comment             = "${var.domain_name} distribution"
  aliases             = [var.domain_name]
  default_root_object = "index.html"
  price_class         = var.price_class

  viewer_certificate {
    acm_certificate_arn      = var.certificate_arn
    ssl_support_method       = "sni-only"
    minimum_protocol_version = "TLSv1.2_2021"
  }

  # S3 origin for static frontend (custom origin pointing at website endpoint)
  origin {
    domain_name = var.s3_website_endpoint
    origin_id   = "S3Origin"

    custom_origin_config {
      http_port              = 80
      https_port             = 443
      origin_protocol_policy = "http-only"
      origin_ssl_protocols   = ["TLSv1.2"]
    }
  }

  # API Gateway origin
  origin {
    domain_name = "${var.api_gateway_id}.execute-api.${var.aws_region != "" ? var.aws_region : data.aws_region.current.name}.amazonaws.com"
    origin_id   = "ApiOrigin"
    origin_path = "/${var.api_stage_name}"

    custom_origin_config {
      http_port              = 80
      https_port             = 443
      origin_protocol_policy = "https-only"
      origin_ssl_protocols   = ["TLSv1.2"]
    }
  }

  # Default behavior -> S3 (static files)
  default_cache_behavior {
    target_origin_id       = "S3Origin"
    viewer_protocol_policy = "redirect-to-https"
    compress               = true

    allowed_methods = ["GET", "HEAD", "OPTIONS"]
    cached_methods  = ["GET", "HEAD"]

    forwarded_values {
      query_string = false
      cookies {
        forward = "none"
      }
    }

    function_association {
      event_type   = "viewer-request"
      function_arn = aws_cloudfront_function.spa_rewrite.arn
    }
  }

  # /api/* -> API Gateway (no caching)
  ordered_cache_behavior {
    path_pattern           = var.api_path_pattern
    target_origin_id       = "ApiOrigin"
    viewer_protocol_policy = "redirect-to-https"

    allowed_methods = ["GET", "HEAD", "OPTIONS", "PUT", "POST", "PATCH", "DELETE"]
    cached_methods  = ["GET", "HEAD"]

    forwarded_values {
      query_string = true
      headers      = var.api_forwarded_headers
      cookies {
        forward = "none"
      }
    }

    min_ttl     = 0
    default_ttl = 0
    max_ttl     = 0
  }

  # NOTE: No custom_error_response blocks here. SPA routing is handled by the
  # spa_rewrite CloudFront Function on the default (S3) behavior only,
  # so API 404/403 responses pass through to the client unchanged.

  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }
}
