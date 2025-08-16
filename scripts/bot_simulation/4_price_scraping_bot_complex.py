#!/usr/bin/env python3
"""
Price scraping bot for pricing-demo-3 flight booking page
Simulates competitive price monitoring and data extraction
Uses environment variables from .env file with command-line argument fallbacks
"""

import asyncio
import argparse
import sys
import os
import json
import csv
import time
from pathlib import Path
from datetime import datetime
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

class FlightPriceScraper:
    def __init__(self, base_url, headless=True, delay=2):
        self.base_url = base_url
        self.headless = headless
        self.delay = delay
        self.scraped_data = []
        self.session_id = int(time.time())
        
    async def scrape_flight_prices(self, page):
        """Scrape flight pricing data from the page"""
        try:
            print("🔍 Extracting flight pricing data...")
            
            # Extract flight data using multiple methods
            flight_data = []
            
            # Method 1: Extract from API response (intercept network requests) - Most reliable
            api_data = await self.extract_from_api_response(page)
            if api_data:
                flight_data.extend(api_data)
                print(f"✅ Extracted {len(api_data)} flights from API response")
            
            # Method 2: Try to find and click refresh button to trigger API calls
            if not flight_data:
                print("🔄 Attempting to trigger API calls...")
                try:
                    # Look for refresh button
                    refresh_selectors = [
                        'button:has-text("Refresh")',
                        'button:has-text("refresh")',
                        'button[class*="refresh"]',
                        'button:has-text("Load")',
                        'button:has-text("Get")'
                    ]
                    
                    for selector in refresh_selectors:
                        refresh_button = page.locator(selector)
                        if await refresh_button.count() > 0:
                            print(f"🎯 Found refresh button: {selector}")
                            await refresh_button.first.click()
                            await asyncio.sleep(self.delay * 2)
                            
                            # Try API extraction again
                            api_data = await self.extract_from_api_response(page)
                            if api_data:
                                flight_data.extend(api_data)
                                print(f"✅ Extracted {len(api_data)} flights after refresh")
                                break
                except Exception as e:
                    print(f"⚠️ Error clicking refresh: {str(e)}")
            
            # Method 3: Extract from DOM elements as fallback
            if not flight_data:
                dom_data = await self.extract_from_dom(page)
                if dom_data:
                    flight_data.extend(dom_data)
                    print(f"✅ Extracted {len(dom_data)} flights from DOM")
            
            # Method 4: Extract from JavaScript variables as last resort
            if not flight_data:
                js_data = await self.extract_from_javascript(page)
                if js_data:
                    flight_data.extend(js_data)
                    print(f"✅ Extracted {len(js_data)} flights from JavaScript")
            
            return flight_data
            
        except Exception as e:
            print(f"❌ Error scraping flight prices: {str(e)}")
            return []
    
    async def extract_from_api_response(self, page):
        """Extract flight data by intercepting API responses"""
        flight_data = []
        
        try:
            # Refresh the page to trigger API call
            print("🔄 Refreshing page to capture API response...")
            
            # Set up response interception
            responses = []
            
            def handle_response(response):
                if '/api/pricing-demo-3/flights' in response.url:
                    responses.append(response)
            
            page.on('response', handle_response)
            
            # Click refresh button to trigger API call
            refresh_button = page.locator('button:has-text("Refresh Flights")')
            if await refresh_button.count() > 0:
                await refresh_button.click()
                await asyncio.sleep(self.delay * 2)
            
            # Process captured responses
            for response in responses:
                try:
                    if response.status == 200:
                        json_data = await response.json()
                        if 'flights' in json_data:
                            for flight in json_data['flights']:
                                flight_data.append({
                                    'source': 'API',
                                    'timestamp': datetime.now().isoformat(),
                                    'route': flight.get('route', 'Unknown'),
                                    'airline': flight.get('airline', 'Unknown'),
                                    'departure': flight.get('departure', 'Unknown'),
                                    'arrival': flight.get('arrival', 'Unknown'),
                                    'duration': flight.get('duration', 'Unknown'),
                                    'price': flight.get('price', 0),
                                    'original_price': flight.get('originalPrice', 0),
                                    'discount': flight.get('discount', 0),
                                    'bot_price': flight.get('botPrice'),
                                    'user_price': flight.get('userPrice'),
                                    'pricing_strategy': json_data.get('pricingStrategy', 'unknown'),
                                    'is_bot_detected': json_data.get('isBot', False)
                                })
                except Exception as e:
                    print(f"⚠️ Error processing API response: {str(e)}")
            
        except Exception as e:
            print(f"⚠️ Error intercepting API responses: {str(e)}")
        
        return flight_data
    
    async def extract_from_dom(self, page):
        """Extract flight data from DOM elements"""
        flight_data = []
        
        try:
            # Wait for CloudScape Cards component to be visible
            await page.wait_for_selector('.awsui-cards-container', timeout=5000)
            
            # Extract flight cards from CloudScape Cards component
            flight_cards = page.locator('.awsui-cards-container .awsui-cards-card-container')
            card_count = await flight_cards.count()
            
            print(f"🎯 Found {card_count} flight cards in DOM")
            
            for i in range(card_count):
                try:
                    card = flight_cards.nth(i)
                    
                    # Extract route information (header h3)
                    route_element = card.locator('h3').first
                    route = await route_element.text_content() if await route_element.count() > 0 else 'Unknown'
                    
                    # Extract airline (text below route)
                    airline_elements = card.locator('div:has-text("SkyWings"), div:has-text("PacificAir"), div:has-text("EuroConnect"), div:has-text("Mediterranean Air"), div:has-text("Pacific Rim"), div:has-text("Italian Wings")')
                    airline = await airline_elements.first.text_content() if await airline_elements.count() > 0 else 'Unknown'
                    
                    # Extract price (large blue text with $)
                    price_elements = page.locator('div[style*="color: #0073bb"], div[style*="color:#0073bb"]')
                    price_text = ''
                    for j in range(await price_elements.count()):
                        text = await price_elements.nth(j).text_content()
                        if '$' in text and any(char.isdigit() for char in text):
                            price_text = text
                            break
                    
                    price = int(''.join(filter(str.isdigit, price_text))) if price_text else 0
                    
                    # Extract departure/arrival times (look for AM/PM)
                    time_elements = card.locator('div:has-text("AM"), div:has-text("PM")')
                    times = []
                    for j in range(min(2, await time_elements.count())):
                        time_text = await time_elements.nth(j).text_content()
                        if 'AM' in time_text or 'PM' in time_text:
                            times.append(time_text.strip())
                    
                    departure = times[0] if len(times) > 0 else 'Unknown'
                    arrival = times[1] if len(times) > 1 else 'Unknown'
                    
                    # Extract duration (look for "h" pattern)
                    duration_elements = card.locator('div:has-text("h ")')
                    duration = 'Unknown'
                    for j in range(await duration_elements.count()):
                        text = await duration_elements.nth(j).text_content()
                        if 'h' in text and any(char.isdigit() for char in text):
                            duration = text.strip()
                            break
                    
                    # Look for discount badges
                    discount_elements = card.locator('.awsui-badge, [class*="badge"]')
                    discount = 0
                    for j in range(await discount_elements.count()):
                        text = await discount_elements.nth(j).text_content()
                        if 'OFF' in text or '%' in text:
                            discount_match = ''.join(filter(str.isdigit, text))
                            discount = int(discount_match) if discount_match else 0
                            break
                    
                    flight_data.append({
                        'source': 'DOM',
                        'timestamp': datetime.now().isoformat(),
                        'route': route.strip(),
                        'airline': airline.strip(),
                        'departure': departure,
                        'arrival': arrival,
                        'duration': duration,
                        'price': price,
                        'original_price': None,
                        'discount': discount if discount > 0 else None,
                        'bot_price': None,
                        'user_price': None,
                        'pricing_strategy': 'unknown',
                        'is_bot_detected': None
                    })
                    
                except Exception as e:
                    print(f"⚠️ Error extracting data from card {i}: {str(e)}")
            
        except Exception as e:
            print(f"⚠️ Error extracting from DOM: {str(e)}")
        
        return flight_data
    
    async def extract_from_javascript(self, page):
        """Extract flight data from JavaScript variables"""
        flight_data = []
        
        try:
            # Try to extract data from React component state or window variables
            js_result = await page.evaluate("""
                () => {
                    // Try to find flight data in various places
                    let flightData = [];
                    
                    // Check for React component data
                    const reactElements = document.querySelectorAll('[data-reactroot] *');
                    for (let element of reactElements) {
                        if (element._reactInternalFiber || element._reactInternalInstance) {
                            // Try to access React component state
                            try {
                                const fiber = element._reactInternalFiber || element._reactInternalInstance;
                                if (fiber && fiber.memoizedState) {
                                    // Look for flight data in state
                                    console.log('Found React state');
                                }
                            } catch (e) {
                                // Ignore errors
                            }
                        }
                    }
                    
                    // Check for data in window object
                    if (window.flightData) {
                        flightData = window.flightData;
                    }
                    
                    // Check for data in localStorage
                    try {
                        const stored = localStorage.getItem('flightData');
                        if (stored) {
                            flightData = JSON.parse(stored);
                        }
                    } catch (e) {
                        // Ignore errors
                    }
                    
                    return flightData;
                }
            """)
            
            if js_result and len(js_result) > 0:
                for flight in js_result:
                    flight_data.append({
                        'source': 'JavaScript',
                        'timestamp': datetime.now().isoformat(),
                        **flight
                    })
            
        except Exception as e:
            print(f"⚠️ Error extracting from JavaScript: {str(e)}")
        
        return flight_data
    
    async def save_data(self, flight_data, format='json'):
        """Save scraped data to file"""
        if not flight_data:
            print("⚠️ No data to save")
            return
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if format.lower() == 'json':
            filename = f"flight_prices_{timestamp}.json"
            filepath = Path(__file__).parent / filename
            
            with open(filepath, 'w') as f:
                json.dump({
                    'scraping_session': self.session_id,
                    'timestamp': datetime.now().isoformat(),
                    'total_flights': len(flight_data),
                    'flights': flight_data
                }, f, indent=2)
            
            print(f"💾 Saved {len(flight_data)} flight records to {filename}")
        
        elif format.lower() == 'csv':
            filename = f"flight_prices_{timestamp}.csv"
            filepath = Path(__file__).parent / filename
            
            if flight_data:
                fieldnames = flight_data[0].keys()
                with open(filepath, 'w', newline='') as f:
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writeheader()
                    writer.writerows(flight_data)
                
                print(f"💾 Saved {len(flight_data)} flight records to {filename}")
    
    async def analyze_pricing(self, flight_data):
        """Analyze pricing patterns"""
        if not flight_data:
            return
        
        print("\n" + "="*50)
        print("📊 PRICING ANALYSIS")
        print("="*50)
        
        # Group by source
        sources = {}
        for flight in flight_data:
            source = flight.get('source', 'Unknown')
            if source not in sources:
                sources[source] = []
            sources[source].append(flight)
        
        for source, flights in sources.items():
            print(f"\n📈 {source} Data ({len(flights)} flights):")
            
            prices = [f.get('price', 0) for f in flights if f.get('price')]
            if prices:
                avg_price = sum(prices) / len(prices)
                min_price = min(prices)
                max_price = max(prices)
                
                print(f"   💰 Average Price: ${avg_price:.2f}")
                print(f"   📉 Minimum Price: ${min_price}")
                print(f"   📈 Maximum Price: ${max_price}")
                
                # Check for bot detection
                bot_detected = any(f.get('is_bot_detected') for f in flights)
                if bot_detected:
                    print(f"   🤖 Bot Detection: DETECTED")
                    pricing_strategy = flights[0].get('pricing_strategy', 'unknown')
                    print(f"   💡 Pricing Strategy: {pricing_strategy}")
                else:
                    print(f"   👤 Bot Detection: NOT DETECTED")
        
        # Route analysis
        routes = {}
        for flight in flight_data:
            route = flight.get('route', 'Unknown')
            price = flight.get('price', 0)
            if route not in routes:
                routes[route] = []
            routes[route].append(price)
        
        print(f"\n🛫 Route Analysis:")
        for route, prices in routes.items():
            if prices:
                avg_price = sum(prices) / len(prices)
                print(f"   {route}: ${avg_price:.2f} avg")

