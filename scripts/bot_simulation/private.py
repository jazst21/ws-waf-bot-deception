#!/usr/bin/env python3
"""
Private Content Scraper - Extract all text content from private index.html
Simple scraper to extract and display all text content from the private page
"""

import asyncio
import argparse
import sys
import os
import re
from pathlib import Path
from playwright.async_api import async_playwright
from dotenv import load_dotenv

def clean_text(text):
    """Clean and format extracted text"""
    # Remove extra whitespace and normalize line breaks
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'\n\s*\n', '\n\n', text)
    return text.strip()

class PrivateContentScraper:
    def __init__(self, user_agent, headless=True):
        self.user_agent = user_agent
        self.headless = headless
        
    async def scrape_private_content(self, url):
        """Scrape all text content from the private page"""
        print(f"🔍 Scraping content from: {url}")
        print(f"🤖 User Agent: {self.user_agent}")
        print("-" * 80)
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=self.headless,
                args=[
                    '--no-sandbox', 
                    '--disable-setuid-sandbox',
                    '--disable-web-security',
                    '--disable-features=VizDisplayCompositor'
                ]
            )
            
            try:
                context = await browser.new_context(
                    user_agent=self.user_agent,
                    viewport={'width': 1920, 'height': 1080}
                )
                
                page = await context.new_page()
                
                # Navigate to the page
                response = await page.goto(url, wait_until='networkidle', timeout=30000)
                print(f"📊 Response Status: {response.status}")
                
                # Wait for content to load
                await asyncio.sleep(2)
                
                # Extract page title
                title = await page.title()
                print(f"📄 Page Title: {title}")
                
                # Extract all text content
                text_content = await page.evaluate("""
                    () => {
                        // Remove script and style elements
                        const scripts = document.querySelectorAll('script, style');
                        scripts.forEach(el => el.remove());
                        
                        // Get the main text content
                        return document.body.innerText || document.body.textContent || '';
                    }
                """)
                
                # Clean the text
                cleaned_text = clean_text(text_content)
                
                # Extract structured content
                structured_content = await self.extract_structured_content(page)
                
                # Display results
                self.display_content(title, cleaned_text, structured_content, response.status)
                
                return {
                    'title': title,
                    'text_content': cleaned_text,
                    'structured_content': structured_content,
                    'status': response.status,
                    'url': url
                }
                
            except Exception as e:
                print(f"❌ Error scraping content: {e}")
                return None
            finally:
                await browser.close()
    
    async def extract_structured_content(self, page):
        """Extract structured content like headings, lists, etc."""
        structured = {}
        
        # Extract headings
        headings = await page.evaluate("""
            () => {
                const headings = [];
                for (let i = 1; i <= 6; i++) {
                    const elements = document.querySelectorAll(`h${i}`);
                    elements.forEach(el => {
                        const text = el.textContent.trim();
                        if (text) {
                            headings.push({
                                level: i,
                                text: text,
                                id: el.id || ''
                            });
                        }
                    });
                }
                return headings;
            }
        """)
        structured['headings'] = headings
        
        # Extract paragraphs
        paragraphs = await page.evaluate("""
            () => {
                const paras = Array.from(document.querySelectorAll('p'));
                return paras.map(p => p.textContent.trim()).filter(text => text.length > 0);
            }
        """)
        structured['paragraphs'] = paragraphs
        
        # Extract lists
        lists = await page.evaluate("""
            () => {
                const lists = [];
                const ulElements = document.querySelectorAll('ul, ol');
                ulElements.forEach(list => {
                    const items = Array.from(list.querySelectorAll('li')).map(li => li.textContent.trim());
                    if (items.length > 0) {
                        lists.push({
                            type: list.tagName.toLowerCase(),
                            items: items
                        });
                    }
                });
                return lists;
            }
        """)
        structured['lists'] = lists
        
        # Extract links
        links = await page.evaluate("""
            () => {
                const links = Array.from(document.querySelectorAll('a[href]'));
                return links.map(link => ({
                    text: link.textContent.trim(),
                    href: link.href,
                    title: link.title || ''
                })).filter(link => link.text.length > 0);
            }
        """)
        structured['links'] = links
        
        return structured
    
    def display_content(self, title, text_content, structured_content, status):
        """Display the scraped content in a formatted way"""
        print(f"\n{'='*80}")
        print(f"📋 SCRAPED CONTENT SUMMARY")
        print(f"{'='*80}")
        print(f"Status: {status}")
        print(f"Title: {title}")
        print(f"Content Length: {len(text_content)} characters")
        print(f"Headings: {len(structured_content.get('headings', []))}")
        print(f"Paragraphs: {len(structured_content.get('paragraphs', []))}")
        print(f"Lists: {len(structured_content.get('lists', []))}")
        print(f"Links: {len(structured_content.get('links', []))}")
        
        print(f"\n{'='*80}")
        print(f"📝 FULL TEXT CONTENT")
        print(f"{'='*80}")
        print(text_content)
        
        # Display structured content
        headings = structured_content.get('headings', [])
        if headings:
            print(f"\n{'='*80}")
            print(f"📑 HEADINGS STRUCTURE")
            print(f"{'='*80}")
            for heading in headings:
                indent = "  " * (heading['level'] - 1)
                print(f"{indent}H{heading['level']}: {heading['text']}")
        
        paragraphs = structured_content.get('paragraphs', [])
        if paragraphs:
            print(f"\n{'='*80}")
            print(f"📄 PARAGRAPHS ({len(paragraphs)} found)")
            print(f"{'='*80}")
            for i, para in enumerate(paragraphs[:5], 1):  # Show first 5 paragraphs
                print(f"{i}. {para[:200]}{'...' if len(para) > 200 else ''}")
            if len(paragraphs) > 5:
                print(f"... and {len(paragraphs) - 5} more paragraphs")
        
        lists = structured_content.get('lists', [])
        if lists:
            print(f"\n{'='*80}")
            print(f"📋 LISTS ({len(lists)} found)")
            print(f"{'='*80}")
            for i, list_item in enumerate(lists, 1):
                print(f"{i}. {list_item['type'].upper()} with {len(list_item['items'])} items:")
                for item in list_item['items'][:3]:  # Show first 3 items
                    print(f"   - {item}")
                if len(list_item['items']) > 3:
                    print(f"   ... and {len(list_item['items']) - 3} more items")
        
        links = structured_content.get('links', [])
        if links:
            print(f"\n{'='*80}")
            print(f"🔗 LINKS ({len(links)} found)")
            print(f"{'='*80}")
            for i, link in enumerate(links[:10], 1):  # Show first 10 links
                print(f"{i}. {link['text']} -> {link['href']}")
            if len(links) > 10:
                print(f"... and {len(links) - 10} more links")

