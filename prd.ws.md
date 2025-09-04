modification for workshop mode from complete setup:
#lambda /source/backend/api_lambda.py
- remove is_bot function in comment post, get
- remove is_bot function in flight price post, get
#waf /terraform/main.tf
- remove waf rules : AWSManagedRulesBotControlRuleSet, TokenAbsentChallengeRule, BotDetectedHeaderRule
