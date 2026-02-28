#!/bin/bash
set -e

REGION="${AWS_REGION:-us-west-2}"

echo "=== Gunset OpenTofu Deployment ==="
echo "Region: $REGION"
echo ""

# Export AWS credentials for OpenTofu
eval "$(aws configure export-credentials --format env)"

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"

# --- Step 1: OpenTofu init + apply ---
echo "--- Running OpenTofu ---"

cd "$REPO_ROOT/infra/stacks/gunset"

tofu init
tofu apply -auto-approve

# Capture outputs
API_URL=$(tofu output -raw api_url)
FRONTEND_BUCKET=$(tofu output -raw frontend_bucket_name)
FRONTEND_URL=$(tofu output -raw frontend_url)
CF_DIST_ID=$(tofu output -raw cloudfront_distribution_id)

cd "$REPO_ROOT/gunset"

# --- Step 2: Deploy frontend to S3 ---
echo ""
echo "--- Deploying frontend to S3 ---"

aws s3 sync frontend/ "s3://${FRONTEND_BUCKET}/" \
    --region "$REGION" \
    --delete

# --- Step 3: Invalidate CloudFront cache ---
echo ""
echo "--- Invalidating CloudFront cache ---"

aws cloudfront create-invalidation \
    --distribution-id "$CF_DIST_ID" \
    --paths "/*" \
    --output text

echo ""
echo "=== Deployment Complete ==="
echo ""
echo "API URL:      $API_URL"
echo "Frontend:     $FRONTEND_URL"
echo "Custom Domain: https://gunset.porwit.net"
