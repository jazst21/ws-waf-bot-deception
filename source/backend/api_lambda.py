import json
import os
import time
import random
import string
import sqlite3
from datetime import datetime, timezone
from contextlib import contextmanager
from urllib.parse import parse_qsl
from functools import wraps

# Configuration
DB_PATH = os.environ.get('SQLITE_DB_PATH', '/mnt/efs/comments.db')
base_flights = [
        {'id': 1, 'route': 'New York → London', 'airline': 'SkyWings', 'departure': '10:30 AM', 'arrival': '10:30 PM', 'duration': '7h 0m', 'originalPrice': 1299, 'baseDiscount': 31},
        {'id': 2, 'route': 'Los Angeles → Tokyo', 'airline': 'PacificAir', 'departure': '2:15 PM', 'arrival': '5:30 PM (next day)', 'duration': '11h 15m', 'originalPrice': 1899, 'baseDiscount': 32},
        {'id': 3, 'route': 'Chicago → Paris', 'airline': 'EuroConnect', 'departure': '8:45 PM', 'arrival': '11:20 AM (next day)', 'duration': '8h 35m', 'originalPrice': 1499, 'baseDiscount': 27},
        {'id': 4, 'route': 'Miami → Barcelona', 'airline': 'Mediterranean Air', 'departure': '11:20 AM', 'arrival': '5:45 AM (next day)', 'duration': '9h 25m', 'originalPrice': 1699, 'baseDiscount': 29},
        {'id': 5, 'route': 'Seattle → Sydney', 'airline': 'Pacific Rim', 'departure': '10:00 PM', 'arrival': '6:30 AM (2 days later)', 'duration': '16h 30m', 'originalPrice': 2499, 'baseDiscount': 24},
        {'id': 6, 'route': 'Boston → Rome', 'airline': 'Italian Wings', 'departure': '6:30 PM', 'arrival': '9:15 AM (next day)', 'duration': '8h 45m', 'originalPrice': 1599, 'baseDiscount': 25}
    ]

class Database:
    def __init__(self, db_path=DB_PATH):
        self.db_path = db_path
        self._init_db()
    
    @contextmanager
    def conn(self):
        conn = sqlite3.connect(self.db_path, timeout=30)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
    
    def _init_db(self):
        with self.conn() as c:
            c.execute('''CREATE TABLE IF NOT EXISTS comments (
                id TEXT PRIMARY KEY, name TEXT, comment TEXT, rating INTEGER DEFAULT 5,
                timestamp INTEGER, is_fake INTEGER DEFAULT 0, ip TEXT, user_agent TEXT)''')
            c.execute('CREATE INDEX IF NOT EXISTS idx_timestamp ON comments(timestamp)')
    
    def add(self, item):
        with self.conn() as c:
            c.execute('''INSERT OR REPLACE INTO comments 
                (id, name, comment, rating, timestamp, is_fake, ip, user_agent)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)''', (
                item['id'], item['name'], item['comment'], item['rating'],
                item['timestamp'], item.get('is_fake', 0), item.get('ip', ''), item.get('user_agent', '')))
            c.commit()
    
    def get_all(self, limit=50):
        with self.conn() as c:
            rows = c.execute('SELECT id, name, comment, rating, timestamp, ip, user_agent FROM comments WHERE is_fake = 0 ORDER BY timestamp DESC LIMIT ?', (limit,)).fetchall()
            return [dict(row) for row in rows]
    
    def get_all_including_fake(self, limit=50):
        with self.conn() as c:
            rows = c.execute('SELECT id, name, comment, rating, timestamp, ip, user_agent FROM comments ORDER BY timestamp DESC LIMIT ?', (limit,)).fetchall()
            return [dict(row) for row in rows]
    
    def delete(self, item_id):
        with self.conn() as c:
            c.execute('DELETE FROM comments WHERE id = ?', (item_id,))
            c.commit()
            return c.rowcount > 0
    
    def delete_all(self):
        with self.conn() as c:
            cursor = c.execute('DELETE FROM comments')
            c.commit()
            return cursor.rowcount

db = Database()

def response(status, body, headers=None):
    return {
        'statusCode': status,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Content-Type,Authorization',
            'Access-Control-Allow-Methods': 'GET,POST,DELETE,OPTIONS',
            **(headers or {})
        },
        'body': json.dumps(body)
    }

def parse_body(body, content_type=''):
    if not body:
        return {}
    try:
        return json.loads(body) if 'json' in content_type else dict(parse_qsl(body))
    except:
        return {}

def is_bot(headers):
    # Log ALL incoming headers for debugging
    print("=== ALL INCOMING HEADERS ===")
    for key, value in headers.items():
        print(f"Header: {key} = {value}")
    print("=== END HEADERS ===")
    
    waf_detected = headers.get('x-amzn-waf-targeted-bot-detected', '').lower() == 'true'
    
    # Specific logging for WAF header detection
    print(f"Bot detection - WAF header 'x-amzn-waf-targeted-bot-detected': {headers.get('x-amzn-waf-targeted-bot-detected', 'MISSING')}")
    print(f"Bot detection - User-Agent: {headers.get('user-agent', 'MISSING')}")
    print(f"Bot detection - WAF detected result: {waf_detected}")
    
    return waf_detected

