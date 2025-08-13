import json
import os
import time
import random
import string
import urllib.parse
from datetime import datetime, timezone
from decimal import Decimal
import boto3
from botocore.exceptions import ClientError

# DynamoDB configuration
TABLE_NAME = os.environ.get('DYNAMODB_TABLE_NAME', 'bot-deception-dev-comments')
AWS_REGION = os.environ.get('AWS_REGION', 'us-east-1')

class DecimalEncoder(json.JSONEncoder):
    """Custom JSON encoder to handle Decimal types from DynamoDB"""
    def default(self, obj):
        if isinstance(obj, Decimal):
            return int(obj) if obj % 1 == 0 else float(obj)
        return super(DecimalEncoder, self).default(obj)

class SimpleDynamoDB:
    """Simple DynamoDB client using boto3 (available in Lambda runtime)"""
    
    def __init__(self, table_name):
        self.table_name = table_name
        self.region = AWS_REGION
        self.dynamodb = boto3.resource('dynamodb', region_name=self.region)
        self.table = self.dynamodb.Table(table_name)
    
    def put_item(self, item):
        """Add an item to DynamoDB table"""
        try:
            self.table.put_item(Item=item)
            return True
        except ClientError as error:
            print(f'DynamoDB put error: {error}')
            return False
    
    def get_items(self, limit=50):
        """Get items from DynamoDB table"""
        try:
            # Try to query using the timestamp index first
            try:
                response = self.table.query(
                    IndexName='timestamp-index',
                    ScanIndexForward=False,  # Sort by timestamp descending
                    Limit=limit
                )
                return response.get('Items', [])
            except ClientError:
                print('DynamoDB query error, falling back to scan')
                # Fallback to scan if query fails
                response = self.table.scan(Limit=limit)
                items = response.get('Items', [])
                # Sort by timestamp descending
                return sorted(items, key=lambda x: x.get('timestamp', 0), reverse=True)
        except ClientError as error:
            print(f'DynamoDB scan error: {error}')
            return []
    
    def delete_item(self, item_id):
        """Delete an item from DynamoDB table"""
        try:
            self.table.delete_item(Key={'id': item_id})
            return True
        except ClientError as error:
            print(f'DynamoDB delete error: {error}')
            return False

# Initialize DynamoDB client
db = SimpleDynamoDB(TABLE_NAME)

def send_response(status_code, body, headers=None):
    """Create a Lambda response object"""
    default_headers = {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
        'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS'
    }
    
    if headers:
        default_headers.update(headers)
    
    return {
        'statusCode': status_code,
        'headers': default_headers,
        'body': json.dumps(body, cls=DecimalEncoder)
    }

def parse_body(body, content_type):
    """Parse request body based on content type"""
    if not body:
        return {}
    
    try:
        if content_type and 'application/json' in content_type:
            return json.loads(body)
        elif content_type and 'application/x-www-form-urlencoded' in content_type:
            return dict(urllib.parse.parse_qsl(body))
        else:
            # Try JSON first, then form data
            try:
                return json.loads(body)
            except json.JSONDecodeError:
                return dict(urllib.parse.parse_qsl(body))
    except Exception as error:
        print(f'Error parsing body: {error}')
        return {}

def generate_fake_comment():
    """Generate a fake comment for bot deception"""
    fake_comments = [
        "Great article! Very informative.",
        "Thanks for sharing this valuable information.",
        "I found this really helpful for my project.",
        "Excellent explanation of the concepts.",
        "This solved my problem perfectly!",
        "Well written and easy to understand.",
        "Looking forward to more content like this.",
        "This is exactly what I was looking for."
    ]
    
    fake_names = [
        "Alex Johnson", "Sarah Chen", "Mike Rodriguez", "Emma Thompson",
        "David Kim", "Lisa Wang", "John Smith", "Maria Garcia"
    ]
    
    # Generate random ID
    random_suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=9))
    fake_id = f"fake_{int(time.time() * 1000)}_{random_suffix}"
    
    # Random timestamp within last 24 hours
    random_time = int(time.time() * 1000) - random.randint(0, 86400000)
    
    return {
        'id': fake_id,
        'name': random.choice(fake_names),  # Frontend expects 'name'
        'comment': random.choice(fake_comments),  # Frontend expects 'comment'
        'rating': random.randint(4, 5),  # Frontend expects 'rating'
        'created_at': random_time,
        'silent_discard': True
    }

