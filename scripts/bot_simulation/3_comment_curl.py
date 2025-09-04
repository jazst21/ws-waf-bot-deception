#!/usr/bin/env python3
"""
Simple bot comment submission using curl/requests
Uses basic HTTP requests without browser simulation to trigger WAF bot detection
"""

import requests
import json
import random
import time
import argparse

# Bot-like user agents that should trigger WAF detection
BOT_USER_AGENTS = [
    'curl/7.68.0',
    'python-requests/2.25.1',
    'Scrapy/2.5.0',
    'wget/1.20.3',
    'HTTPie/2.4.0',
    'PostmanRuntime/7.28.0',
    'Go-http-client/1.1',
    'Apache-HttpClient/4.5.13',
    'okhttp/4.9.1',
    'libwww-perl/6.43'
]

# Sample negative reviews
SAMPLE_REVIEWS = [
    {"name": "Bot User 1", "rating": 1, "comment": "Terrible service, worst hotel ever!"},
    {"name": "Bot User 2", "rating": 1, "comment": "Dirty rooms, broken facilities, avoid this place!"},
    {"name": "Bot User 3", "rating": 2, "comment": "Overpriced and disappointing experience."},
    {"name": "Bot User 4", "rating": 1, "comment": "Staff was rude, room was disgusting."},
    {"name": "Bot User 5", "rating": 2, "comment": "Nothing worked, complete waste of money."}
]

def submit_comment(url, review_data, user_agent=None):
    """Submit a comment using simple HTTP POST"""
    try:
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        
        if user_agent:
            headers['User-Agent'] = user_agent
            print(f"Using User-Agent: {user_agent}")
        
        response = requests.post(
            f"{url}/api/comments",
            json=review_data,
            headers=headers,
            timeout=10
        )
        
        print(f"Response Status: {response.status_code}")
        if response.status_code == 201:
            print(f"✓ Comment submitted: {review_data['name']}")
            return True
        else:
            print(f"✗ Failed to submit: {response.text}")
            return False
            
    except Exception as e:
        print(f"✗ Error submitting comment: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description='Simple bot comment submission')
    parser.add_argument('--url', default='https://dhmxm3xqfs2e5.cloudfront.net', help='Base URL')
    parser.add_argument('--count', type=int, default=3, help='Number of comments to submit')
    parser.add_argument('--delay', type=float, default=1, help='Delay between requests')
    
    args = parser.parse_args()
    
    print(f"🤖 Starting simple bot comment submission...")
    print(f"📍 Target URL: {args.url}")
    print(f"🔄 Comments to submit: {args.count}")
    print("-" * 50)
    
    successful = 0
    
    for i in range(args.count):
        print(f"\n📝 Submission {i + 1}/{args.count}")
        
        # Select random review and user agent
        review = random.choice(SAMPLE_REVIEWS)
        user_agent = random.choice(BOT_USER_AGENTS)
        
        success = submit_comment(args.url, review, user_agent)
        if success:
            successful += 1
        
        if i < args.count - 1:
            print(f"⏳ Waiting {args.delay}s...")
            time.sleep(args.delay)
    
    print(f"\n🏁 Completed: {successful}/{args.count} successful submissions")

if __name__ == '__main__':
    main()
