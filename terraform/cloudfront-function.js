import cf from 'cloudfront';

async function handler(event) {
    var request = event.request;
    var headers = request.headers;
    
    // Check if bot is detected by WAF
    var isBotDetected = headers['x-amzn-waf-targeted-bot-detected'] && 
                       headers['x-amzn-waf-targeted-bot-detected'].value === 'true';
    
    // Check if this is a request for bot-demo-1
    var isBotDemo1 = request.uri === '/bot-demo-1' || request.uri.startsWith('/bot-demo-1/');
    
    // If bot is detected and accessing bot-demo-1, redirect with 70% probability
    if (isBotDetected && isBotDemo1) {
        // Generate random number between 0 and 1
        var random = Math.random();
        
        // 70% probability of redirect to timeout origin
        if (random < 0.7) {
            // Update request to use timeout ALB (will cause timeout due to security group)
            cf.updateRequestOrigin({
                "domainName": "${timeout_alb_dns_name}",  // Will be replaced by Terraform
                "originAccessControlConfig": {
                    "enabled": false
                },
                "timeouts": {
                    "readTimeout": 30,      // Standard timeout
                    "connectionTimeout": 10  // Standard timeout
                },
                "connectionAttempts": 3
            });
            
            console.log('Bot detected on bot-demo-1: routed to timeout ALB');
            
            // Add custom headers for debugging
            request.headers['x-bot-redirect'] = { value: 'timeout-alb' };
            request.headers['x-redirect-probability'] = { value: random.toString() };
        } else {
            console.log('Bot detected on bot-demo-1: allowed through (30% probability)');
            request.headers['x-bot-redirect'] = { value: 'allowed-through' };
        }
    }
    
    // For private paths, bots accessing these get routed to fake S3 content
    if (request.uri.startsWith('/private/')) {
        console.log('Private path accessed: ' + request.uri);
        // This will be handled by CloudFront behavior routing to S3 fake pages
        // No modification needed here, just pass through
        request.headers['x-private-access'] = { value: 'true' };
    }
    
    // Add custom headers for debugging and tracking
    request.headers['x-bot-detected'] = { value: isBotDetected ? 'true' : 'false' };
    request.headers['x-demo-path'] = { value: isBotDemo1 ? 'bot-demo-1' : 'other' };
    request.headers['x-original-uri'] = { value: request.uri };
    
    // Log request details for monitoring
    console.log('CloudFront Function - URI: ' + request.uri + ', Bot: ' + isBotDetected + ', Demo1: ' + isBotDemo1);
    console.log(event);
    return request;
}