def is_bot_request(headers):
    """Detect if request is from a bot based on WAF headers and User-Agent"""
    
    # Primary detection: Check WAF bot control headers
    # WAF adds 'targeted-bot-detected: true' which CloudFront forwards as 'x-amzn-waf-targeted-bot-detected'
    waf_bot_detected = (
        headers.get('x-amzn-waf-targeted-bot-detected', '').lower() == 'true' or
        headers.get('targeted-bot-detected', '').lower() == 'true'
    )
    
    if waf_bot_detected:
        print(f"🤖 WAF Bot Detection: Bot detected via WAF headers")
        return True
    
    # Secondary detection: Check User-Agent patterns for basic bots
    user_agent = headers.get('user-agent', '').lower()
    bot_patterns = [
        'bot', 'crawler', 'spider', 'scraper', 'curl', 'wget', 'python', 'java',
        'googlebot', 'bingbot', 'slurp', 'duckduckbot', 'baiduspider', 'yandexbot',
        'facebookexternalhit', 'twitterbot', 'linkedinbot', 'whatsapp', 'telegram'
    ]
    
    user_agent_bot = any(pattern in user_agent for pattern in bot_patterns)
    if user_agent_bot:
        print(f"🤖 User-Agent Bot Detection: Bot detected via User-Agent: {user_agent}")
        return True
    
    # Additional behavioral detection for sophisticated bots
    # Check for rapid submission patterns or suspicious headers
    suspicious_headers = [
        'x-forwarded-for',  # Multiple proxy chains
        'x-real-ip',        # Proxy indicators
        'x-bot-detected'    # Custom bot markers
    ]
    
    # Log for debugging but don't block based on these alone
    if any(header in headers for header in suspicious_headers):
        print(f"🔍 Suspicious headers detected: {[h for h in suspicious_headers if h in headers]}")
    
    print(f"✅ Legitimate User: No bot indicators found. User-Agent: {user_agent}")
    return False



def generate_random_id():
    """Generate a random ID for comments"""
    random_suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=9))
    return f"{int(time.time() * 1000)}_{random_suffix}"

# Route handlers
def handle_health(event):
    """Health check endpoint"""
    return send_response(200, {
        'status': 'healthy',
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'environment': 'lambda',
        'region': AWS_REGION,
        'functionName': os.environ.get('AWS_LAMBDA_FUNCTION_NAME'),
        'functionVersion': os.environ.get('AWS_LAMBDA_FUNCTION_VERSION'),
        'memory': os.environ.get('AWS_LAMBDA_FUNCTION_MEMORY_SIZE'),
        'database': {
            'type': 'DynamoDB',
            'tableName': TABLE_NAME,
            'region': AWS_REGION
        }
    })

def handle_status(event):
    """Bot detection status endpoint"""
    headers = event.get('headers', {})
    is_bot = is_bot_request(headers)
    
    # Enhanced debugging information
    waf_header = headers.get('x-amzn-waf-targeted-bot-detected', 'Not present')
    user_agent = headers.get('user-agent', 'Unknown')
    
    message = 'Suspicious bot traffic detected' if is_bot else 'Hello'
    
    return send_response(200, {
        'message': message,
        'isBot': is_bot,
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'userAgent': user_agent,
        'ip': event.get('requestContext', {}).get('identity', {}).get('sourceIp', 'Unknown'),
        'wafBotHeader': waf_header,
        'detectionMethod': 'WAF Header' if waf_header.lower() == 'true' else 'User-Agent' if is_bot else 'None',
        'allHeaders': {k: v for k, v in headers.items() if k.lower().startswith(('x-amzn-waf', 'targeted-bot', 'x-bot'))}
    })

