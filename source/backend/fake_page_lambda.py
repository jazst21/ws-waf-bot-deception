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
        "dns-security-fundamentals",
        "network-intrusion-detection",
        "web-application-security",
        "ssl-tls-encryption",
        "firewall-configuration",
        "penetration-testing-basics",
        "malware-analysis",
        "incident-response-procedures",
        "vulnerability-assessment",
        "secure-coding-practices",
        "authentication-mechanisms",
        "authorization-frameworks",
        "cryptography-essentials",
        "network-monitoring-tools",
        "security-information-event-management",
        "threat-intelligence",
        "digital-forensics",
        "cloud-security-architecture"
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
    """Generate a fake HTML page for the given topic"""
    
    title = topic.replace('-', ' ').title()
    
    # Generate random navigation links to other pages
    other_topics = [t for t in all_topics if t != topic]
    nav_links = random.sample(other_topics, min(5, len(other_topics)))
    
    nav_html = ""
    for nav_topic in nav_links:
        nav_title = nav_topic.replace('-', ' ').title()
        nav_html += f'            <li><a href="/private/{nav_topic}.html">{nav_title}</a></li>\n'
    
    # Generate fake content based on topic
    content_sections = generate_content_sections(topic)
    
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="description" content="Comprehensive guide to {title} - Professional cybersecurity resource">
    <meta name="keywords" content="cybersecurity, {topic.replace('-', ', ')}, security, information security">
    <meta name="author" content="CyberSec Academy">
    <title>{title} - CyberSec Academy</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background-color: #f8f9fa;
            color: #333;
            margin: 0;
            padding: 0;
            line-height: 1.6;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }}
        header {{
            background: linear-gradient(135deg, #4a6fa5, #6f42c1);
            color: white;
            padding: 2rem 0;
            margin-bottom: 2rem;
            border-radius: 8px;
        }}
        h1 {{
            margin: 0;
            font-size: 2.5rem;
            text-align: center;
        }}
        .subtitle {{
            text-align: center;
            font-size: 1.2rem;
            opacity: 0.9;
            margin-top: 0.5rem;
        }}
        .navigation {{
            background-color: #ffffff;
            border: 1px solid #dee2e6;
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 2rem;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .navigation h3 {{
            color: #4a6fa5;
            margin-top: 0;
        }}
        .navigation ul {{
            list-style-type: none;
            padding: 0;
            display: flex;
            flex-wrap: wrap;
            gap: 15px;
        }}
        .navigation li {{
            background-color: #f8f9fa;
            border-radius: 5px;
        }}
        .navigation a {{
            color: #4a6fa5;
            text-decoration: none;
            padding: 8px 15px;
            display: block;
            border-radius: 5px;
            transition: all 0.3s;
        }}
        .navigation a:hover {{
            background-color: #4a6fa5;
            color: white;
        }}
        .content {{
            background-color: #ffffff;
            border-radius: 8px;
            padding: 2rem;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            margin-bottom: 2rem;
        }}
        .content h2 {{
            color: #4a6fa5;
            border-bottom: 2px solid #4a6fa5;
            padding-bottom: 10px;
        }}
        .code-block {{
            background-color: #f8f9fa;
            border: 1px solid #e9ecef;
            border-radius: 5px;
            padding: 15px;
            font-family: 'Courier New', monospace;
            margin: 15px 0;
            overflow-x: auto;
        }}
        .warning {{
            background-color: #fff3cd;
            border: 1px solid #ffeaa7;
            color: #856404;
            padding: 15px;
            border-radius: 5px;
            margin: 20px 0;
        }}
        .info {{
            background-color: #d1ecf1;
            border: 1px solid #bee5eb;
            color: #0c5460;
            padding: 15px;
            border-radius: 5px;
            margin: 20px 0;
        }}
        .footer {{
            text-align: center;
            color: #6c757d;
            border-top: 1px solid #dee2e6;
            padding-top: 20px;
            margin-top: 3rem;
        }}
        @media (max-width: 768px) {{
            .navigation ul {{
                flex-direction: column;
            }}
            h1 {{
                font-size: 2rem;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>🔒 {title}</h1>
            <div class="subtitle">Professional Cybersecurity Resource</div>
        </header>
        
        <div class="navigation">
            <h3>📚 Related Resources</h3>
            <ul>
{nav_html}
            </ul>
        </div>
        
        <div class="content">
{content_sections}
        </div>
        
        <div class="footer">
            <p>&copy; 2024 CyberSec Academy - Professional Security Training</p>
            <p><em>This content is for educational purposes only</em></p>
            <p>Last updated: {datetime.now().strftime('%B %d, %Y')}</p>
        </div>
    </div>
</body>
</html>"""

def generate_content_sections(topic):
    """Generate realistic content sections based on the topic"""
    
    content_templates = {
        "cyber-security-101": """
            <h2>Introduction to Cybersecurity</h2>
            <p>Cybersecurity is the practice of protecting systems, networks, and programs from digital attacks. These cyberattacks are usually aimed at accessing, changing, or destroying sensitive information.</p>
            
            <div class="info">
                <strong>Key Principles:</strong> Confidentiality, Integrity, and Availability (CIA Triad)
            </div>
            
            <h2>Common Threats</h2>
            <ul>
                <li><strong>Malware:</strong> Malicious software designed to damage or disrupt systems</li>
                <li><strong>Phishing:</strong> Fraudulent attempts to obtain sensitive information</li>
                <li><strong>Ransomware:</strong> Malware that encrypts files and demands payment</li>
                <li><strong>Social Engineering:</strong> Psychological manipulation to divulge information</li>
            </ul>
            
            <h2>Best Practices</h2>
            <div class="code-block">
# Security Checklist
1. Use strong, unique passwords
2. Enable two-factor authentication
3. Keep software updated
4. Regular security training
5. Implement network segmentation
            </div>
        """,
        
        "network-intrusion-detection": """
            <h2>Network Intrusion Detection Systems (NIDS)</h2>
            <p>Network Intrusion Detection Systems monitor network traffic for suspicious activity and known threats, providing real-time analysis of security alerts.</p>
            
            <div class="warning">
                <strong>Critical:</strong> Proper NIDS configuration is essential for effective threat detection
            </div>
            
            <h2>Detection Methods</h2>
            <ul>
                <li><strong>Signature-based:</strong> Matches known attack patterns</li>
                <li><strong>Anomaly-based:</strong> Detects deviations from normal behavior</li>
                <li><strong>Hybrid:</strong> Combines both approaches for comprehensive coverage</li>
            </ul>
            
            <h2>Implementation Example</h2>
            <div class="code-block">
# Snort Rule Example
alert tcp any any -> 192.168.1.0/24 80 (
    msg:"Potential SQL Injection Attack";
    content:"union select";
    nocase;
    sid:1000001;
)
            </div>
        """,
        
        "default": f"""
            <h2>Overview</h2>
            <p>This comprehensive guide covers essential aspects of {topic.replace('-', ' ')} in modern cybersecurity environments.</p>
            
            <div class="info">
                <strong>Learning Objectives:</strong> Understand key concepts, implementation strategies, and best practices
            </div>
            
            <h2>Key Concepts</h2>
            <ul>
                <li>Fundamental principles and methodologies</li>
                <li>Industry standards and compliance requirements</li>
                <li>Risk assessment and mitigation strategies</li>
                <li>Implementation best practices</li>
            </ul>
            
            <h2>Practical Implementation</h2>
            <div class="code-block">
# Configuration Example
security_policy = {{
    "encryption": "AES-256",
    "authentication": "multi-factor",
    "logging": "enabled",
    "monitoring": "continuous"
}}
            </div>
            
            <div class="warning">
                <strong>Important:</strong> Always follow your organization's security policies and procedures
            </div>
        """
    }
    
    return content_templates.get(topic, content_templates["default"])

def generate_index_page(topics):
    """Generate an index page that links to all fake pages"""
    
    links_html = ""
    for topic in topics:
        title = topic.replace('-', ' ').title()
        links_html += f'                <li><a href="/private/{topic}.html">{title}</a></li>\n'
    
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="description" content="Private cybersecurity resources and training materials">
    <title>Private Security Resources - CyberSec Academy</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background-color: #f8f9fa;
            color: #333;
            margin: 0;
            padding: 20px;
            line-height: 1.6;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
        }}
        header {{
            background: linear-gradient(135deg, #4a6fa5, #6f42c1);
            color: white;
            padding: 2rem;
            border-radius: 8px;
            text-align: center;
            margin-bottom: 2rem;
        }}
        h1 {{
            margin: 0;
            font-size: 2.5rem;
        }}
        .warning {{
            background-color: #fff3cd;
            border: 1px solid #ffeaa7;
            color: #856404;
            padding: 20px;
            border-radius: 8px;
            margin: 20px 0;
            text-align: center;
        }}
        .resources-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-top: 30px;
        }}
        .resource-category {{
            background-color: #ffffff;
            border: 1px solid #dee2e6;
            border-radius: 8px;
            padding: 25px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .resource-category h3 {{
            color: #4a6fa5;
            margin-top: 0;
            font-size: 1.3rem;
        }}
        .resource-category ul {{
            list-style-type: none;
            padding: 0;
        }}
        .resource-category li {{
            margin: 10px 0;
        }}
        .resource-category a {{
            color: #4a6fa5;
            text-decoration: none;
            padding: 8px 12px;
            border-radius: 5px;
            transition: all 0.3s;
            display: block;
            border: 1px solid transparent;
        }}
        .resource-category a:hover {{
            background-color: #4a6fa5;
            color: white;
            border-color: #4a6fa5;
        }}
        .footer {{
            margin-top: 50px;
            text-align: center;
            color: #6c757d;
            border-top: 1px solid #dee2e6;
            padding-top: 20px;
        }}
        .stats {{
            background-color: #d1ecf1;
            border: 1px solid #bee5eb;
            color: #0c5460;
            padding: 15px;
            border-radius: 8px;
            margin: 20px 0;
            text-align: center;
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>🔒 Private Security Resources</h1>
            <p>Professional Cybersecurity Training Materials</p>
        </header>
        
        <div class="warning">
            <strong>⚠️ Access Restricted:</strong> This directory contains sensitive security documentation and training materials. 
            Access is logged and monitored. Unauthorized access is prohibited.
        </div>
        
        <div class="stats">
            <strong>📊 Resource Statistics:</strong> {len(topics)} comprehensive guides available | 
            Last updated: {datetime.now().strftime('%B %d, %Y')} | 
            Access level: Professional
        </div>
        
        <p>Welcome to our comprehensive cybersecurity resource library. These materials are designed for security professionals, 
        researchers, and students looking to deepen their understanding of information security concepts and practices.</p>
        
        <div class="resources-grid">
            <div class="resource-category">
                <h3>📚 Available Security Guides</h3>
                <ul>
{links_html}
                </ul>
            </div>
        </div>
        
        <div class="footer">
            <p>&copy; 2024 CyberSec Academy - Professional Security Training</p>
            <p><em>This content is generated for educational and demonstration purposes</em></p>
            <p>For support, contact: security-training@cybersecacademy.com</p>
        </div>
    </div>
</body>
</html>"""

# For backwards compatibility
handler = lambda_handler
