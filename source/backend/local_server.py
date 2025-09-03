#!/usr/bin/env python3
"""
Local development server for bot deception API
Mimics the Lambda function behavior for local testing
"""

import json
import time
import random
import string
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse
from datetime import datetime, timezone

# In-memory storage for local development
comments_db = []
comments_lock = threading.Lock()

def response(status_code, body, headers=None):
    """Create a response object matching Lambda format"""
    default_headers = {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type,Authorization',
        'Access-Control-Allow-Methods': 'GET,POST,DELETE,OPTIONS'
    }
    if headers:
        default_headers.update(headers)
    
    return {
        'statusCode': status_code,
        'headers': default_headers,
        'body': json.dumps(body) if isinstance(body, (dict, list)) else body
    }

def is_bot(headers):
    """Bot detection matching Lambda version"""
    user_agent = headers.get('user-agent', '').lower()
    bot_patterns = [
        'bot', 'crawler', 'spider', 'scraper', 'curl', 'wget', 'python', 'java',
        'googlebot', 'bingbot', 'slurp', 'duckduckbot', 'baiduspider', 'yandexbot'
    ]
    return any(pattern in user_agent for pattern in bot_patterns)

def generate_random_id():
    """Generate a random ID for comments"""
    random_suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=9))
    return f"{int(time.time() * 1000)}_{random_suffix}"

def generate_fake_comment():
    """Generate a fake comment for bot deception"""
    fake_comments = [
        "Great article! Very informative.",
        "Thanks for sharing this valuable information.",
        "I found this really helpful for my project.",
        "Excellent explanation of the concepts.",
        "This solved my problem perfectly!"
    ]
    fake_names = ["Alex Johnson", "Sarah Chen", "Mike Rodriguez", "Emma Thompson"]
    
    return {
        'id': generate_random_id(),
        'name': random.choice(fake_names),
        'comment': random.choice(fake_comments),
        'rating': random.randint(4, 5),
        'created_at': int(time.time() * 1000) - random.randint(0, 86400000),
        'silent_discard': True
    }

# Route decorator system matching Lambda
def route(path):
    def decorator(func):
        func.route = path
        return func
    return decorator

@route('GET /health')
def health(event):
    return response(200, {
        'status': 'healthy',
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'environment': 'local',
        'database': {'type': 'in-memory', 'count': len(comments_db)}
    })

@route('GET /api/status')
def status(event):
    headers = event.get('headers', {})
    is_bot_detected = is_bot(headers)
    
    return response(200, {
        'message': 'Suspicious bot traffic detected' if is_bot_detected else 'Hello',
        'isBot': is_bot_detected,
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'userAgent': headers.get('user-agent', 'Unknown')
    })

@route('GET /api/comments')
def get_comments(event):
    headers = event.get('headers', {})
    is_bot_detected = is_bot(headers)
    
    if is_bot_detected:
        fake_comments = [generate_fake_comment() for _ in range(5)]
        return response(200, {'comments': fake_comments, 'total': len(fake_comments)})
    else:
        with comments_lock:
            real_comments = [c for c in comments_db if not c.get('silent_discard', False)]
            return response(200, {'comments': real_comments, 'total': len(real_comments)})

@route('POST /api/comments')
def post_comment(event):
    headers = event.get('headers', {})
    is_bot_detected = is_bot(headers)
    
    if is_bot_detected:
        return response(200, {
            'message': 'Comment added successfully',
            'comment': {'id': generate_random_id(), 'silent_discard': True}
        })
    
    try:
        body = json.loads(event.get('body', '{}'))
        name = body.get('name')
        comment = body.get('comment')
        rating = body.get('rating', 5)
        
        if not name or not comment:
            return response(400, {'error': 'Missing required fields'})
        
        new_comment = {
            'id': generate_random_id(),
            'name': str(name)[:100],
            'comment': str(comment)[:1000],
            'rating': int(rating) if isinstance(rating, (int, float, str)) and str(rating).isdigit() else 5,
            'created_at': int(time.time() * 1000),
            'silent_discard': False
        }
        
        with comments_lock:
            comments_db.append(new_comment)
        
        return response(201, {'message': 'Comment added successfully', 'comment': new_comment})
    except Exception as error:
        return response(500, {'error': str(error)})

@route('DELETE /api/comments')
def delete_comment(event):
    headers = event.get('headers', {})
    is_bot_detected = is_bot(headers)
    
    if is_bot_detected:
        return response(200, {'message': 'Comment deleted successfully'})
    
    try:
        body = json.loads(event.get('body', '{}'))
        comment_id = body.get('id')
        
        if not comment_id:
            return response(400, {'error': 'Missing comment ID'})
        
        with comments_lock:
            original_length = len(comments_db)
            comments_db[:] = [c for c in comments_db if c['id'] != comment_id]
            success = len(comments_db) < original_length
        
        return response(200 if success else 404, {
            'message': 'Comment deleted' if success else 'Comment not found'
        })
    except Exception as error:
        return response(500, {'error': str(error)})