def handle_get_comments(event):
    """Get comments endpoint with bot deception"""
    headers = event.get('headers', {})
    is_bot = is_bot_request(headers)
    
    # Log the request for debugging
    user_agent = headers.get('user-agent', 'Unknown')
    source_ip = event.get('requestContext', {}).get('identity', {}).get('sourceIp', 'Unknown')
    waf_header = headers.get('x-amzn-waf-targeted-bot-detected', 'Not present')
    
    print(f"📖 Get Comments Request:")
    print(f"   IP: {source_ip}")
    print(f"   User-Agent: {user_agent}")
    print(f"   WAF Bot Header: {waf_header}")
    print(f"   Bot Detected: {is_bot}")
    
    try:
        if is_bot:
            # Return fake comments for bots
            print(f"🎭 BOT DECEPTION: Serving fake comments to bot")
            fake_comments = [generate_fake_comment() for _ in range(5)]
            return send_response(200, {
                'comments': fake_comments,
                'total': len(fake_comments),
                'message': 'Comments retrieved successfully (bot detected - showing fake data)'
            })
        else:
            # Return real comments for legitimate users
            print(f"✅ LEGITIMATE USER: Serving real comments")
            raw_comments = db.get_items(50)
            
            # Transform field names to match frontend expectations
            transformed_comments = []
            for comment in raw_comments:
                transformed_comment = {
                    'id': comment.get('id'),
                    'name': comment.get('name', comment.get('commenter', 'Anonymous')),  # Frontend expects 'name'
                    'comment': comment.get('comment', comment.get('details', '')),  # Frontend expects 'comment'
                    'rating': comment.get('rating', 5),  # Frontend expects 'rating'
                    'created_at': comment.get('timestamp', comment.get('created_at', int(time.time() * 1000))),
                    'silent_discard': comment.get('isFake', comment.get('silent_discard', False)),
                    'ip': comment.get('ip', 'Unknown'),
                    'userAgent': comment.get('userAgent', 'Unknown')
                }
                transformed_comments.append(transformed_comment)
            
            return send_response(200, {
                'comments': transformed_comments,
                'total': len(transformed_comments),
                'message': 'Comments retrieved successfully'
            })
    except Exception as error:
        print(f'Error getting comments: {error}')
        return send_response(500, {
            'error': 'Failed to retrieve comments',
            'message': str(error)
        })

def handle_post_comments(event):
    """Add new comment endpoint"""
    headers = event.get('headers', {})
    is_bot = is_bot_request(headers)
    
    # Log the request for debugging
    user_agent = headers.get('user-agent', 'Unknown')
    source_ip = event.get('requestContext', {}).get('identity', {}).get('sourceIp', 'Unknown')
    waf_header = headers.get('x-amzn-waf-targeted-bot-detected', 'Not present')
    
    print(f"📝 Comment Submission Request:")
    print(f"   IP: {source_ip}")
    print(f"   User-Agent: {user_agent}")
    print(f"   WAF Bot Header: {waf_header}")
    print(f"   Bot Detected: {is_bot}")
    
    if is_bot:
        # SHADOW BAN: Pretend to accept the comment but don't actually store it
        print(f"🚫 SHADOW BAN: Bot comment rejected silently")
        return send_response(200, {
            'message': 'Comment added successfully (bot detected - not actually stored)',
            'comment': {
                'id': f"fake_{int(time.time() * 1000)}",
                'created_at': int(time.time() * 1000),  # Use created_at for consistency
                'silent_discard': True  # Use silent_discard for consistency
            }
        })
    
    try:
        body = parse_body(event.get('body'), event.get('headers', {}).get('content-type'))
        
        # Support both field name formats for compatibility
        name = body.get('name') or body.get('commenter')
        comment = body.get('comment') or body.get('details')
        rating = body.get('rating', 5)  # Default to 5 stars if not provided
        
        if not name or not comment:
            return send_response(400, {
                'error': 'Missing required fields',
                'required': ['name/commenter', 'comment/details'],
                'received': list(body.keys()) if body else []
            })
        
        # Store with both field name formats for maximum compatibility
        new_comment = {
            'id': generate_random_id(),
            # Store both field name formats
            'name': str(name)[:100],  # Frontend expected format
            'commenter': str(name)[:100],  # Legacy format
            'comment': str(comment)[:1000],  # Frontend expected format
            'details': str(comment)[:1000],  # Legacy format
            'rating': int(rating) if isinstance(rating, (int, float, str)) and str(rating).isdigit() else 5,  # Store rating
            'timestamp': int(time.time() * 1000),  # Legacy format
            'created_at': int(time.time() * 1000),  # Frontend expected format
            'isFake': False,  # Legacy format
            'silent_discard': False,  # Frontend expected format
            'ip': event.get('requestContext', {}).get('identity', {}).get('sourceIp', 'Unknown'),
            'userAgent': event.get('headers', {}).get('user-agent', 'Unknown')
        }
        
        success = db.put_item(new_comment)
        
        if success:
            # Return response with frontend-expected field names
            response_comment = {
                'id': new_comment['id'],
                'name': new_comment['name'],  # Frontend expects 'name'
                'comment': new_comment['comment'],  # Frontend expects 'comment'
                'rating': new_comment['rating'],  # Frontend expects 'rating'
                'created_at': new_comment['created_at'],
                'silent_discard': new_comment['silent_discard']
            }
            
            return send_response(201, {
                'message': 'Comment added successfully',
                'comment': response_comment,
                'success': True  # Add success field for frontend compatibility
            })
        else:
            return send_response(500, {
                'error': 'Failed to save comment',
                'success': False
            })
    except Exception as error:
        print(f'Error adding comment: {error}')
        return send_response(500, {
            'error': 'Failed to add comment',
            'message': str(error),
            'success': False
        })

