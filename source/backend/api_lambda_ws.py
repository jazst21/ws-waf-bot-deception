import json
import boto3
import logging
from datetime import datetime
import uuid
import os

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize DynamoDB
dynamodb = boto3.resource('dynamodb')
table_name = os.environ.get('DYNAMODB_TABLE_NAME', 'bot-deception-dev-comments')
table = dynamodb.Table(table_name)

def lambda_handler(event, context):
    """
    Main Lambda handler for API requests
    """
    try:
        # Log the incoming event
        logger.info(f"Received event: {json.dumps(event)}")
        
        # Extract HTTP method and path
        http_method = event.get('httpMethod', '')
        path = event.get('path', '')
        
        # Route requests
        if path == '/api/health':
            return health_check()
        elif path == '/api/status':
            return status_check()
        elif path == '/api/comments' and http_method == 'GET':
            return get_comments()
        elif path == '/api/comments' and http_method == 'POST':
            return post_comment(event)
        elif path == '/api/flight-prices' and http_method == 'GET':
            return get_flight_prices()
        elif path == '/api/flight-prices' and http_method == 'POST':
            return post_flight_price(event)
        else:
            return {
                'statusCode': 404,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({'error': 'Not found'})
            }
            
    except Exception as e:
        logger.error(f"Error processing request: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({'error': 'Internal server error'})
        }

def health_check():
    """Health check endpoint"""
    return {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        },
        'body': json.dumps({
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat()
        })
    }

def status_check():
    """Status check endpoint"""
    return {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        },
        'body': json.dumps({
            'status': 'operational',
            'service': 'bot-deception-api',
            'timestamp': datetime.utcnow().isoformat()
        })
    }

def get_comments():
    """Get all comments"""
    try:
        response = table.scan()
        comments = response.get('Items', [])
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'comments': comments,
                'count': len(comments)
            })
        }
    except Exception as e:
        logger.error(f"Error getting comments: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({'error': 'Failed to retrieve comments'})
        }

def post_comment(event):
    """Post a new comment"""
    try:
        body = json.loads(event.get('body', '{}'))
        
        comment = {
            'id': str(uuid.uuid4()),
            'content': body.get('content', ''),
            'author': body.get('author', 'Anonymous'),
            'timestamp': datetime.utcnow().isoformat(),
            'type': 'comment'
        }
        
        table.put_item(Item=comment)
        
        return {
            'statusCode': 201,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'message': 'Comment posted successfully',
                'comment': comment
            })
        }
    except Exception as e:
        logger.error(f"Error posting comment: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({'error': 'Failed to post comment'})
        }

def get_flight_prices():
    """Get flight prices"""
    try:
        # Mock flight price data
        prices = [
            {'route': 'NYC-LAX', 'price': 299, 'airline': 'Delta'},
            {'route': 'NYC-MIA', 'price': 199, 'airline': 'American'},
            {'route': 'LAX-SEA', 'price': 149, 'airline': 'Alaska'}
        ]
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'prices': prices,
                'timestamp': datetime.utcnow().isoformat()
            })
        }
    except Exception as e:
        logger.error(f"Error getting flight prices: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({'error': 'Failed to retrieve flight prices'})
        }

def post_flight_price(event):
    """Post flight price search"""
    try:
        body = json.loads(event.get('body', '{}'))
        
        search = {
            'id': str(uuid.uuid4()),
            'from': body.get('from', ''),
            'to': body.get('to', ''),
            'date': body.get('date', ''),
            'timestamp': datetime.utcnow().isoformat(),
            'type': 'flight_search'
        }
        
        table.put_item(Item=search)
        
        return {
            'statusCode': 201,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'message': 'Flight search recorded',
                'search': search
            })
        }
    except Exception as e:
        logger.error(f"Error posting flight search: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({'error': 'Failed to record flight search'})
        }
