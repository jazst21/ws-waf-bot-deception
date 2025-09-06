# =============================================================================
# WORKSHOP ADDITION - STAGE 2 TERRAFORM CONFIGURATION
# =============================================================================
# This file updates existing workshop resources to add production bot detection.
# Apply this after the initial workshop deployment.

# Reference resources from the workshop deployment
locals {
  # Get references from parent terraform state
  lambda_function_name = data.terraform_remote_state.workshop.outputs.lambda_api_function_name
  cloudfront_distribution_id = data.terraform_remote_state.workshop.outputs.cloudfront_distribution_id
  timeout_alb_dns_name = data.terraform_remote_state.workshop.outputs.timeout_alb_dns_name
  fake_s3_domain_name = "${data.terraform_remote_state.workshop.outputs.fake_webpages_bucket_name}.s3.amazonaws.com"
}

# Update Lambda API source to production version with bot detection
resource "null_resource" "update_lambda_source" {
  triggers = {
    lambda_version = "production-v4"
    force_update = "2025-09-06-15-14"
  }

  provisioner "local-exec" {
    command = <<-EOT
      cd /workspaces/ws-waf-bot-deception/terraform_ws/stage2
      rm -f lambda-api.zip
      zip lambda-api.zip -j /workspaces/ws-waf-bot-deception/source/backend/api_lambda.py
      
      aws lambda update-function-code \
        --function-name bot-deception-dev-api \
        --zip-file fileb://lambda-api.zip
      
      echo "✅ Updated Lambda function to production version with bot detection"
    EOT
  }

  provisioner "local-exec" {
    when = destroy
    command = <<-EOT
      cd /workspaces/ws-waf-bot-deception/terraform_ws/stage2
      rm -f lambda-api-ws.zip
      zip lambda-api-ws.zip -j /workspaces/ws-waf-bot-deception/source/backend/api_lambda_ws.py
      
      aws lambda update-function-code \
        --function-name bot-deception-dev-api \
        --zip-file fileb://lambda-api-ws.zip
      
      echo "✅ Rolled back Lambda function to workshop version"
    EOT
  }
}