def handle_delete_comments(event):
    """Delete comment endpoint (admin function)"""
    is_bot = is_bot_request(event.get('headers', {}))
    
    if is_bot:
        return send_response(200, {
            'message': 'Comment deleted successfully (bot detected - fake response)'
        })
    
    try:
        body = parse_body(event.get('body'), event.get('headers', {}).get('content-type'))
        
        if not body.get('id'):
            return send_response(400, {
                'error': 'Missing comment ID'
            })
        
        success = db.delete_item(body['id'])
        
        if success:
            return send_response(200, {
                'message': 'Comment deleted successfully'
            })
        else:
            return send_response(500, {
                'error': 'Failed to delete comment'
            })
    except Exception as error:
        print(f'Error deleting comment: {error}')
        return send_response(500, {
            'error': 'Failed to delete comment',
            'message': str(error)
        })

def handle_get_flights(event):
    """Get flight data with bot-specific pricing"""
    is_bot = is_bot_request(event.get('headers', {}))
    
    try:
        # Base flight data (matches original SSR logic)
        base_flights = [
            {
                'id': 1,
                'route': 'New York → London',
                'airline': 'SkyWings',
                'departure': '10:30 AM',
                'arrival': '10:30 PM',
                'duration': '7h 0m',
                'originalPrice': 1299,
                'baseDiscount': 31
            },
            {
                'id': 2,
                'route': 'Los Angeles → Tokyo',
                'airline': 'PacificAir',
                'departure': '2:15 PM',
                'arrival': '5:30 PM (next day)',
                'duration': '11h 15m',
                'originalPrice': 1899,
                'baseDiscount': 32
            },
            {
                'id': 3,
                'route': 'Chicago → Paris',
                'airline': 'EuroConnect',
                'departure': '8:45 PM',
                'arrival': '11:20 AM (next day)',
                'duration': '8h 35m',
                'originalPrice': 1499,
                'baseDiscount': 27
            },
            {
                'id': 4,
                'route': 'Miami → Barcelona',
                'airline': 'Mediterranean Air',
                'departure': '11:20 AM',
                'arrival': '5:45 AM (next day)',
                'duration': '9h 25m',
                'originalPrice': 1699,
                'baseDiscount': 29
            },
            {
                'id': 5,
                'route': 'Seattle → Sydney',
                'airline': 'Pacific Rim',
                'departure': '10:00 PM',
                'arrival': '6:30 AM (2 days later)',
                'duration': '16h 30m',
                'originalPrice': 2499,
                'baseDiscount': 24
            },
            {
                'id': 6,
                'route': 'Boston → Rome',
                'airline': 'Italian Wings',
                'departure': '6:30 PM',
                'arrival': '9:15 AM (next day)',
                'duration': '8h 45m',
                'originalPrice': 1599,
                'baseDiscount': 25
            }
        ]
        
        # Apply bot-specific pricing logic
        flights = []
        for flight in base_flights:
            if is_bot:
                # Bots see inflated prices (original price)
                processed_flight = {
                    **flight,
                    'price': flight['originalPrice'],
                    'discount': 0,
                    'available': True,
                    'botPrice': flight['originalPrice'],
                    'userPrice': None
                }
            else:
                # Normal users see discounted prices
                discounted_price = int(flight['originalPrice'] * (100 - flight['baseDiscount']) / 100)
                processed_flight = {
                    **flight,
                    'price': discounted_price,
                    'discount': flight['baseDiscount'],
                    'available': True,
                    'botPrice': None,
                    'userPrice': discounted_price
                }
            
            flights.append(processed_flight)
        
        return send_response(200, {
            'flights': flights,
            'total': len(flights),
            'message': f'Flight data retrieved successfully ({"bot detected - showing inflated prices" if is_bot else "showing discounted prices"})',
            'isBot': is_bot,
            'pricingStrategy': 'inflated' if is_bot else 'discounted'
        })
        
    except Exception as error:
        print(f'Error getting flights: {error}')
        return send_response(500, {
            'error': 'Failed to retrieve flight data',
            'message': str(error)
        })

