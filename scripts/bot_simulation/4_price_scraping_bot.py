#!/usr/bin/env python3
"""
Simplified price scraping bot for pricing-demo-3 flight booking page
Focuses on API interception for reliable data extraction
"""

import asyncio
import argparse
import sys
import os
import json
import time
from pathlib import Path
from datetime import datetime
from playwright.async_api import async_playwright
from dotenv import load_dotenv

def print_table(data, title="Scraped Flight Data"):
    """Print data in a formatted CLI table"""
    if not data:
        print("📊 No data to display")
        return
    
    print(f"\n📊 {title}")
    print("=" * 120)
    
    # Table headers
    headers = ["Route", "Airline", "Departure", "Arrival", "Duration", "Price", "Discount"]
    col_widths = [25, 18, 12, 12, 10, 8, 8]
    
    # Print header
    header_row = "│"
    for i, header in enumerate(headers):
        header_row += f" {header:<{col_widths[i]}} │"
    print(header_row)
    
    # Print separator
    separator = "├"
    for width in col_widths:
        separator += "─" * (width + 2) + "┼"
    separator = separator[:-1] + "┤"
    print(separator)
    
    # Print data rows
    for flight in data:
        route = flight.get('route', 'Unknown')[:24]
        airline = flight.get('airline', 'Unknown')[:17]
        departure = flight.get('departure', 'Unknown')[:11]
        arrival = flight.get('arrival', 'Unknown')[:11]
        duration = flight.get('duration', 'Unknown')[:9]
        price = f"${flight.get('price', 0)}"
        discount = f"{flight.get('discount', 0)}%" if flight.get('discount', 0) > 0 else "None"
        
        row = f"│ {route:<{col_widths[0]}} │ {airline:<{col_widths[1]}} │ {departure:<{col_widths[2]}} │ {arrival:<{col_widths[3]}} │ {duration:<{col_widths[4]}} │ {price:<{col_widths[5]}} │ {discount:<{col_widths[6]}} │"
        print(row)
    
    # Print bottom border
    bottom = "└"
    for width in col_widths:
        bottom += "─" * (width + 2) + "┴"
    bottom = bottom[:-1] + "┘"
    print(bottom)

def print_summary_table(all_flight_data):
    """Print summary statistics in table format"""
    if not all_flight_data:
        return
    
    print(f"\n📈 Scraping Summary")
    print("=" * 60)
    
    # Calculate statistics
    total_flights = len(all_flight_data)
    unique_routes = len(set(f.get('route', 'Unknown') for f in all_flight_data))
    avg_price = sum(f.get('price', 0) for f in all_flight_data) / total_flights if total_flights > 0 else 0
    min_price = min(f.get('price', 0) for f in all_flight_data) if all_flight_data else 0
    max_price = max(f.get('price', 0) for f in all_flight_data) if all_flight_data else 0
    
    # Summary data (removed bot-related fields)
    summary_data = [
        ["Total Flights Scraped", str(total_flights)],
        ["Unique Routes", str(unique_routes)],
        ["Average Price", f"${avg_price:.2f}"],
        ["Price Range", f"${min_price} - ${max_price}"],
        ["Data Sources", "API Response Interception"],
        ["Success Rate", "100%" if total_flights > 0 else "0%"],
        ["Scraping Method", "Network Traffic Analysis"],
        ["Response Format", "JSON API Data"]
    ]
    
    # Print summary table
    print("┌─────────────────────────┬──────────────────────────────┐")
    print("│ Metric                  │ Value                        │")
    print("├─────────────────────────┼──────────────────────────────┤")
    
    for metric, value in summary_data:
        print(f"│ {metric:<23} │ {value:<28} │")
    
    print("└─────────────────────────┴──────────────────────────────┘")

def print_route_analysis(all_flight_data):
    """Print route-by-route price analysis"""
    if not all_flight_data:
        return
    
    # Group by route
    routes = {}
    for flight in all_flight_data:
        route = flight.get('route', 'Unknown')
        price = flight.get('price', 0)
        if route not in routes:
            routes[route] = []
        routes[route].append(price)
    
    print(f"\n🛫 Route Price Analysis")
    print("=" * 80)
    print("┌─────────────────────────────┬──────────────┬──────────────┐")
    print("│ Route                       │ Avg Price    │ Occurrences  │")
    print("├─────────────────────────────┼──────────────┼──────────────┤")
    
    for route, prices in sorted(routes.items()):
        avg_price = sum(prices) / len(prices)
        occurrences = len(prices)
        route_display = route[:27] if len(route) <= 27 else route[:24] + "..."
        print(f"│ {route_display:<27} │ ${avg_price:>10.2f} │ {occurrences:>10}x │")
    
    print("└─────────────────────────────┴──────────────┴──────────────┘")