# Update existing WAF with bot control rules
resource "null_resource" "update_waf_with_bot_control" {
  triggers = {
    update_version = "v4"
    force_update = "2025-09-06-15-14"
  }

  provisioner "local-exec" {
    command = <<-EOT
      WAF_ID=$(aws wafv2 list-web-acls --scope CLOUDFRONT --query 'WebACLs[?Name==`bot-deception-dev-web-acl`].Id' --output text)
      
      if [ -z "$WAF_ID" ]; then
        echo "❌ Could not find existing WAF WebACL"
        exit 1
      fi
      
      echo "📋 Found existing WAF WebACL: $WAF_ID"
      
      # Get current WAF configuration
      aws wafv2 get-web-acl --scope CLOUDFRONT --id $WAF_ID --name bot-deception-dev-web-acl > /tmp/current-waf.json
      LOCK_TOKEN=$(jq -r '.LockToken' /tmp/current-waf.json)
      
      # Extract existing rules and add new bot control rules
      jq '.WebACL | {
        Name: .Name,
        Scope: .Scope,
        DefaultAction: .DefaultAction,
        Rules: (.Rules + [
          {
            "Name": "AWSManagedRulesBotControlRuleSet",
            "Priority": 5,
            "OverrideAction": {"Count": {}},
            "Statement": {
              "ManagedRuleGroupStatement": {
                "VendorName": "AWS",
                "Name": "AWSManagedRulesBotControlRuleSet",
                "ManagedRuleGroupConfigs": [{"AWSManagedRulesBotControlRuleSet": {"InspectionLevel": "TARGETED"}}],
                "ScopeDownStatement": {
                  "AndStatement": {
                    "Statements": [
                      {"NotStatement": {"Statement": {"ByteMatchStatement": {"SearchString": ".css", "FieldToMatch": {"UriPath": {}}, "TextTransformations": [{"Priority": 0, "Type": "LOWERCASE"}], "PositionalConstraint": "ENDS_WITH"}}}},
                      {"NotStatement": {"Statement": {"ByteMatchStatement": {"SearchString": ".js", "FieldToMatch": {"UriPath": {}}, "TextTransformations": [{"Priority": 0, "Type": "LOWERCASE"}], "PositionalConstraint": "ENDS_WITH"}}}},
                      {"NotStatement": {"Statement": {"ByteMatchStatement": {"SearchString": ".jpg", "FieldToMatch": {"UriPath": {}}, "TextTransformations": [{"Priority": 0, "Type": "LOWERCASE"}], "PositionalConstraint": "ENDS_WITH"}}}},
                      {"NotStatement": {"Statement": {"ByteMatchStatement": {"SearchString": ".png", "FieldToMatch": {"UriPath": {}}, "TextTransformations": [{"Priority": 0, "Type": "LOWERCASE"}], "PositionalConstraint": "ENDS_WITH"}}}}
                    ]
                  }
                }
              }
            },
            "VisibilityConfig": {"SampledRequestsEnabled": true, "CloudWatchMetricsEnabled": true, "MetricName": "AWSManagedRulesBotControlRuleSet"}
          },
          {
            "Name": "TokenAbsentChallengeRule",
            "Priority": 6,
            "Action": {"Challenge": {}},
            "Statement": {
              "AndStatement": {
                "Statements": [
                  {"LabelMatchStatement": {"Scope": "LABEL", "Key": "awswaf:managed:token:absent"}},
                  {"NotStatement": {"Statement": {"ByteMatchStatement": {"SearchString": "/private", "FieldToMatch": {"UriPath": {}}, "TextTransformations": [{"Priority": 0, "Type": "LOWERCASE"}], "PositionalConstraint": "STARTS_WITH"}}}}
                ]
              }
            },
            "VisibilityConfig": {"SampledRequestsEnabled": true, "CloudWatchMetricsEnabled": true, "MetricName": "TokenAbsentChallengeRule"}
          },
          {
            "Name": "BotDetectedHeaderRule",
            "Priority": 7,
            "Action": {"Count": {"CustomRequestHandling": {"InsertHeaders": [{"Name": "targeted-bot-detected", "Value": "true"}]}}},
            "Statement": {"LabelMatchStatement": {"Scope": "NAMESPACE", "Key": "awswaf:managed:aws:bot-control:targeted:"}},
            "VisibilityConfig": {"SampledRequestsEnabled": true, "CloudWatchMetricsEnabled": true, "MetricName": "BotDetectedHeaderRule"}
          }
        ]),
        VisibilityConfig: .VisibilityConfig
      }' /tmp/current-waf.json > /tmp/updated-waf.json
      
      aws wafv2 update-web-acl \
        --scope CLOUDFRONT \
        --id $WAF_ID \
        --name bot-deception-dev-web-acl \
        --lock-token $LOCK_TOKEN \
        --cli-input-json file:///tmp/updated-waf.json
      
      rm -f /tmp/current-waf.json /tmp/updated-waf.json
      echo "✅ Added bot control rules to existing WAF WebACL"
    EOT
  }

  provisioner "local-exec" {
    when = destroy
    command = <<-EOT
      WAF_ID=$(aws wafv2 list-web-acls --scope CLOUDFRONT --query 'WebACLs[?Name==`bot-deception-dev-web-acl`].Id' --output text)
      
      if [ -z "$WAF_ID" ]; then
        echo "❌ Could not find existing WAF WebACL"
        exit 1
      fi
      
      # Get current WAF configuration
      aws wafv2 get-web-acl --scope CLOUDFRONT --id $WAF_ID --name bot-deception-dev-web-acl > /tmp/current-waf.json
      LOCK_TOKEN=$(jq -r '.LockToken' /tmp/current-waf.json)
      
      # Remove the bot control rules we added (keep only original rules)
      jq '.WebACL | {
        Name: .Name,
        Scope: .Scope,
        DefaultAction: .DefaultAction,
        Rules: [.Rules[] | select(.Name != "AWSManagedRulesBotControlRuleSet" and .Name != "TokenAbsentChallengeRule" and .Name != "BotDetectedHeaderRule")],
        VisibilityConfig: .VisibilityConfig
      }' /tmp/current-waf.json > /tmp/rollback-waf.json
      
      aws wafv2 update-web-acl \
        --scope CLOUDFRONT \
        --id $WAF_ID \
        --name bot-deception-dev-web-acl \
        --lock-token $LOCK_TOKEN \
        --cli-input-json file:///tmp/rollback-waf.json
      
      rm -f /tmp/current-waf.json /tmp/rollback-waf.json
      echo "✅ Removed bot control rules from WAF WebACL"
    EOT
  }
}

