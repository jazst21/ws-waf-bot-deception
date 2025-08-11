#!/usr/bin/env python3
"""
Search Engine Bot Simulation using Playwright
Simulates how search engines like Google, Bing crawl websites
"""

import asyncio
import argparse
import sys
import os
import re
import urllib.parse
from pathlib import Path
from playwright.async_api import async_playwright
from dotenv import load_dotenv

class SearchEngineBot:
    def __init__(self, base_url, user_agent="Googlebot"):
        self.base_url = base_url.rstrip('/')
        self.visited_urls = set()
        self.found_links = set()
        self.robots_txt_rules = {}
        self.sitemap_urls = set()
        self.user_agent = user_agent
        
    async def simulate_crawl(self, browser):
        """Main crawling simulation"""
        page = await browser.new_page()
        
        # Set search engine user agent
        await page.set_extra_http_headers({
            'User-Agent': self.get_user_agent()
        })
        
        print(f"🤖 Starting crawl simulation as: {self.user_agent}")
        print(f"🎯 Target: {self.base_url}")
        print()
        
        # Step 1: Check robots.txt
        await self.check_robots_txt(page)
        
        # Step 2: Check sitemap
        await self.check_sitemap(page)
        
        # Step 3: Crawl main page and discover links
        await self.crawl_page(page, self.base_url)
        
        # Step 4: Crawl discovered links (limited depth)
        await self.crawl_discovered_links(page, max_pages=5)
        
        await page.close()
        
    async def check_robots_txt(self, page):
        """Check robots.txt file like search engines do"""
        robots_url = f"{self.base_url}/robots.txt"
        print(f"🔍 Checking robots.txt: {robots_url}")
        
        try:
            response = await page.goto(robots_url)
            if response.status == 200:
                content = await page.content()
                # Extract text content from HTML
                robots_text = await page.evaluate("document.body.textContent || document.body.innerText")
                print(f"✅ robots.txt found (Status: {response.status})")
                print("📋 robots.txt content:")
                print("-" * 40)
                print(robots_text[:500] + ("..." if len(robots_text) > 500 else ""))
                print("-" * 40)
                
                # Parse robots.txt rules
                self.parse_robots_txt(robots_text)
                
                # Look for sitemap references
                sitemap_matches = re.findall(r'Sitemap:\s*(.+)', robots_text, re.IGNORECASE)
                for sitemap_url in sitemap_matches:
                    self.sitemap_urls.add(sitemap_url.strip())
                    print(f"🗺️  Found sitemap reference: {sitemap_url.strip()}")
                    
            else:
                print(f"❌ robots.txt not found (Status: {response.status})")
                
        except Exception as e:
            print(f"❌ Error checking robots.txt: {e}")
        
        print()
    
    async def check_sitemap(self, page):
        """Check sitemap files"""
        # Check common sitemap locations
        common_sitemaps = [
            f"{self.base_url}/sitemap.xml",
            f"{self.base_url}/sitemap_index.xml",
            f"{self.base_url}/sitemaps.xml"
        ]
        
        # Add sitemaps found in robots.txt
        all_sitemaps = set(common_sitemaps) | self.sitemap_urls
        
        for sitemap_url in all_sitemaps:
            print(f"🗺️  Checking sitemap: {sitemap_url}")
            try:
                response = await page.goto(sitemap_url)
                if response.status == 200:
                    content = await page.content()
                    print(f"✅ Sitemap found (Status: {response.status})")
                    
                    # Extract URLs from sitemap (basic parsing)
                    url_matches = re.findall(r'<loc>(.*?)</loc>', content)
                    print(f"📄 Found {len(url_matches)} URLs in sitemap")
                    for url in url_matches[:5]:  # Show first 5
                        print(f"   - {url}")
                    if len(url_matches) > 5:
                        print(f"   ... and {len(url_matches) - 5} more")
                        
                else:
                    print(f"❌ Sitemap not found (Status: {response.status})")
                    
            except Exception as e:
                print(f"❌ Error checking sitemap: {e}")
        
        print()
    
    async def crawl_page(self, page, url):
        """Crawl a single page and extract information"""
        if url in self.visited_urls:
            return
            
        print(f"🕷️  Crawling: {url}")
        self.visited_urls.add(url)
        
        try:
            response = await page.goto(url, wait_until='networkidle')
            print(f"   Status: {response.status}")
            
            if response.status == 200:
                # Extract page title
                title = await page.title()
                print(f"   Title: {title}")
                
                # Extract meta description
                meta_desc = await page.get_attribute('meta[name="description"]', 'content')
                if meta_desc:
                    print(f"   Meta Description: {meta_desc[:100]}...")
                
                # Extract all links
                links = await page.evaluate("""
                    Array.from(document.querySelectorAll('a[href]')).map(a => a.href)
                """)
                
                # Filter and collect internal links
                internal_links = []
                for link in links:
                    if link.startswith(self.base_url):
                        internal_links.append(link)
                        self.found_links.add(link)
                
                print(f"   Found {len(internal_links)} internal links")
                
                # Check for common SEO elements
                await self.check_seo_elements(page)
                
        except Exception as e:
            print(f"   ❌ Error crawling page: {e}")
        
        print()
    
    async def check_seo_elements(self, page):
        """Check for common SEO elements that search engines look for"""
        # Check for structured data
        structured_data = await page.evaluate("""
            Array.from(document.querySelectorAll('script[type="application/ld+json"]')).length
        """)
        if structured_data > 0:
            print(f"   📊 Found {structured_data} structured data blocks")
        
        # Check for Open Graph tags
        og_tags = await page.evaluate("""
            Array.from(document.querySelectorAll('meta[property^="og:"]')).length
        """)
        if og_tags > 0:
            print(f"   📱 Found {og_tags} Open Graph tags")
        
        # Check for canonical URL
        canonical = await page.get_attribute('link[rel="canonical"]', 'href')
        if canonical:
            print(f"   🔗 Canonical URL: {canonical}")
    
    async def crawl_discovered_links(self, page, max_pages=5):
        """Crawl discovered links up to a maximum number"""
        print(f"🔍 Crawling discovered links (max {max_pages})...")
        
        crawled_count = 0
        for link in list(self.found_links):
            if crawled_count >= max_pages:
                break
            if link not in self.visited_urls:
                await self.crawl_page(page, link)
                crawled_count += 1
                await asyncio.sleep(1)  # Polite crawling delay
    
    def parse_robots_txt(self, content):
        """Basic robots.txt parsing"""
        lines = content.split('\n')
        current_user_agent = None
        
        for line in lines:
            line = line.strip()
            if line.startswith('User-agent:'):
                current_user_agent = line.split(':', 1)[1].strip()
            elif line.startswith('Disallow:') and current_user_agent:
                disallow_path = line.split(':', 1)[1].strip()
                if current_user_agent not in self.robots_txt_rules:
                    self.robots_txt_rules[current_user_agent] = {'disallow': []}
                self.robots_txt_rules[current_user_agent]['disallow'].append(disallow_path)
    
    def get_user_agent(self):
        """Get user agent string for different search engines"""
        user_agents = {
            'Googlebot': 'Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)',
            'Bingbot': 'Mozilla/5.0 (compatible; bingbot/2.0; +http://www.bing.com/bingbot.htm)',
            'YandexBot': 'Mozilla/5.0 (compatible; YandexBot/3.0; +http://yandex.com/bots)',
            'DuckDuckBot': 'DuckDuckBot/1.0; (+http://duckduckgo.com/duckduckbot.html)',
            'Baiduspider': 'Mozilla/5.0 (compatible; Baiduspider/2.0; +http://www.baidu.com/search/spider.html)'
        }
        return user_agents.get(self.user_agent, user_agents['Googlebot'])

