#!/usr/bin/env python3
"""
Local development server for SQLite-based Lambda function
Wraps the Lambda handler to work as a local HTTP server
"""

import json
import os
import sys
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

# Import your Lambda function
from api_lambda import lambda_handler

class LocalAPIHandler(BaseHTTPRequestHandler):
    """HTTP request handler that converts requests to Lambda events"""
    
    def _send_response(self, status_code, data, headers=None):
        """Send HTTP response"""
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization, X-Requested-With')
        
        if headers:
            for key, value in headers.items():
                self.send_header(key, value)
        
        self.end_headers()
        
        if isinstance(data, dict):
            self.wfile.write(json.dumps(data, indent=2).encode())
        else:
            self.wfile.write(str(data).encode())
    
    def _create_lambda_event(self, method, path, body=None, query_params=None):
        """Convert HTTP request to Lambda event format"""
        return {
            'httpMethod': method,
            'path': path,
            'queryStringParameters': query_params or {},
            'headers': dict(self.headers),
            'body': body,
            'requestContext': {
                'requestId': 'local-dev-request',
                'stage': 'dev',
                'identity': {
                    'sourceIp': self.client_address[0]
                },
                'elb': {
                    'targetGroupArn': 'local-dev'
                }
            }
        }
    
    def _handle_request(self, method):
        """Generic request handler"""
        parsed_path = urlparse(self.path)
        path = parsed_path.path
        query_params = dict(parse_qs(parsed_path.query))
        
        # Get request body for POST/PUT requests
        body = None
        if method in ['POST', 'PUT', 'PATCH']:
            content_length = int(self.headers.get('Content-Length', 0))
            if content_length > 0:
                body = self.rfile.read(content_length).decode('utf-8')
        
        # Convert to Lambda event
        event = self._create_lambda_event(method, path, body=body, query_params=query_params)
        
        try:
            # Call your Lambda function
            print(f"🔄 {method} {path}")
            response = lambda_handler(event, {})
            
            # Extract response
            status_code = response.get('statusCode', 200)
            response_body = response.get('body', '{}')
            response_headers = response.get('headers', {})
            
            # Parse JSON body if it's a string
            if isinstance(response_body, str):
                try:
                    response_body = json.loads(response_body)
                except json.JSONDecodeError:
                    pass
            
            print(f"✅ {status_code} {path}")
            self._send_response(status_code, response_body, response_headers)
            
        except Exception as e:
            print(f"❌ Error handling {method} {path}: {e}")
            self._send_response(500, {'error': str(e), 'path': path, 'method': method})
    
    def do_OPTIONS(self):
        """Handle CORS preflight requests"""
        self._send_response(200, {})
    
    def do_GET(self):
        """Handle GET requests"""
        self._handle_request('GET')
    
    def do_POST(self):
        """Handle POST requests"""
        self._handle_request('POST')
    
    def do_PUT(self):
        """Handle PUT requests"""
        self._handle_request('PUT')
    
    def do_DELETE(self):
        """Handle DELETE requests"""
        self._handle_request('DELETE')
    
    def do_PATCH(self):
        """Handle PATCH requests"""
        self._handle_request('PATCH')
    
    def log_message(self, format, *args):
        """Override to reduce noise in logs"""
        pass

def run_local_server(port=3001, host='localhost'):
    """Run local development server"""
    
    # Set up local SQLite database path
    os.environ['SQLITE_DB_PATH'] = './local_comments.db'
    
    server_address = (host, port)
    httpd = HTTPServer(server_address, LocalAPIHandler)
    
    print("🚀 Bot Deception API - Local Development Server")
    print("=" * 50)
    print(f"📡 Server running on http://{host}:{port}")
    print(f"📁 SQLite database: {os.path.abspath('./local_comments.db')}")
    print(f"🔗 Frontend should proxy /api requests to this server")
    print("📋 Available endpoints:")
    print("   GET  /api/status")
    print("   GET  /api/bot-demo-2/comments")
    print("   POST /api/bot-demo-2/comments")
    print("   GET  /api/bot-demo-3/flights")
    print("   GET  /robots.txt")
    print("   GET  /health")
    print("⏹️  Press Ctrl+C to stop")
    print("=" * 50)
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 Server stopped")
        httpd.server_close()

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Local development server for Bot Deception API')
    parser.add_argument('--port', '-p', type=int, default=3001, help='Port to run server on (default: 3001)')
    parser.add_argument('--host', default='localhost', help='Host to bind to (default: localhost)')
    
    args = parser.parse_args()
    
    run_local_server(port=args.port, host=args.host)
