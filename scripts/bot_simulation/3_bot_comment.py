#!/usr/bin/env python3
"""
Bot simulation script for submitting negative hotel reviews to bot-demo-2 page
Simulates malicious bot behavior with fake negative reviews and low ratings
Uses environment variables from .env file with command-line argument fallbacks
"""

import asyncio
import argparse
import sys
import os
import random
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

# Sample negative review data for bot simulation
# Bots typically leave fake negative reviews to damage reputation
SAMPLE_REVIEWS = [
    {
        "name": "John Smith",
        "rating": 1,
        "comment": "Terrible experience! Room was dirty and smelled bad. Staff was rude and unhelpful. Complete waste of money. Would never recommend this place to anyone."
    },
    {
        "name": "Sarah Johnson",
        "rating": 2,
        "comment": "Overpriced and disappointing. The pool was closed for maintenance without notice. Food was cold and tasteless. Very poor service overall."
    },
    {
        "name": "Mike Wilson",
        "rating": 1,
        "comment": "Worst hotel stay ever! Air conditioning broken, noisy neighbors all night, and front desk ignored our complaints. Ruined our vacation completely."
    },
    {
        "name": "Emily Davis",
        "rating": 2,
        "comment": "Not worth the money at all. Facilities are outdated and poorly maintained. WiFi didn't work and room service took 2 hours. Very disappointed."
    },
    {
        "name": "Robert Brown",
        "rating": 1,
        "comment": "Disgusting conditions! Bathroom had mold, bed sheets were stained, and elevator was broken. Management doesn't care about guests at all."
    },
    {
        "name": "Lisa Garcia",
        "rating": 2,
        "comment": "False advertising! Photos online look nothing like reality. Tiny rooms, broken amenities, and extremely loud construction noise during the day."
    },
    {
        "name": "David Martinez",
        "rating": 1,
        "comment": "Horrible customer service and dirty facilities. Found bugs in the room and staff refused to help. This place should be shut down immediately."
    },
    {
        "name": "Jennifer Lee",
        "rating": 2,
        "comment": "Total scam! Hidden fees everywhere and room was nothing like advertised. Spa was closed, restaurant had limited menu. Avoid at all costs."
    },
    {
        "name": "Thomas Anderson",
        "rating": 1,
        "comment": "Nightmare stay! No hot water, broken TV, and housekeeping never showed up. Staff was unprofessional and argumentative. Demanded refund."
    },
    {
        "name": "Amanda White",
        "rating": 2,
        "comment": "Extremely disappointing for the price. Parking was full, check-in took forever, and room had no view despite booking ocean view. Poor management."
    },
    {
        "name": "Mark Johnson",
        "rating": 1,
        "comment": "Absolutely awful! Bed was uncomfortable, room was freezing cold, and noise from street kept us awake all night. Staff couldn't care less."
    },
    {
        "name": "Jessica Brown",
        "rating": 2,
        "comment": "Overrated and overpriced. Breakfast was terrible, gym equipment broken, and pool area was dirty. Would not stay here again."
    },
    {
        "name": "Kevin Davis",
        "rating": 1,
        "comment": "Worst vacation ever! Room key didn't work, no towels provided, and front desk was always empty. This place is a complete joke."
    },
    {
        "name": "Rachel Wilson",
        "rating": 2,
        "comment": "Very poor experience. Internet was down entire stay, room service was cold, and checkout process was a nightmare. Not recommended."
    },
    {
        "name": "Steve Miller",
        "rating": 1,
        "comment": "Terrible hotel with zero customer service. Complained about noise and nothing was done. Room was dirty and smelled like smoke. Avoid!"
    }
]

async def submit_review(page, review_data, delay=1):
    """Submit a single hotel review"""
    try:
        print(f"Submitting review by {review_data['name']} with {review_data['rating']} stars...")
        
        # Fill in the name field
        name_input = page.locator('input[placeholder="Enter your name"]')
        await name_input.fill(review_data['name'])
        await asyncio.sleep(delay * 0.5)
        
        # Click on the rating stars
        rating = review_data['rating']
        star_buttons = page.locator('button[type="button"]').filter(has_text="★")
        await star_buttons.nth(rating - 1).click()
        await asyncio.sleep(delay * 0.5)
        
        # Fill in the comment/review text
        comment_textarea = page.locator('textarea[placeholder*="Tell us about your stay"]')
        await comment_textarea.fill(review_data['comment'])
        await asyncio.sleep(delay * 0.5)
        
        # Submit the form
        submit_button = page.locator('button[type="submit"]', has_text="Submit Review")
        await submit_button.click()
        
        # Wait for submission to complete
        await asyncio.sleep(delay * 2)
        
        print(f"✓ Review submitted successfully by {review_data['name']}")
        return True
        
    except Exception as e:
        print(f"✗ Failed to submit review by {review_data['name']}: {str(e)}")
        return False