async def main():
    """Main execution function"""
    # Load environment variables
    env_path = Path(__file__).parent / '.env'
    load_dotenv(dotenv_path=env_path)
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Scrape private content from bot demo page')
    parser.add_argument('--url', 
                       default='https://d3mx9cjq6wwawz.cloudfront.net/private/',
                       help='URL to scrape (default: private index.html)')
    parser.add_argument('--user-agent',
                       default='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
                       help='User agent string to use')
    parser.add_argument('--headless', 
                       action='store_true',
                       default=True,
                       help='Run in headless mode (default: True)')
    parser.add_argument('--visible', 
                       action='store_true',
                       help='Run in visible mode (overrides headless)')
    parser.add_argument('--bot-agent',
                       action='store_true',
                       help='Use a bot user agent (python-requests)')
    
    args = parser.parse_args()
    
    # Override headless if visible is requested
    if args.visible:
        args.headless = False
    
    # Use bot user agent if requested
    if args.bot_agent:
        args.user_agent = 'python-requests/2.25.1'
    
    print(f"🕷️  PRIVATE CONTENT SCRAPER")
    print(f"📍 Target URL: {args.url}")
    print(f"🤖 User Agent: {args.user_agent}")
    print(f"👁️  Headless: {args.headless}")
    
    # Create scraper and run
    scraper = PrivateContentScraper(args.user_agent, args.headless)
    result = await scraper.scrape_private_content(args.url)
    
    if result:
        print(f"\n✅ Scraping completed successfully!")
        
        # Optionally save to file
        output_file = Path(__file__).parent / 'scraped_private_content.txt'
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(f"Title: {result['title']}\n")
            f.write(f"URL: {result['url']}\n")
            f.write(f"Status: {result['status']}\n")
            f.write(f"Scraped at: {asyncio.get_event_loop().time()}\n")
            f.write(f"\n{'='*80}\n")
            f.write(f"FULL TEXT CONTENT\n")
            f.write(f"{'='*80}\n")
            f.write(result['text_content'])
        
        print(f"💾 Content saved to: {output_file}")
        return 0
    else:
        print(f"❌ Scraping failed!")
        return 1

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