async def scrape_flight_api(page, base_url, delay=2):
    """Scrape flight data by intercepting API responses"""
    flight_data = []
    responses_captured = []
    
    def handle_response(response):
        if '/api/pricing-demo-3/flights' in response.url:
            responses_captured.append(response)
            print(f"📡 Captured API response: {response.url} (Status: {response.status})")
    
    # Set up response interception
    page.on('response', handle_response)
    
    try:
        # Navigate to the page
        target_url = f"{base_url.rstrip('/')}/pricing-demo-3"
        print(f"🌐 Navigating to {target_url}...")
        await page.goto(target_url, wait_until='domcontentloaded')
        
        # Wait for initial load
        await asyncio.sleep(delay * 2)
        
        # Try to trigger API calls by looking for and clicking refresh button
        try:
            refresh_button = page.locator('button:has-text("Refresh")')
            if await refresh_button.count() > 0:
                print("🔄 Clicking refresh button to trigger API call...")
                await refresh_button.click()
                await asyncio.sleep(delay * 2)
        except Exception as e:
            print(f"⚠️ Could not click refresh button: {str(e)}")
        
        # Also try to make direct API call
        try:
            print("🔗 Making direct API call...")
            api_url = f"{base_url.rstrip('/')}/api/pricing-demo-3/flights"
            api_response = await page.request.get(api_url)
            if api_response.status == 200:
                responses_captured.append(api_response)
                print(f"✅ Direct API call successful: {api_response.status}")
        except Exception as e:
            print(f"⚠️ Direct API call failed: {str(e)}")
        
        # Process captured responses
        for response in responses_captured:
            try:
                if response.status == 200:
                    json_data = await response.json()
                    if 'flights' in json_data:
                        print(f"✅ Found {len(json_data['flights'])} flights in API response")
                        for flight in json_data['flights']:
                            flight_data.append({
                                'timestamp': datetime.now().isoformat(),
                                'route': flight.get('route', 'Unknown'),
                                'airline': flight.get('airline', 'Unknown'),
                                'departure': flight.get('departure', 'Unknown'),
                                'arrival': flight.get('arrival', 'Unknown'),
                                'duration': flight.get('duration', 'Unknown'),
                                'price': flight.get('price', 0),
                                'original_price': flight.get('originalPrice', 0),
                                'discount': flight.get('discount', 0),
                                'api_message': json_data.get('message', '')
                            })
            except Exception as e:
                print(f"⚠️ Error processing API response: {str(e)}")
    
    except Exception as e:
        print(f"❌ Error during API scraping: {str(e)}")
    
    return flight_data

async def main():
    # Load environment variables
    env_path = Path(__file__).parent / '.env'
    load_dotenv(dotenv_path=env_path)
    
    # Parse arguments
    parser = argparse.ArgumentParser(description='Simple flight price scraping bot')
    parser.add_argument('--url', default=os.getenv('URL', 'https://d3mx9cjq6wwawz.cloudfront.net'))
    parser.add_argument('--headless', type=bool, default=True)
    parser.add_argument('--iterations', type=int, default=2)
    parser.add_argument('--delay', type=float, default=2.0)
    
    args = parser.parse_args()
    
    print(f"🤖 Starting simple flight price scraper...")
    print(f"📍 Target: {args.url}/pricing-demo-3")
    print(f"🔄 Iterations: {args.iterations}")
    print("-" * 50)
    
    all_flight_data = []
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=args.headless,
            args=['--no-sandbox', '--disable-setuid-sandbox']
        )
        
        try:
            context = await browser.new_context(
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            )
            
            page = await context.new_page()
            
            for i in range(args.iterations):
                print(f"\n🔄 Iteration {i + 1}/{args.iterations}")
                print("-" * 30)
                
                flight_data = await scrape_flight_api(page, args.url, args.delay)
                
                if flight_data:
                    all_flight_data.extend(flight_data)
                    print(f"✅ Collected {len(flight_data)} flight records")
                    
                    # Show sample data (without revealing bot detection architecture)
                    sample = flight_data[0]
                    print(f"📊 Sample: {sample['route']} - ${sample['price']}")
                else:
                    print("⚠️ No flight data collected")
                
                if i < args.iterations - 1:
                    await asyncio.sleep(args.delay)
            
            # Results summary
            print("\n" + "=" * 120)
            print("🏁 Flight Price Scraping Results")
            print("=" * 120)
            
            if all_flight_data:
                # Remove duplicates for display (keep unique flights)
                unique_flights = []
                seen_flights = set()
                for flight in all_flight_data:
                    flight_key = (flight.get('route'), flight.get('airline'), flight.get('price'))
                    if flight_key not in seen_flights:
                        unique_flights.append(flight)
                        seen_flights.add(flight_key)
                
                # Display flight data table
                print_table(unique_flights, f"Flight Data ({len(unique_flights)} unique flights)")
                
                # Display summary statistics
                print_summary_table(all_flight_data)
                
                # Display route analysis
                print_route_analysis(all_flight_data)
                
                # Save data
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"flight_prices_{timestamp}.json"
                
                with open(filename, 'w') as f:
                    json.dump({
                        'timestamp': datetime.now().isoformat(),
                        'total_flights': len(all_flight_data),
                        'unique_flights': len(unique_flights),
                        'flights': all_flight_data
                    }, f, indent=2)
                
                print(f"\n💾 Detailed data saved to: {filename}")
                print(f"📊 Scraped {len(all_flight_data)} total records ({len(unique_flights)} unique flights)")
            else:
                print("❌ No flight data collected")
                print("🔍 Possible issues:")
                print("   • WAF blocking requests")
                print("   • API endpoint changes")
                print("   • Network connectivity issues")
                print("   • Page structure modifications")
            
        finally:
            await browser.close()

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Scraping interrupted")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        sys.exit(1)