async def main():
    # Load environment variables from .env file
    env_path = Path(__file__).parent / '.env'
    load_dotenv(dotenv_path=env_path)
    
    # Parse command line arguments with environment variable defaults
    parser = argparse.ArgumentParser(description='Malicious hotel review bot simulation using Playwright')
    parser.add_argument('--url', 
                       default=os.getenv('URL', 'https://d3mx9cjq6wwawz.cloudfront.net'),
                       help='Base URL for the website (default from .env)')
    parser.add_argument('--headless', 
                       type=str_to_bool,
                       default=str_to_bool(os.getenv('HEADLESS', 'false')),
                       help='Run in headless mode (default from .env or false)')
    parser.add_argument('--iterations', 
                       type=int, 
                       default=int(os.getenv('ITERATIONS', '5')),
                       help='Number of reviews to submit (default from .env or 5)')
    parser.add_argument('--delay',
                       type=float,
                       default=float(os.getenv('DELAY', '2')),
                       help='Delay between actions in seconds (default from .env or 2)')
    parser.add_argument('--timeout',
                       type=int,
                       default=int(os.getenv('TIMEOUT', '30')),
                       help='Browser timeout in seconds (default from .env or 30)')
    parser.add_argument('--random-reviews',
                       action='store_true',
                       help='Use random reviews from sample data (default: sequential)')
    
    args = parser.parse_args()
    
    # Construct the bot-demo-2 URL
    bot_demo_url = f"{args.url.rstrip('/')}/bot-demo-2"
    
    print(f"🤖 Starting malicious hotel review bot simulation...")
    print(f"📍 Target URL: {bot_demo_url}")
    print(f"🔄 Negative reviews to submit: {args.iterations}")
    print(f"⏱️  Delay between actions: {args.delay}s")
    print(f"👁️  Headless mode: {args.headless}")
    print(f"🎲 Random reviews: {args.random_reviews}")
    print(f"⭐ All reviews will be 1-2 stars with negative content")
    print("-" * 50)
    
    async with async_playwright() as p:
        # Launch browser
        browser = await p.chromium.launch(
            headless=args.headless,
            args=['--no-sandbox', '--disable-setuid-sandbox']
        )
        
        try:
            # Create browser context with realistic user agent
            context = await browser.new_context(
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                viewport={'width': 1920, 'height': 1080}
            )
            
            # Set default timeout
            context.set_default_timeout(args.timeout * 1000)
            
            page = await context.new_page()
            
            # Navigate to the bot-demo-2 page
            print(f"🌐 Navigating to {bot_demo_url}...")
            await page.goto(bot_demo_url)
            
            # Wait for the page to load completely
            await page.wait_for_load_state('networkidle')
            await asyncio.sleep(args.delay)
            
            # Verify we're on the correct page
            page_title = await page.title()
            print(f"📄 Page loaded: {page_title}")
            
            # Check if the review form is present
            form_present = await page.locator('form').count() > 0
            if not form_present:
                print("❌ Review form not found on the page!")
                return
            
            print("✅ Review form found, starting submissions...")
            print("-" * 50)
            
            successful_submissions = 0
            failed_submissions = 0
            
            # Submit reviews
            for i in range(args.iterations):
                print(f"\n📝 Submission {i + 1}/{args.iterations}")
                
                # Select review data
                if args.random_reviews:
                    review_data = random.choice(SAMPLE_REVIEWS)
                else:
                    review_data = SAMPLE_REVIEWS[i % len(SAMPLE_REVIEWS)]
                
                # Submit the review
                success = await submit_review(page, review_data, args.delay)
                
                if success:
                    successful_submissions += 1
                else:
                    failed_submissions += 1
                
                # Wait between submissions (except for the last one)
                if i < args.iterations - 1:
                    print(f"⏳ Waiting {args.delay}s before next submission...")
                    await asyncio.sleep(args.delay)
            
            # Final summary
            print("\n" + "=" * 50)
            print("🏁 Bot simulation completed!")
            print(f"✅ Successful submissions: {successful_submissions}")
            print(f"❌ Failed submissions: {failed_submissions}")
            print(f"📊 Success rate: {(successful_submissions / args.iterations * 100):.1f}%")
            print("=" * 50)
            
        except Exception as e:
            print(f"❌ Error during bot simulation: {str(e)}")
            return 1
        finally:
            await browser.close()
    
    return 0

if __name__ == '__main__':
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n🛑 Bot simulation interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
        sys.exit(1)
