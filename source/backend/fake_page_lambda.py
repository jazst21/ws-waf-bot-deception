import json
import boto3
import os
import random
import time
from datetime import datetime, timezone
from botocore.config import Config
from botocore.exceptions import ClientError

def lambda_handler(event, context):
    """
    Lambda function to generate fake webpages and upload them to S3 bucket
    for bot deception purposes
    """
    
    # Get S3 bucket name from environment or event
    bucket_name = os.environ.get('S3_BUCKET_NAME')
    if not bucket_name and event.get('bucket_name'):
        bucket_name = event['bucket_name']
    
    if not bucket_name:
        return {
            'statusCode': 400,
            'body': json.dumps({
                'error': 'S3_BUCKET_NAME environment variable or bucket_name parameter required'
            })
        }
    
    # Configure timeout settings for AWS clients
    config = Config(
        read_timeout=300,  # 5 minutes
        connect_timeout=60,  # 1 minute
        retries={'max_attempts': 3}
    )
    
    # Initialize AWS clients
    s3_client = boto3.client('s3', region_name=os.environ.get('AWS_REGION', 'us-east-1'), config=config)
    
    # Topics for fake pages (cybersecurity focused)
    topics = [
        "cyber-security-101",
        "http-protocol-deep-dive", 
        "dns-security-fundamentals"
    ]
    
    try:
        generated_pages = []
        
        # Determine how many pages to generate
        page_count = min(len(topics), event.get('page_count', 10))
        selected_topics = random.sample(topics, page_count)
        
        # Generate fake pages
        for i, topic in enumerate(selected_topics):
            print(f"Generating page {i+1}/{page_count}: {topic}")
            
            # Generate HTML content (without Bedrock for simplicity)
            content = generate_fake_html_page(topic, selected_topics)
            
            # Upload to S3
            s3_key = f"private/{topic}.html"
            s3_client.put_object(
                Bucket=bucket_name,
                Key=s3_key,
                Body=content,
                ContentType='text/html',
                CacheControl='max-age=3600',
                Metadata={
                    'generated-by': 'fake-page-lambda',
                    'generated-at': str(int(time.time())),
                    'topic': topic
                }
            )
            
            generated_pages.append({
                'topic': topic,
                's3_key': s3_key,
                'size': len(content),
                'url': f"https://{bucket_name}.s3.amazonaws.com/{s3_key}"
            })
            
            print(f"Successfully generated and uploaded: {s3_key}")
        
        # Create an index page that links to all generated pages
        index_content = generate_index_page(selected_topics)
        s3_client.put_object(
            Bucket=bucket_name,
            Key="private/index.html",
            Body=index_content,
            ContentType='text/html',
            CacheControl='max-age=3600',
            Metadata={
                'generated-by': 'fake-page-lambda',
                'generated-at': str(int(time.time())),
                'type': 'index'
            }
        )
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'message': f'Successfully generated {len(generated_pages)} fake pages',
                'pages': generated_pages,
                'index_page': 'private/index.html',
                'bucket': bucket_name,
                'timestamp': datetime.now(timezone.utc).isoformat()
            })
        }
        
    except ClientError as e:
        print(f"AWS Error: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': f'AWS Error: {str(e)}',
                'error_code': e.response['Error']['Code']
            })
        }
    except Exception as e:
        print(f"Error: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e)
            })
        }

def generate_fake_html_page(topic, all_topics):
    """Generate a fake HTML page using Amazon Bedrock"""
    
    # Initialize Bedrock client
    bedrock = boto3.client('bedrock-runtime', region_name=os.environ.get('AWS_REGION', 'us-east-1'))
    
    # Create navigation links
    other_topics = [t for t in all_topics if t != topic]
    nav_links = random.sample(other_topics, min(5, len(other_topics)))
    nav_list = ', '.join([f'"{t.replace("-", " ").title()}"' for t in nav_links])
    
    prompt = f"""Create a complete HTML page about "{topic.replace('-', ' ').title()}" for cybersecurity education.

Requirements:
- Professional cybersecurity content with technical depth
- Include navigation links to: {nav_list}
- Use modern CSS styling with blue/purple color scheme
- Include code examples and security best practices
- Add warning/info boxes for important points
- Make it look like a legitimate security training resource
- Include meta tags and proper HTML structure

Topic: {topic.replace('-', ' ').title()}

Generate a complete, professional HTML page."""

    try:
        response = bedrock.converse(
            modelId="anthropic.claude-3-haiku-20240307-v1:0",
            messages=[{"role": "user", "content": [{"text": prompt}]}],
            inferenceConfig={"maxTokens": 4000, "temperature": 0.7}
        )
        
        content = response['output']['message']['content'][0]['text']
        
        # Ensure we have valid HTML
        if not content.strip().startswith('<!DOCTYPE html>'):
            content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>{topic.replace('-', ' ').title()}</title>
</head>
<body>
{content}
</body>
</html>"""
        
        return content
        
    except Exception as e:
        print(f"Bedrock error: {str(e)}")
        # Fallback to minimal HTML
        title = topic.replace('-', ' ').title()
        return f"""<!DOCTYPE html>
<html><head><title>{title} - CyberSec Academy</title></head>
<body><h1>{title}</h1><p>Content generation temporarily unavailable.</p></body></html>"""

def generate_index_page(topics):
    """Generate an index page using Amazon Bedrock"""
    
    bedrock = boto3.client('bedrock-runtime', region_name=os.environ.get('AWS_REGION', 'us-east-1'))
    
    topics_list = ', '.join([f'"{t.replace("-", " ").title()}"' for t in topics])
    
    prompt = f"""Create a professional HTML index page for a cybersecurity training portal.

Requirements:
- Title: "Private Security Resources - CyberSec Academy"
- Professional styling with blue/purple color scheme
- Warning about restricted access and monitoring
- Grid layout showing available resources
- Link to these topics: {topics_list}
- Each link should go to /private/[topic].html
- Include access statistics and professional footer
- Make it look like a legitimate corporate security portal

Generate a complete, professional HTML index page."""

    try:
        response = bedrock.converse(
            modelId="anthropic.claude-3-haiku-20240307-v1:0",
            messages=[{"role": "user", "content": [{"text": prompt}]}],
            inferenceConfig={"maxTokens": 4000, "temperature": 0.7}
        )
        
        content = response['output']['message']['content'][0]['text']
        
        if not content.strip().startswith('<!DOCTYPE html>'):
            content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Private Security Resources</title>
</head>
<body>
{content}
</body>
</html>"""
        
        return content
        
    except Exception as e:
        print(f"Bedrock error for index: {str(e)}")
        # Fallback index
        links_html = ''.join([f'<li><a href="/private/{topic}.html">{topic.replace("-", " ").title()}</a></li>' for topic in topics])
        return f"""<!DOCTYPE html>
<html><head><title>Private Security Resources - CyberSec Academy</title></head>
<body><h1>Security Resources</h1><ul>{links_html}</ul></body></html>"""

# For backwards compatibility
handler = lambda_handler
