#!/usr/bin/env python3

import os
import asyncio
import argparse
from pathlib import Path
from playwright.async_api import async_playwright
from dotenv import load_dotenv

# Load environment variables
env_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path)

# Parse command line arguments with environment variable defaults
parser = argparse.ArgumentParser(description='Private page scraper using Playwright')
parser.add_argument('--url', 
                   default=os.getenv('TARGET_URL', 'https://d3mx9cjq6wwawz.cloudfront.net'),
                   help='Base URL for the website (default from TARGET_URL env var)')

async def scrape_private_page(base_url):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(user_agent=os.getenv('USER_AGENT'))
        
        try:
            target_url = f"{base_url}/private"
            
            print(f"Scraping URL: {target_url}")
            
            # Navigate and wait for potential JS challenges
            await page.goto(target_url, wait_until='networkidle')
            
            # Wait for AWS WAF token processing
            await page.wait_for_timeout(3000)
            
            # Get final HTML content
            html_content = await page.content()
            
            print("=== HTML Response ===")
            print(html_content)
            
        except Exception as e:
            print(f"Error: {e}")
        finally:
            await browser.close()

if __name__ == "__main__":
    args = parser.parse_args()
    asyncio.run(scrape_private_page(args.url))