def handle_robots_txt(event):
    """Robots.txt endpoint with bot deception"""
    is_bot = is_bot_request(event.get('headers', {}))
    
    if is_bot:
        # Provide fake robots.txt for bots
        fake_robots = f"""User-agent: *
Allow: /
Allow: /api/
Allow: /comments
Crawl-delay: 1

Sitemap: https://{event.get('headers', {}).get('host', 'example.com')}/sitemap.xml"""
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'text/plain',
                'Access-Control-Allow-Origin': '*'
            },
            'body': fake_robots
        }
    else:
        # Provide real robots.txt for legitimate users
        real_robots = """User-agent: *
Disallow: /api/
Disallow: /admin/
Allow: /

Crawl-delay: 10"""
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'text/plain',
                'Access-Control-Allow-Origin': '*'
            },
            'body': real_robots
        }

def handle_options(event):
    """Handle OPTIONS requests for CORS"""
    return send_response(200, {}, {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
        'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS'
    })

# Route mapping
ROUTES = {
    'GET /health': handle_health,
    'GET /api/status': handle_status,
    'GET /api/comments': handle_get_comments,
    'POST /api/comments': handle_post_comments,
    'DELETE /api/comments': handle_delete_comments,
    # Demo-specific routes
    'GET /api/bot-demo-2/comments': handle_get_comments,
    'POST /api/bot-demo-2/comments': handle_post_comments,
    'DELETE /api/bot-demo-2/comments': handle_delete_comments,
    'GET /api/bot-demo-3/comments': handle_get_comments,
    'POST /api/bot-demo-3/comments': handle_post_comments,
    'DELETE /api/bot-demo-3/comments': handle_delete_comments,
    # Flight data routes
    'GET /api/bot-demo-3/flights': handle_get_flights,
    'GET /robots.txt': handle_robots_txt,
    'OPTIONS': handle_options
}

def lambda_handler(event, context):
    """Main Lambda handler function"""
    print(f'Event: {json.dumps(event, default=str)}')
    
    try:
        # Handle ALB events
        if event.get('requestContext', {}).get('elb'):
            method = event.get('httpMethod')
            path = event.get('path')
            route_key = f"{method} {path}"
            
            print(f'Processing ALB request: {route_key}')
            
            # Find matching route
            handler = ROUTES.get(route_key) or ROUTES.get(method) or ROUTES.get('OPTIONS')
            
            if handler:
                result = handler(event)
                print(f'Response: {json.dumps(result, default=str)}')
                return result
            else:
                print(f'No handler found for route: {route_key}')
                return send_response(404, {
                    'error': 'Not Found',
                    'path': path,
                    'method': method,
                    'availableRoutes': list(ROUTES.keys())
                })
        
        # Handle API Gateway events (if needed)
        if event.get('requestContext', {}).get('apiId'):
            method = event.get('httpMethod')
            path = event.get('path')
            route_key = f"{method} {path}"
            
            print(f'Processing API Gateway request: {route_key}')
            
            handler = ROUTES.get(route_key) or ROUTES.get(method) or ROUTES.get('OPTIONS')
            
            if handler:
                return handler(event)
            else:
                return send_response(404, {
                    'error': 'Not Found',
                    'path': path,
                    'method': method
                })
        
        # Handle direct Lambda invocation
        print('Direct Lambda invocation')
        return send_response(200, {
            'message': 'Bot Deception API is running',
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'environment': 'lambda'
        })
        
    except Exception as error:
        print(f'Lambda Error: {error}')
        return send_response(500, {
            'error': 'Internal Server Error',
            'message': str(error),
            'timestamp': datetime.now(timezone.utc).isoformat()
        })

# For backwards compatibility, also export as 'handler'
handler = lambda_handler