def fake_comment():
    return {
        'id': f"fake_{int(time.time() * 1000)}_{random.randint(1000, 9999)}",
        'name': random.choice(['Alex Johnson', 'Sarah Chen', 'Mike Rodriguez', 'Emma Thompson']),
        'comment': random.choice(['Great article!', 'Very helpful!', 'Thanks for sharing!']),
        'rating': random.randint(4, 5),
        'timestamp': int(time.time() * 1000) - random.randint(0, 86400000)
    }

def route(path_method):
    def decorator(func):
        func.route = path_method
        return func
    return decorator

@route('GET /health')
def health(event):
    return response(200, {
        'status': 'healthy',
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'database': {'type': 'SQLite', 'exists': os.path.exists(DB_PATH)}
    })

@route('GET /api/status')
def status(event):
    headers = event.get('headers', {})
    bot_detected = is_bot(headers)
    return response(200, {
        'message': 'Suspicious bot traffic detected' if bot_detected else 'Hello',
        'isBot': bot_detected,
        'userAgent': headers.get('user-agent', 'Unknown')
    })

@route('GET /api/comments')
def get_comments(event):
    headers = event.get('headers', {})
    
    if is_bot(headers):
        # Bots see all comments including fake ones
        comments = db.get_all_including_fake()
    else:
        # Real users only see real comments (filter out is_fake=1)
        comments = db.get_all()
    
    return response(200, {'comments': comments, 'total': len(comments)})

@route('POST /api/comments')
def post_comment(event):
    data = json.loads(event.get('body', '{}'))
    new_comment = {
        'id': f"{int(time.time() * 1000)}_{random.randint(1000, 9999)}",
        'name': data.get('name', 'Anonymous'),
        'comment': data.get('comment', ''),
        'rating': int(data.get('rating', 1)),
        'timestamp': int(time.time() * 1000),
        'is_fake': 1 if is_bot(event.get('headers', {})) else 0,
        'ip': event.get('requestContext', {}).get('identity', {}).get('sourceIp', ''),
        'user_agent': event.get('headers', {}).get('user-agent', '')
    }
    
    db.add(new_comment)
    return response(201, {'message': 'Comment added successfully', 'comment': new_comment})

@route('DELETE /api/comments')
def delete_comment(event):
    if is_bot(event.get('headers', {})):
        return response(200, {'message': 'Comment deleted successfully'})
    
    body = parse_body(event.get('body', ''), event.get('headers', {}).get('content-type', ''))
    
    # If no ID provided, delete all comments
    if not body.get('id'):
        deleted_count = db.delete_all()
        return response(200, {'message': f'All comments deleted successfully', 'deleted_count': deleted_count})
    
    # Delete specific comment by ID
    success = db.delete(body['id'])
    return response(200 if success else 404, {'message': 'Comment deleted' if success else 'Comment not found'})

@route('GET /api/bot-demo-3/flights')
def get_flights(event):    
    bot_detected = is_bot(event.get('headers', {}))
    flights = []
    for flight in base_flights:
        if bot_detected:
            processed_flight = {**flight, 'price': flight['originalPrice'], 'discount': 0, 'available': True}
        else:
            discounted_price = int(flight['originalPrice'] * (100 - flight['baseDiscount']) / 100)
            processed_flight = {**flight, 'price': discounted_price, 'discount': flight['baseDiscount'], 'available': True}
        flights.append(processed_flight)
    
    return response(200, {'flights': flights, 'total': len(flights)})

@route('GET /private')
def private_content(event):
    headers = event.get('headers', {})
    
    # Return user profile data for legitimate users
    user_profile = {
        'name': 'John Doe',
        'email': 'john.doe@example.com',
        'membershipStatus': 'Premium',
        'accountId': 'ACC-12345',
        'lastLogin': '2025-09-08T07:20:00Z',
        'permissions': ['read', 'write', 'admin']
    }
    
    return response(200, {
        'message': 'Private content accessed successfully',
        'userProfile': user_profile,
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'accessLevel': 'premium'
    })

@route('OPTIONS')
def options(event):
    return response(200, {})

# Route registry
routes = {}
for name, obj in list(globals().items()):
    if hasattr(obj, 'route'):
        routes[obj.route] = obj

def lambda_handler(event, context):
    method = event.get('httpMethod', 'GET')
    path = event.get('path', '/')
    route_key = f"{method} {path}"
    
    handler = routes.get(route_key) or routes.get(method) or routes.get('OPTIONS')
    
    if handler:
        try:
            return handler(event)
        except Exception as e:
            return response(500, {'error': str(e)})
    
    return response(404, {'error': 'Not Found', 'path': path})

handler = lambda_handler
