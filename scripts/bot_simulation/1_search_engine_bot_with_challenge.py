#!/usr/bin/env python3
"""
Search Engine Bot Simulation with WAF Challenge Handling - Fixed Version
"""

import asyncio
import os
import re
from pathlib import Path
from urllib.parse import urljoin, urlparse
from playwright.async_api import async_playwright
from dotenv import load_dotenv

class SearchEngineBotSimulator:
    def __init__(self, base_url, user_agent="Googlebot/2.1 (+http://www.google.com/bot.html)"):
        self.base_url = base_url.rstrip('/')
        self.user_agent = user_agent
        self.visited_urls = set()
        self.found_links = set()
        self.robots_rules = []
        self.sitemaps = []
        
    async def run_simulation(self):
        """Run the complete bot simulation"""
        print(f"🤖 Starting crawl simulation as: {self.user_agent}")
        print(f"🎯 Target: {self.base_url}")
        print()
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                user_agent=self.user_agent,
                viewport={'width': 1920, 'height': 1080}
            )
            
            page = await context.new_page()
            
            # Set shorter timeouts
            page.set_default_timeout(10000)  # 10 seconds instead of 30
            
            try:
                # Step 1: Check robots.txt
                await self.check_robots_txt(page)
                
                # Step 2: Check sitemaps
                await self.check_sitemaps(page)
                
                # Step 3: Crawl main page
                await self.crawl_page(page, self.base_url)
                
                # Step 4: Crawl discovered links (all of them)
                print(f"🔍 Crawling discovered links ({len(self.found_links)} found)...")
                links_to_crawl = list(self.found_links)
                for link in links_to_crawl:
                    await self.crawl_page(page, link)
                
                # Step 5: Test private paths
                print("🔒 Testing private paths...")
                private_paths = ['/private', '/private/']
                for path in private_paths:
                    private_url = f"{self.base_url}{path}"
                    await self.crawl_page(page, private_url)
                
                # Step 5: Print summary
                self.print_summary()
                
            finally:
                await browser.close()
    
    async def check_robots_txt(self, page):
        """Check robots.txt file"""
        robots_url = f"{self.base_url}/robots.txt"
        print(f"🔍 Checking robots.txt: {robots_url}")
        
        try:
            response = await page.goto(robots_url, wait_until='domcontentloaded')
            
            if response.status == 202:
                print("🔄 Handling WAF challenge for robots.txt...")
                try:
                    await page.wait_for_load_state('domcontentloaded', timeout=10000)
                    await page.wait_for_timeout(2000)
                except:
                    pass
            
            if response.status in [200, 202]:
                print(f"✅ robots.txt found (Status: {response.status})")
                content = await page.content()
                
                # Extract robots.txt content from page
                robots_content = await page.evaluate("""
                    document.body ? document.body.innerText : document.documentElement.innerText
                """)
                
                if robots_content and len(robots_content) < 5000:  # Reasonable size for robots.txt
                    print("📋 robots.txt content:")
                    print("----------------------------------------")
                    print(robots_content[:1000] + ("..." if len(robots_content) > 1000 else ""))
                    print("----------------------------------------")
                    
                    # Parse robots.txt rules
                    self.parse_robots_txt(robots_content)
                    
                    # Look for sitemap references
                    sitemap_matches = re.findall(r'Sitemap:\s*(.+)', robots_content, re.IGNORECASE)
                    for sitemap in sitemap_matches:
                        sitemap = sitemap.strip()
                        print(f"🗺️  Found sitemap reference: {sitemap}")
                        self.sitemaps.append(sitemap)
                        
            else:
                print(f"❌ robots.txt not found (Status: {response.status})")
                
        except Exception as e:
            print(f"❌ Error checking robots.txt: {e}")
        
        print()
    
    def parse_robots_txt(self, content):
        """Parse robots.txt content for rules"""
        lines = content.split('\n')
        current_user_agent = None
        
        for line in lines:
            line = line.strip()
            if line.startswith('User-agent:'):
                current_user_agent = line.split(':', 1)[1].strip()
            elif line.startswith('Disallow:') or line.startswith('Allow:'):
                rule_type = line.split(':', 1)[0]
                path = line.split(':', 1)[1].strip()
                self.robots_rules.append({
                    'user_agent': current_user_agent,
                    'rule': rule_type,
                    'path': path
                })
    
    async def check_sitemaps(self, page):
        """Check sitemap files"""
        # Add common sitemap locations
        common_sitemaps = [
            f"{self.base_url}/sitemap.xml",
            f"{self.base_url}/sitemaps.xml", 
            f"{self.base_url}/sitemap_index.xml"
        ]
        
        all_sitemaps = list(set(self.sitemaps + common_sitemaps))
        
        for sitemap_url in all_sitemaps:
            print(f"🗺️  Checking sitemap: {sitemap_url}")
            
            try:
                response = await page.goto(sitemap_url, wait_until='domcontentloaded')
                
                if response.status == 202:
                    print(f"🔄 Handling WAF challenge for {sitemap_url}...")
                    try:
                        await page.wait_for_load_state('domcontentloaded', timeout=10000)
                        await page.wait_for_timeout(2000)
                    except:
                        pass
                
                if response.status in [200, 202]:
                    print(f"✅ Sitemap found (Status: {response.status})")
                    
                    # Get sitemap content
                    content = await page.evaluate("""
                        document.body ? document.body.innerText : document.documentElement.innerText
                    """)
                    
                    # Extract URLs from sitemap
                    url_matches = re.findall(r'<loc>(.*?)</loc>', content, re.IGNORECASE)
                    if not url_matches:
                        # Try alternative format
                        url_matches = re.findall(r'https?://[^\s<>"]+', content)
                        url_matches = [url for url in url_matches if self.base_url in url]
                    
                    print(f"📄 Found {len(url_matches)} URLs in sitemap")
                    for url in url_matches[:5]:  # Show first 5
                        print(f"   - {url}")
                        self.found_links.add(url)
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
            response = await page.goto(url, wait_until='domcontentloaded')
            print(f"   Status: {response.status}")
            
            # Handle WAF challenge (202) and success (200) responses
            if response.status in [200, 202]:
                # Wait for any challenges to complete
                if response.status == 202:
                    print(f"   🔄 Handling WAF challenge...")
                    try:
                        await page.wait_for_load_state('domcontentloaded', timeout=10000)
                        await page.wait_for_timeout(2000)
                    except:
                        pass
                
                # Wait for page to be ready
                try:
                    await page.wait_for_load_state('domcontentloaded', timeout=5000)
                except:
                    pass
                
                # Extract page title
                try:
                    title = await page.title()
                    print(f"   Title: {title}")
                except:
                    print("   Title: Unable to extract")
                
                # Extract meta description
                try:
                    meta_desc = await page.get_attribute('meta[name="description"]', 'content')
                    if meta_desc:
                        print(f"   Meta Description: {meta_desc[:100]}...")
                except:
                    pass
                
                # Extract all links (with timeout)
                try:
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
                except Exception as e:
                    print(f"   Could not extract links: {e}")
                
        except Exception as e:
            print(f"   ❌ Error crawling page: {e}")
        
        print()
    
    def print_summary(self):
        """Print crawl summary"""
        print("=" * 50)
        print("🏁 CRAWL SUMMARY")
        print("=" * 50)
        print(f"Bot: {self.user_agent.split('/')[0]}")
        print(f"Pages crawled: {len(self.visited_urls)}")
        print(f"Links discovered: {len(self.found_links)}")
        print(f"Robots.txt rules: {len(self.robots_rules)}")
        print(f"Sitemaps found: {len([s for s in self.sitemaps if s])}")

async def main():
    # Load environment variables
    env_path = Path(__file__).parent / '.env'
    load_dotenv(dotenv_path=env_path)
    
    # Configuration
    BASE_URL = os.getenv('TARGET_URL', 'https://d2d7z9s673hmv1.cloudfront.net')
    USER_AGENT = "Googlebot/2.1 (+http://www.google.com/bot.html)"
    
    # Run simulation
    simulator = SearchEngineBotSimulator(BASE_URL, USER_AGENT)
    await simulator.run_simulation()

if __name__ == "__main__":
    asyncio.run(main())
