#!/usr/bin/env python3

import os
import asyncio
from playwright.async_api import async_playwright
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def scrape_private_page():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(user_agent=os.getenv('USER_AGENT'))
        
        try:
            base_url = os.getenv('TARGET_URL')
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
    asyncio.run(scrape_private_page())