# Update existing CloudFront function with production code
resource "null_resource" "update_cloudfront_function" {
  triggers = {
    function_version = "production-v6"
    force_update = "2025-09-06-15-18"
  }

  provisioner "local-exec" {
    command = <<-EOT
      FUNCTION_NAME="bot-deception-dev-bot-redirect-ce3b11e8"
      
      echo "📋 Updating CloudFront function: $FUNCTION_NAME"
      
      # Use the production CloudFront function file with template substitution
      sed 's/$${timeout_alb_dns_name}/internal-bot-deception-dev-timeout-alb-930849746.us-east-1.elb.amazonaws.com/g; s/$${fake_s3_domain_name}/bot-deception-dev-fake-webpages-f9af6d63.s3.amazonaws.com/g' \
        /workspaces/ws-waf-bot-deception/source/backend/cloudfront-function.js > /tmp/cloudfront-function-production.js
      
      aws cloudfront update-function \
        --name "$FUNCTION_NAME" \
        --function-config Comment="Production bot redirect function with full logic" \
        --function-code fileb:///tmp/cloudfront-function-production.js
      
      sleep 2
      ETAG=$(aws cloudfront describe-function --name "$FUNCTION_NAME" --query 'ETag' --output text)
      echo "Got ETAG: $ETAG"
      
      aws cloudfront publish-function \
        --name "$FUNCTION_NAME" \
        --if-match "$ETAG"
      
      rm -f /tmp/cloudfront-function-production.js
      echo "✅ Updated existing CloudFront function to production version"
    EOT
  }

  provisioner "local-exec" {
    when = destroy
    command = <<-EOT
      FUNCTION_NAME=$(aws cloudfront list-functions --query 'FunctionList.Items[?contains(Name, `bot-deception-dev-bot-redirect`)].Name' --output text | head -1)
      
      if [ -z "$FUNCTION_NAME" ]; then
        echo "❌ Could not find existing CloudFront function"
        exit 1
      fi
      
      # Use the workshop CloudFront function file (hardcoded path)
      cp /workspaces/ws-waf-bot-deception/source/backend/cloudfront-function-ws.js /tmp/cloudfront-function-workshop.js
      
      aws cloudfront update-function \
        --name "$FUNCTION_NAME" \
        --function-config Comment="Workshop bot redirect function with TODO placeholders" \
        --function-code fileb:///tmp/cloudfront-function-workshop.js
      
      ETAG=$(aws cloudfront describe-function --name "$FUNCTION_NAME" --query 'ETag' --output text)
      if [ ! -z "$ETAG" ]; then
        aws cloudfront publish-function \
          --name "$FUNCTION_NAME" \
          --if-match "$ETAG"
      fi
      
      rm -f /tmp/cloudfront-function-workshop.js
      echo "✅ Rolled back CloudFront function to workshop version"
    EOT
  }
}

output "stage2_deployment_status" {
  description = "Status of Stage 2 deployment with bot detection"
  value = {
    lambda_updated              = "Existing Lambda updated to production version with bot detection"
    waf_updated                 = "Existing WAF updated with bot control rules"
    cloudfront_function_updated = "Existing CloudFront function updated to production version"
  }
}
