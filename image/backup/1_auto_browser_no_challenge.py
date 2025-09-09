#!/usr/bin/env python3
"""
Python Playwright script equivalent to auto-browser.js (No Challenge Handling)
Simulates bot behavior by visiting a URL multiple times without handling WAF challenges
Uses environment variables from .env file with command-line argument fallbacks
"""

import asyncio
import argparse
import sys
import os
from pathlib import Path
from playwright.async_api import async_playwright
from dotenv import load_dotenv

def str_to_bool(value):
    """Convert string to boolean"""
    if isinstance(value, bool):
        return value
    if str(value).lower() in ('yes', 'true', 't', 'y', '1'):
        return True
    elif str(value).lower() in ('no', 'false', 'f', 'n', '0'):
        return False
    else:
        raise argparse.ArgumentTypeError('Boolean value expected.')

async def main():
    # Load environment variables from .env file
    env_path = Path(__file__).parent / '.env'
    load_dotenv(dotenv_path=env_path)
    
    # Parse command line arguments with environment variable defaults
    parser = argparse.ArgumentParser(description='Bot simulation using Playwright (No Challenge Handling)')
    parser.add_argument('--url', 
                       default=os.getenv('TARGET_URL', 'https://d2gy6opttm3z3x.cloudfront.net'),
                       help='URL to visit (default from .env or https://d2gy6opttm3z3x.cloudfront.net)')
    parser.add_argument('--headless', 
                       type=str_to_bool,
                       default=str_to_bool(os.getenv('HEADLESS', 'false')),
                       help='Run in headless mode (default from .env or false)')
    parser.add_argument('--iterations', 
                       type=int, 
                       default=int(os.getenv('ITERATIONS', '3')),
                       help='Number of times to visit the URL (default from .env or 3)')
    parser.add_argument('--delay',
                       type=float,
                       default=float(os.getenv('DELAY', '1')),
                       help='Delay between visits in seconds (default from .env or 1)')
    parser.add_argument('--timeout',
                       type=int,
                       default=int(os.getenv('TIMEOUT', '30')),
                       help='Browser timeout in seconds (default from .env or 30)')
    parser.add_argument('--user-agent',
                       default=os.getenv('USER_AGENT', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'),
                       help='User agent string (default from .env or Chrome)')
    
    args = parser.parse_args()
    
    print(f"Configuration:")
    print(f"  URL: {args.url}")
    print(f"  Headless: {args.headless}")
    print(f"  Iterations: {args.iterations}")
    print(f"  Delay: {args.delay}s")
    print(f"  Timeout: {args.timeout}s")
    print(f"  User Agent: {args.user_agent}")
    print(f"  .env file: {'Found' if env_path.exists() else 'Not found'}")
    print(f"  Challenge Handling: DISABLED")
    print()
    
    try:
        async with async_playwright() as p:
            # Launch browser
            browser = await p.chromium.launch(
                headless=args.headless,
                timeout=args.timeout * 1000  # Convert to milliseconds
            )
            
            # Create new context with user agent
            context = await browser.new_context(
                user_agent=args.user_agent
            )
            
            # Create new page
            page = await context.new_page()
            
            # Set page timeout
            page.set_default_timeout(args.timeout * 1000)
            
            # Visit URL multiple times
            for i in range(args.iterations):
                print(f'try: {i}')
                
                # Clear cookies to force fresh request each time
                await context.clear_cookies()
                
                try:
                    # Navigate to bot-demo-1 path to trigger CloudFront function
                    bot_demo_url = args.url.rstrip('/') + '/bot-demo-1'
                    
                    # Navigate without handling challenges
                    response = await page.goto(bot_demo_url, wait_until='domcontentloaded')
                    status = response.status if response else 0
                    
                    # Simplify output - just success or blocked
                    if status == 200:
                        print(f'  ✓ Success')
                    elif status == 202:
                        print(f'  🛡️ Blocked (Challenge)')
                    elif status >= 400:
                        print(f'  ❌ Blocked ({status})')
                    else:
                        print(f'  ⚠️ Unknown ({status})')
                    
                    # Wait between requests
                    if i < args.iterations - 1:  # Don't wait after last iteration
                        await asyncio.sleep(args.delay)
                        
                except Exception as e:
                    print(f'  ✗ Error: {e}')
            
            print(f'\nCompleted {args.iterations} visits')
            
            # Keep browser open like original (comment out to close immediately)
            if not args.headless:
                print('Browser will stay open. Press Ctrl+C to close.')
                try:
                    await asyncio.sleep(3600)  # Wait 1 hour or until interrupted
                except KeyboardInterrupt:
                    print('\nClosing browser...')
            else:
                print('Headless mode - closing browser automatically.')
                await asyncio.sleep(2)  # Brief pause to see results
            
            await browser.close()
            
    except Exception as error:
        print(f'Error running: {error}', file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    asyncio.run(main())