async def main():
    # Load environment variables from .env file
    env_path = Path(__file__).parent / '.env'
    load_dotenv(dotenv_path=env_path)
    
    # Parse command line arguments with environment variable defaults
    parser = argparse.ArgumentParser(description='Flight price scraping bot using Playwright')
    parser.add_argument('--url', 
                       default=os.getenv('URL', 'https://d3mx9cjq6wwawz.cloudfront.net'),
                       help='Base URL for the website (default from .env)')
    parser.add_argument('--headless', 
                       type=str_to_bool,
                       default=str_to_bool(os.getenv('HEADLESS', 'true')),
                       help='Run in headless mode (default from .env or true)')
    parser.add_argument('--iterations', 
                       type=int, 
                       default=int(os.getenv('ITERATIONS', '3')),
                       help='Number of scraping iterations (default from .env or 3)')
    parser.add_argument('--delay',
                       type=float,
                       default=float(os.getenv('DELAY', '2')),
                       help='Delay between actions in seconds (default from .env or 2)')
    parser.add_argument('--timeout',
                       type=int,
                       default=int(os.getenv('TIMEOUT', '30')),
                       help='Browser timeout in seconds (default from .env or 30)')
    parser.add_argument('--output-format',
                       choices=['json', 'csv', 'both'],
                       default='json',
                       help='Output format for scraped data (default: json)')
    parser.add_argument('--user-agent',
                       default='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                       help='Custom User-Agent string')
    
    args = parser.parse_args()
    
    # Construct the pricing-demo-3 URL
    target_url = f"{args.url.rstrip('/')}/pricing-demo-3"
    
    print(f"🤖 Starting flight price scraping bot...")
    print(f"📍 Target URL: {target_url}")
    print(f"🔄 Scraping iterations: {args.iterations}")
    print(f"⏱️  Delay between actions: {args.delay}s")
    print(f"👁️  Headless mode: {args.headless}")
    print(f"📊 Output format: {args.output_format}")
    print(f"🕷️ User-Agent: {args.user_agent[:50]}...")
    print("-" * 60)
    
    scraper = FlightPriceScraper(args.url, args.headless, args.delay)
    all_flight_data = []
    
    async with async_playwright() as p:
        # Launch browser with bot-like characteristics
        browser = await p.chromium.launch(
            headless=args.headless,
            args=[
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-blink-features=AutomationControlled',
                '--disable-extensions',
                '--disable-plugins',
                '--disable-images',  # Faster loading
                '--disable-javascript-harmony-shipping',
                '--disable-background-timer-throttling',
                '--disable-renderer-backgrounding',
                '--disable-backgrounding-occluded-windows',
                '--disable-features=TranslateUI',
                '--disable-ipc-flooding-protection'
            ]
        )
        
        try:
            # Create browser context with scraper characteristics
            context = await browser.new_context(
                user_agent=args.user_agent,
                viewport={'width': 1920, 'height': 1080},
                extra_http_headers={
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.5',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'DNT': '1',
                    'Connection': 'keep-alive',
                    'Upgrade-Insecure-Requests': '1',
                }
            )
            
            # Set default timeout
            context.set_default_timeout(args.timeout * 1000)
            
            page = await context.new_page()
            
            # Perform multiple scraping iterations
            for iteration in range(args.iterations):
                print(f"\n🔄 Scraping Iteration {iteration + 1}/{args.iterations}")
                print("-" * 40)
                
                try:
                    # Navigate to the target page
                    print(f"🌐 Navigating to {target_url}...")
                    await page.goto(target_url, wait_until='networkidle')
                    
                    # Wait for page to load completely
                    await asyncio.sleep(args.delay * 2)
                    
                    # Verify we're on the correct page
                    page_title = await page.title()
                    print(f"📄 Page loaded: {page_title}")
                    
                    # Look for any content that indicates the page loaded
                    page_content = await page.content()
                    if 'FlightBooker' in page_content or 'pricing-demo-3' in page_content or 'flight' in page_content.lower():
                        print("✅ Flight booking page detected")
                        
                        # Scrape flight pricing data
                        flight_data = await scraper.scrape_flight_prices(page)
                        
                        if flight_data:
                            all_flight_data.extend(flight_data)
                            print(f"✅ Scraped {len(flight_data)} flight records")
                        else:
                            print("⚠️ No flight data extracted")
                    else:
                        print("❌ Flight booking page not detected")
                        print(f"Page content preview: {page_content[:200]}...")
                    
                    # Wait between iterations
                    if iteration < args.iterations - 1:
                        print(f"⏳ Waiting {args.delay}s before next iteration...")
                        await asyncio.sleep(args.delay)
                
                except Exception as e:
                    print(f"❌ Error in iteration {iteration + 1}: {str(e)}")
                    continue
            
            # Analyze and save results
            print("\n" + "="*60)
            print("🏁 Scraping completed!")
            print(f"📊 Total flight records collected: {len(all_flight_data)}")
            
            if all_flight_data:
                # Analyze pricing patterns
                await scraper.analyze_pricing(all_flight_data)
                
                # Save data
                if args.output_format in ['json', 'both']:
                    await scraper.save_data(all_flight_data, 'json')
                if args.output_format in ['csv', 'both']:
                    await scraper.save_data(all_flight_data, 'csv')
            else:
                print("⚠️ No data collected to analyze or save")
            
            print("="*60)
            
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
        print("\n🛑 Price scraping interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
        sys.exit(1)