async def main():
    # Load environment variables
    env_path = Path(__file__).parent / '.env'
    load_dotenv(dotenv_path=env_path)
    
    parser = argparse.ArgumentParser(description='Search Engine Bot Simulation')
    parser.add_argument('--url', 
                       default=os.getenv('URL', 'https://d2gy6opttm3z3x.cloudfront.net'),
                       help='URL to crawl')
    parser.add_argument('--bot', 
                       choices=['Googlebot', 'Bingbot', 'YandexBot', 'DuckDuckBot', 'Baiduspider'],
                       default='Googlebot',
                       help='Search engine bot to simulate')
    parser.add_argument('--headless', 
                       type=lambda x: x.lower() == 'true',
                       default=True,
                       help='Run in headless mode')
    
    args = parser.parse_args()
    
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=args.headless)
            
            bot = SearchEngineBot(args.url, args.bot)
            await bot.simulate_crawl(browser)
            
            await browser.close()
            
            # Summary
            print("=" * 50)
            print("🏁 CRAWL SUMMARY")
            print("=" * 50)
            print(f"Bot: {args.bot}")
            print(f"Pages crawled: {len(bot.visited_urls)}")
            print(f"Links discovered: {len(bot.found_links)}")
            print(f"Robots.txt rules: {len(bot.robots_txt_rules)}")
            print(f"Sitemaps found: {len(bot.sitemap_urls)}")
            
    except Exception as error:
        print(f'Error running bot simulation: {error}', file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    asyncio.run(main())