@route('GET /api/bot-demo-3/flights')
def get_flights(event):
    headers = event.get('headers', {})
    is_bot_detected = is_bot(headers)
    
    base_flights = [
        {'id': 1, 'route': 'New York → London', 'airline': 'SkyWings', 'departure': '10:30 AM', 'arrival': '10:30 PM', 'duration': '7h 0m', 'originalPrice': 1299, 'baseDiscount': 31},
        {'id': 2, 'route': 'Los Angeles → Tokyo', 'airline': 'PacificAir', 'departure': '2:15 PM', 'arrival': '5:30 PM (next day)', 'duration': '11h 15m', 'originalPrice': 1899, 'baseDiscount': 32},
        {'id': 3, 'route': 'Chicago → Paris', 'airline': 'EuroConnect', 'departure': '8:45 PM', 'arrival': '11:20 AM (next day)', 'duration': '8h 35m', 'originalPrice': 1499, 'baseDiscount': 27},
        {'id': 4, 'route': 'Miami → Barcelona', 'airline': 'Mediterranean Air', 'departure': '11:20 AM', 'arrival': '5:45 AM (next day)', 'duration': '9h 25m', 'originalPrice': 1699, 'baseDiscount': 29},
        {'id': 5, 'route': 'Seattle → Sydney', 'airline': 'Pacific Rim', 'departure': '10:00 PM', 'arrival': '6:30 AM (2 days later)', 'duration': '16h 30m', 'originalPrice': 2499, 'baseDiscount': 24},
        {'id': 6, 'route': 'Boston → Rome', 'airline': 'Italian Wings', 'departure': '6:30 PM', 'arrival': '9:15 AM (next day)', 'duration': '8h 45m', 'originalPrice': 1599, 'baseDiscount': 25}
    ]
    
    flights = []
    for flight in base_flights:
        if is_bot_detected:
            processed_flight = {**flight, 'price': flight['originalPrice'], 'discount': 0, 'available': True}
        else:
            discounted_price = int(flight['originalPrice'] * (100 - flight['baseDiscount']) / 100)
            processed_flight = {**flight, 'price': discounted_price, 'discount': flight['baseDiscount'], 'available': True}
        flights.append(processed_flight)
    
    return response(200, {'flights': flights, 'total': len(flights), 'isBot': is_bot_detected})

@route('GET /robots.txt')
def robots_txt(event):
    headers = event.get('headers', {})
    content = "User-agent: *\nAllow: /" if is_bot(headers) else "User-agent: *\nDisallow: /api/"
    return {'statusCode': 200, 'headers': {'Content-Type': 'text/plain'}, 'body': content}

@route('OPTIONS')
def options(event):
    return response(200, {})

# Route registry matching Lambda
routes = {}
for name, obj in list(globals().items()):
    if hasattr(obj, 'route'):
        routes[obj.route] = obj

def handle_request(method, path, headers, body=None):
    """Handle request matching Lambda handler logic"""
    route_key = f"{method} {path}"
    handler = routes.get(route_key) or routes.get(method) or routes.get('OPTIONS')
    
    if handler:
        event = {'httpMethod': method, 'path': path, 'headers': headers, 'body': body}
        return handler(event)
    else:
        return response(404, {'error': 'Not Found', 'path': path, 'method': method})

class APIHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self._handle_request('GET')
    
    def do_POST(self):
        self._handle_request('POST')
    
    def do_DELETE(self):
        self._handle_request('DELETE')
    
    def do_OPTIONS(self):
        self._handle_request('OPTIONS')
    
    def _handle_request(self, method):
        parsed_path = urlparse(self.path)
        path = parsed_path.path
        headers = dict(self.headers)
        
        body = None
        if method in ['POST', 'DELETE']:
            content_length = int(headers.get('content-length', 0))
            if content_length > 0:
                body = self.rfile.read(content_length).decode('utf-8')
        
        result = handle_request(method, path, headers, body)
        
        self.send_response(result['statusCode'])
        for key, value in result['headers'].items():
            self.send_header(key, value)
        self.end_headers()
        
        if result['body']:
            self.wfile.write(result['body'].encode() if isinstance(result['body'], str) else result['body'])
    
    def log_message(self, format, *args):
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {format % args}")

def run_server(port=8000):
    server_address = ('', port)
    httpd = HTTPServer(server_address, APIHandler)
    print(f"Starting local development server on http://localhost:{port}")
    print("Available routes:")
    for route in sorted(routes.keys()):
        print(f"  {route}")
    print("Press Ctrl+C to stop the server")
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server...")
        httpd.shutdown()

if __name__ == '__main__':
    run_server()
