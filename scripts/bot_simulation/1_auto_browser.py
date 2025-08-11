#!/usr/bin/env python3
"""
Python Playwright script equivalent to auto-browser.js
Simulates bot behavior by visiting a URL multiple times
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
    parser = argparse.ArgumentParser(description='Bot simulation using Playwright')
    parser.add_argument('--url', 
                       default=os.getenv('URL', 'https://d2gy6opttm3z3x.cloudfront.net'),
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
    
    args = parser.parse_args()
    
    print(f"Configuration:")
    print(f"  URL: {args.url}")
    print(f"  Headless: {args.headless}")
    print(f"  Iterations: {args.iterations}")
    print(f"  Delay: {args.delay}s")
    print(f"  Timeout: {args.timeout}s")
    print(f"  .env file: {'Found' if env_path.exists() else 'Not found'}")
    print()
    
    try:
        async with async_playwright() as p:
            # Launch browser
            browser = await p.chromium.launch(
                headless=args.headless,
                timeout=args.timeout * 1000  # Convert to milliseconds
            )
            
            # Create new page
            page = await browser.new_page()
            
            # Set page timeout
            page.set_default_timeout(args.timeout * 1000)
            
            # Visit URL multiple times
            for i in range(args.iterations):
                print(f'try: {i}')
                
                try:
                    # Navigate to URL
                    await page.goto(args.url)
                    print(f'  ✓ Successfully loaded: {args.url}')
                    
                    # Wait between requests
                    if i < args.iterations - 1:  # Don't wait after last iteration
                        await asyncio.sleep(args.delay)
                        
                except Exception as e:
                    print(f'  ✗ Error loading page: {e}')
            
            print(f'\nCompleted {args.iterations} visits to {args.url}')
            
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
