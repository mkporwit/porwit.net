#!/bin/bash
set -e

REGION="${AWS_REGION:-us-west-2}"
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
STATE_BUCKET="jobtracker-tfstate-${ACCOUNT_ID}"
LOCK_TABLE="jobtracker-tflock"

echo "=== JobTracker OpenTofu Deployment ==="
echo "Region: $REGION"
echo "Account: $ACCOUNT_ID"
echo ""

# --- Step 1: Bootstrap state backend ---
echo "--- Bootstrapping state backend ---"

# Create S3 state bucket if it doesn't exist
if ! aws s3api head-bucket --bucket "$STATE_BUCKET" 2>/dev/null; then
    echo "Creating state bucket: $STATE_BUCKET"
    aws s3api create-bucket \
        --bucket "$STATE_BUCKET" \
        --region "$REGION" \
        --create-bucket-configuration LocationConstraint="$REGION"
    aws s3api put-bucket-versioning \
        --bucket "$STATE_BUCKET" \
        --versioning-configuration Status=Enabled
    aws s3api put-bucket-encryption \
        --bucket "$STATE_BUCKET" \
        --server-side-encryption-configuration '{
            "Rules": [{"ApplyServerSideEncryptionByDefault": {"SSEAlgorithm": "AES256"}}]
        }'
    echo "State bucket created."
else
    echo "State bucket already exists."
fi

# Create DynamoDB lock table if it doesn't exist
if ! aws dynamodb describe-table --table-name "$LOCK_TABLE" --region "$REGION" >/dev/null 2>&1; then
    echo "Creating lock table: $LOCK_TABLE"
    aws dynamodb create-table \
        --table-name "$LOCK_TABLE" \
        --attribute-definitions AttributeName=LockID,AttributeType=S \
        --key-schema AttributeName=LockID,KeyType=HASH \
        --billing-mode PAY_PER_REQUEST \
        --region "$REGION"
    aws dynamodb wait table-exists --table-name "$LOCK_TABLE" --region "$REGION"
    echo "Lock table created."
else
    echo "Lock table already exists."
fi

# --- Step 2: OpenTofu init + apply ---
echo ""
echo "--- Running OpenTofu ---"

# Export AWS credentials for OpenTofu (aws configure login stores session creds
# in a way that the AWS CLI finds but OpenTofu does not)
eval "$(aws configure export-credentials --format env)"

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"

cd "$REPO_ROOT/infra/stacks/jobtracker"

tofu init
tofu apply -auto-approve

# Capture outputs
API_URL=$(tofu output -raw api_url)
FRONTEND_BUCKET=$(tofu output -raw frontend_bucket_name)
CF_DIST_ID=$(tofu output -raw cloudfront_distribution_id)
CF_DOMAIN=$(tofu output -raw cloudfront_domain)

cd "$REPO_ROOT/jobtracker"

# --- Step 3: Generate OpenAPI spec ---
echo ""
echo "--- Generating OpenAPI spec ---"

uv run scripts/generate_openapi.py

# --- Step 4: Update frontend config ---
echo ""
echo "--- Updating frontend config ---"

cat > frontend/config.js << EOF
window.APP_CONFIG = {
    API_URL: "${API_URL}",
    ENVIRONMENT: "prod"
};
EOF

echo "Frontend config updated with API URL: $API_URL"

# --- Step 5: Deploy frontend to S3 ---
echo ""
echo "--- Deploying frontend to S3 ---"

aws s3 sync frontend/ "s3://${FRONTEND_BUCKET}/" \
    --region "$REGION" \
    --delete

aws s3 cp openapi.yaml "s3://${FRONTEND_BUCKET}/.well-known/openapi.yaml" \
    --region "$REGION" \
    --content-type "application/yaml"

# --- Step 6: Invalidate CloudFront cache ---
echo ""
echo "--- Invalidating CloudFront cache ---"

aws cloudfront create-invalidation \
    --distribution-id "$CF_DIST_ID" \
    --paths "/*" \
    --output text

echo ""
echo "=== Deployment Complete ==="
echo ""
echo "API URL:           $API_URL"
echo "Frontend Bucket:   $FRONTEND_BUCKET"
echo "CloudFront Domain: $CF_DOMAIN"
echo "Custom Domain:     https://jobtracker.porwit.net"
echo ""
echo "Next steps:"
echo "  1. Seed companies: cd src && DYNAMODB_TABLE=jobtracker python seed_data.py"
echo "  2. Import applications: uv run scripts/import_excel.py 'Job_Search_Tracker.xlsx' --table jobtracker"
