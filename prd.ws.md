modification for workshop mode from complete setup:
# lambda /source/backend/api_lambda.py
- copy to a new lambda api_lambda_ws.py
- remove is_bot function in comment post, get
- remove is_bot function in flight price post, get
# cloudfront function /terraform/cloudfront-function.js
copy to 
- save only
    // Log request details for monitoring
    console.log('CloudFront Function - URI: ' + request.uri + ', Bot: ' + isBotDetected + ', Demo1: ' + isBotDemo1);
    console.log(event);
    return request;
- add comment where participant need to copy paste additional logic code.

# waf /terraform/main.tf
- copy to a new folder /terraform_ws
- remove waf rules : AWSManagedRulesBotControlRuleSet, TokenAbsentChallengeRule, BotDetectedHeaderRule
