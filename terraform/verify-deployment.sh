#!/bin/bash

# Simple deployment verification script
# This script verifies that the deployment is working correctly

set -e

echo "🔍 Bot Deception Deployment Verification"
echo "========================================"

# Check if terraform is initialized
if [ ! -d ".terraform" ]; then
    echo "❌ Terraform not initialized. Run 'terraform init' first."
    exit 1
fi

# Check if deployment exists
if ! terraform show &>/dev/null; then
    echo "❌ No Terraform deployment found. Run 'terraform apply' first."
    exit 1
fi

echo "✅ Terraform deployment found"

# Get CloudFront domain
CLOUDFRONT_DOMAIN=$(terraform output -raw cloudfront_distribution_domain_name 2>/dev/null || echo "")

if [ -z "$CLOUDFRONT_DOMAIN" ]; then
    echo "❌ Could not get CloudFront domain from Terraform output"
    exit 1
fi

echo "✅ CloudFront domain: $CLOUDFRONT_DOMAIN"

# Test main site
echo "🌐 Testing main site..."
if curl -s -o /dev/null -w "%{http_code}" "https://$CLOUDFRONT_DOMAIN" | grep -q "200"; then
    echo "✅ Main site is accessible"
else
    echo "❌ Main site is not accessible"
fi

# Test API endpoint
echo "🔌 Testing API endpoint..."
if curl -s -o /dev/null -w "%{http_code}" "https://$CLOUDFRONT_DOMAIN/api/status" | grep -q "200"; then
    echo "✅ API endpoint is working"
else
    echo "❌ API endpoint is not working"
fi

# Test health check
echo "🏥 Testing health check..."
if curl -s -o /dev/null -w "%{http_code}" "https://$CLOUDFRONT_DOMAIN/health" | grep -q "200"; then
    echo "✅ Health check is working"
else
    echo "❌ Health check is not working"
fi

echo ""
echo "🎉 Deployment verification complete!"
echo ""
echo "📋 Deployment URLs:"
terraform output deployment_urls

echo ""
echo "🔧 Node.js Build Info:"
terraform output nodejs_info
