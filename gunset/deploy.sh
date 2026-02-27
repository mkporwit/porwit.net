#!/bin/bash
set -e

# Configuration
ENVIRONMENT="${1:-dev}"
FROM_EMAIL="${2:-noreply@example.com}"
REGION="${AWS_REGION:-us-west-2}"

echo "=== Gunset Deployment ==="
echo "Environment: $ENVIRONMENT"
echo "From Email: $FROM_EMAIL"
echo "Region: $REGION"
echo ""

# Build
echo "Building Lambda function..."
sam build

# Deploy infrastructure
echo "Deploying infrastructure..."
sam deploy \
    --stack-name "gunset-api-${ENVIRONMENT}" \
    --parameter-overrides "Environment=${ENVIRONMENT} FromEmail=${FROM_EMAIL}" \
    --capabilities CAPABILITY_IAM \
    --region "$REGION" \
    --no-confirm-changeset \
    --no-fail-on-empty-changeset

# Get outputs
echo ""
echo "Getting deployment outputs..."
API_URL=$(aws cloudformation describe-stacks \
    --stack-name "gunset-api-${ENVIRONMENT}" \
    --query "Stacks[0].Outputs[?OutputKey=='ApiUrl'].OutputValue" \
    --output text \
    --region "$REGION")

FRONTEND_BUCKET=$(aws cloudformation describe-stacks \
    --stack-name "gunset-api-${ENVIRONMENT}" \
    --query "Stacks[0].Outputs[?OutputKey=='FrontendBucketName'].OutputValue" \
    --output text \
    --region "$REGION")

FRONTEND_URL=$(aws cloudformation describe-stacks \
    --stack-name "gunset-api-${ENVIRONMENT}" \
    --query "Stacks[0].Outputs[?OutputKey=='FrontendUrl'].OutputValue" \
    --output text \
    --region "$REGION")

# Update frontend with API URL
echo "Updating frontend with API URL..."
sed -i.bak "s|https://YOUR-API-ID.execute-api.us-east-1.amazonaws.com/dev|${API_URL}|g" frontend/index.html
rm -f frontend/index.html.bak

# Deploy frontend to S3
echo "Deploying frontend to S3..."
aws s3 sync frontend/ "s3://${FRONTEND_BUCKET}/" \
    --region "$REGION" \
    --delete

echo ""
echo "=== Deployment Complete ==="
echo ""
echo "API URL: $API_URL"
echo "Frontend URL: $FRONTEND_URL"
echo ""
echo "Next steps:"
echo "1. Verify your email in SES: aws ses verify-email-identity --email-address $FROM_EMAIL"
echo "2. If in SES sandbox, verify recipient emails too"
echo "3. Visit your frontend: $FRONTEND_URL"
