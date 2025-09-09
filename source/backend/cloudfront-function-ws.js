import cf from 'cloudfront';

async function handler(event) {
    var request = event.request;
    var headers = request.headers;
    
    // Check if bot is detected by WAF
    var isBotDetected = headers['x-amzn-waf-targeted-bot-detected'] && 
                       headers['x-amzn-waf-targeted-bot-detected'].value === 'true';
    
    // Check if this is a request for bot-demo-1
    var isBotDemo1 = request.uri === '/bot-demo-1' || request.uri.startsWith('/bot-demo-1/');
    
    // Check if this is a request for private path
    var isPrivatePath = request.uri === '/private' || request.uri.startsWith('/private/');
    
    // If bot is detected and accessing bot-demo-1, redirect with 50% probability
    // put code alteration here
    
    // If bot is detected and accessing private path, redirect to fake S3 pages distribution
    // put code alteration here
    
    // Add custom headers for debugging and tracking
    request.headers['x-bot-detected'] = { value: isBotDetected ? 'true' : 'false' };
    request.headers['x-demo-path'] = { value: isBotDemo1 ? 'bot-demo-1' : (isPrivatePath ? 'private' : 'other') };
    request.headers['x-original-uri'] = { value: request.uri };
    
    // Log request details for monitoring
    console.log('CloudFront Function - URI: ' + request.uri + ', Bot: ' + isBotDetected + ', Demo1: ' + isBotDemo1 + ', Private: ' + isPrivatePath);
    console.log(event);
    return request;
}
