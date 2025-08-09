#!/usr/bin/env python3
"""
Simple robots.txt checker using Playwright
"""

import asyncio
import argparse
import sys
import os
from pathlib import Path
from playwright.async_api import async_playwright
from dotenv import load_dotenv

async def check_robots_txt(url, user_agent="*"):
    """Check robots.txt for a given URL"""
    base_url = url.rstrip('/')
    robots_url = f"{base_url}/robots.txt"
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        # Set user agent if specified
        if user_agent != "*":
            await page.set_extra_http_headers({
                'User-Agent': f'Mozilla/5.0 (compatible; {user_agent}; +http://example.com/bot.html)'
            })
        
        print(f"🤖 Checking robots.txt as: {user_agent}")
        print(f"🔍 URL: {robots_url}")
        print()
        
        try:
            response = await page.goto(robots_url)
            print(f"Status: {response.status}")
            
            if response.status == 200:
                # Get the raw text content
                content = await page.evaluate("document.body.textContent || document.body.innerText")
                
                print("✅ robots.txt found!")
                print("=" * 50)
                print(content)
                print("=" * 50)
                
                # Parse and show relevant rules
                parse_robots_rules(content, user_agent)
                
            else:
                print("❌ robots.txt not found or not accessible")
                
        except Exception as e:
            print(f"❌ Error: {e}")
        
        await browser.close()

def parse_robots_rules(content, target_user_agent):
    """Parse robots.txt and show rules for specific user agent"""
    lines = content.split('\n')
    current_user_agent = None
    rules_for_target = []
    sitemaps = []
    
    print(f"\n📋 Rules for '{target_user_agent}':")
    print("-" * 30)
    
    for line in lines:
        line = line.strip()
        if not line or line.startswith('#'):
            continue
            
        if line.lower().startswith('user-agent:'):
            current_user_agent = line.split(':', 1)[1].strip()
        elif line.lower().startswith('disallow:') and current_user_agent:
            disallow_path = line.split(':', 1)[1].strip()
            if current_user_agent == '*' or current_user_agent.lower() == target_user_agent.lower():
                rules_for_target.append(f"Disallow: {disallow_path}")
        elif line.lower().startswith('allow:') and current_user_agent:
            allow_path = line.split(':', 1)[1].strip()
            if current_user_agent == '*' or current_user_agent.lower() == target_user_agent.lower():
                rules_for_target.append(f"Allow: {allow_path}")
        elif line.lower().startswith('sitemap:'):
            sitemap_url = line.split(':', 1)[1].strip()
            sitemaps.append(sitemap_url)
    
    if rules_for_target:
        for rule in rules_for_target:
            print(f"  {rule}")
    else:
        print("  No specific rules found (all paths allowed)")
    
    if sitemaps:
        print(f"\n🗺️  Sitemaps found:")
        for sitemap in sitemaps:
            print(f"  {sitemap}")

async def main():
    # Load environment variables
    env_path = Path(__file__).parent / '.env'
    load_dotenv(dotenv_path=env_path)
    
    parser = argparse.ArgumentParser(description='Check robots.txt file')
    parser.add_argument('--url', 
                       default=os.getenv('URL', 'https://d2gy6opttm3z3x.cloudfront.net'),
                       help='URL to check robots.txt for')
    parser.add_argument('--user-agent', 
                       default='Googlebot',
                       help='User agent to check rules for')
    
    args = parser.parse_args()
    
    await check_robots_txt(args.url, args.user_agent)

if __name__ == '__main__':
    asyncio.run(main())
