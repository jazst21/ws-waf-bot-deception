#!/usr/bin/env python3
"""
Flight price scraping bot simulation for bot-demo-3 page
"""

import asyncio
import argparse
import sys
import os
import json
from pathlib import Path
from playwright.async_api import async_playwright
from dotenv import load_dotenv

class FlightScraper:
    def __init__(self):
        self.flights_data = []
        
    async def setup_api_interception(self, page):
        """Setup API response interception"""
        async def handle_response(response):
            if '/api/bot-demo-3/flights' in response.url:
                print(f"📡 Captured API response: {response.url} (Status: {response.status})")
                if response.status == 200:
                    try:
                        data = await response.json()
                        if 'flights' in data:
                            flights = data['flights']
                            print(f"✅ Found {len(flights)} flights in API response")
                            self.flights_data = flights  # Replace, don't extend
                    except Exception as e:
                        print(f"❌ Error parsing API response: {e}")
        
        page.on('response', handle_response)
    
    def format_flight_table(self, flights):
        """Format flights as ASCII table"""
        if not flights:
            print("No flight data available")
            return
        
        print(f"\n📊 Flight Data ({len(flights)} flights)")
        print("=" * 120)
        print("│ {:25} │ {:18} │ {:12} │ {:12} │ {:10} │ {:8} │ {:8} │".format(
            "Route", "Airline", "Departure", "Arrival", "Duration", "Price", "Discount"))
        print("├" + "─" * 27 + "┼" + "─" * 20 + "┼" + "─" * 14 + "┼" + "─" * 14 + "┼" + "─" * 12 + "┼" + "─" * 10 + "┼" + "─" * 10 + "┤")
        
        for flight in flights:
            route = flight.get('route', 'Unknown')[:25]
            airline = flight.get('airline', 'Unknown')[:18]
            departure = flight.get('departure', 'Unknown')[:12]
            arrival = flight.get('arrival', 'Unknown')[:12]
            duration = flight.get('duration', 'Unknown')[:10]
            price = f"${flight.get('price', 0)}"[:8]
            discount = f"{flight.get('discount', 0)}%"[:8]
            
            print("│ {:25} │ {:18} │ {:12} │ {:12} │ {:10} │ {:8} │ {:8} │".format(
                route, airline, departure, arrival, duration, price, discount))
        
        print("└" + "─" * 27 + "┴" + "─" * 20 + "┴" + "─" * 14 + "┴" + "─" * 14 + "┴" + "─" * 12 + "┴" + "─" * 10 + "┴" + "─" * 10 + "┘")

async def main():
    # Load environment variables
    env_path = Path(__file__).parent / '.env'
    load_dotenv(dotenv_path=env_path)
    
    parser = argparse.ArgumentParser(description='Flight price scraping bot')
    parser.add_argument('--url', 
                       default=os.getenv('URL', 'https://dhmxm3xqfs2e5.cloudfront.net'),
                       help='Base URL for the website')
    parser.add_argument('--headless', 
                       type=lambda x: x.lower() == 'true',
                       default=False,
                       help='Run in headless mode')
    
    args = parser.parse_args()
    
    bot_demo_url = f"{args.url.rstrip('/')}/bot-demo-3"
    
    print(f"🤖 Starting flight price scraper...")
    print(f"📍 Target: {bot_demo_url}")
    print("-" * 50)
    
    scraper = FlightScraper()
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=args.headless,
            args=['--no-sandbox', '--disable-setuid-sandbox']
        )
        
        try:
            context = await browser.new_context(
                # user_agent='Mozilla/5.0 (compatible; FlightBot/1.0; +http://example.com/bot)'
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            )
            
            page = await context.new_page()
            await scraper.setup_api_interception(page)
            
            print(f"🌐 Navigating to {bot_demo_url}...")
            await page.goto(bot_demo_url)
            await page.wait_for_load_state('networkidle')
            await asyncio.sleep(2)
            
            # Look for price/search buttons
            button_selectors = [
                'button:has-text("Get Prices")',
                'button:has-text("Search")',
                'button:has-text("Find Flights")',
                'button:has-text("Load")',
                'button[class*="price"]',
                'button[class*="search"]',
                '.search-btn',
                '.price-btn'
            ]
            
            button_found = False
            for selector in button_selectors:
                try:
                    button = page.locator(selector)
                    if await button.count() > 0:
                        print(f"🔄 Clicking button: {selector}")
                        await button.first.click()
                        await asyncio.sleep(2)
                        button_found = True
                        break
                except:
                    continue
            
            if not button_found:
                print("⚠️  No price button found, trying to trigger API manually...")
                # Try to make direct API call
                try:
                    response = await page.request.get(f"{args.url}/api/bot-demo-3/flights")
                    if response.status == 200:
                        data = await response.json()
                        if 'flights' in data:
                            scraper.flights_data = data['flights']
                            print(f"✅ Direct API call successful: {len(scraper.flights_data)} flights")
                except Exception as e:
                    print(f"❌ Direct API call failed: {e}")
            
            # Display results
            if scraper.flights_data:
                scraper.format_flight_table(scraper.flights_data)
                
                # Summary
                total_flights = len(scraper.flights_data)
                avg_price = sum(f.get('price', 0) for f in scraper.flights_data) / total_flights if total_flights > 0 else 0
                
                print(f"\n📈 Summary:")
                print(f"✅ Total flights: {total_flights}")
                print(f"💰 Average price: ${avg_price:.2f}")
                print(f"🤖 Bot detected: {scraper.flights_data[0].get('isBot', 'Unknown') if scraper.flights_data else 'Unknown'}")
            else:
                print("❌ No flight data collected")
            
        except Exception as e:
            print(f"❌ Error during scraping: {str(e)}")
            return 1
        finally:
            await browser.close()
    
    return 0

if __name__ == '__main__':
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n🛑 Scraping interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
        sys.exit(1)
