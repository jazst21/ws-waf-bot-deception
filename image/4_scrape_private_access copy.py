#!/usr/bin/env python3
"""
Advanced Bot Scraper - Bot Demo & Private Endpoint Explorer
Comprehensive bot that accesses the bot demo page, interacts with JavaScript elements,
and systematically explores private endpoints including private/index.html
"""

import asyncio
import argparse
import sys
import os
import re
import json
import time
from pathlib import Path
from urllib.parse import urljoin, urlparse, parse_qs
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError
from dotenv import load_dotenv
from tabulate import tabulate
from collections import defaultdict
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

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

class BotDemoScraper:
    def __init__(self, base_url, user_agent, delay=2, timeout=30):
        self.base_url = base_url.rstrip('/')
        self.user_agent = user_agent
        self.delay = delay
        self.timeout = timeout
        self.session_data = {}
        self.discovered_endpoints = set()
        self.scraping_results = {}
        self.javascript_interactions = []
        
    async def setup_page(self, page):
        """Configure page with stealth settings and monitoring"""
        # Set up request/response monitoring
        page.on('request', self._log_request)
        page.on('response', self._log_response)
        
        # Inject stealth JavaScript to avoid detection
        await page.add_init_script("""
            // Override webdriver detection
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined,
            });
            
            // Override plugins
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5],
            });
            
            // Override languages
            Object.defineProperty(navigator, 'languages', {
                get: () => ['en-US', 'en'],
            });
            
            // Override permissions
            const originalQuery = window.navigator.permissions.query;
            window.navigator.permissions.query = (parameters) => (
                parameters.name === 'notifications' ?
                    Promise.resolve({ state: Notification.permission }) :
                    originalQuery(parameters)
            );
        """)
        
    async def _log_request(self, request):
        """Log outgoing requests"""
        logger.debug(f"REQUEST: {request.method} {request.url}")
        
    async def _log_response(self, response):
        """Log incoming responses"""
        logger.debug(f"RESPONSE: {response.status} {response.url}")
        
    async def access_bot_demo_page(self, page):
        """Access and interact with the bot demo page"""
        demo_url = f"{self.base_url}/bot-demo-1"
        logger.info(f"🎯 Accessing bot demo page: {demo_url}")
        
        try:
            # Navigate to bot demo page
            response = await page.goto(demo_url, wait_until='networkidle', timeout=self.timeout * 1000)
            logger.info(f"✅ Bot demo page loaded with status: {response.status}")
            
            # Wait for page to fully load
            await asyncio.sleep(self.delay)
            
            # Analyze the page content
            analysis = await self._analyze_page_content(page, demo_url, "Bot Demo Page")
            self.scraping_results['bot_demo'] = analysis
            
            # Look for and interact with JavaScript buttons
            await self._interact_with_javascript_elements(page, demo_url)
            
            # Extract any hidden or dynamic content
            await self._extract_dynamic_content(page)
            
            return analysis
            
        except Exception as e:
            logger.error(f"❌ Failed to access bot demo page: {e}")
            return {'error': str(e), 'url': demo_url}
    
    async def _interact_with_javascript_elements(self, page, url):
        """Find and interact with JavaScript buttons and elements"""
        logger.info(f"🔄 Looking for JavaScript interactive elements on {url}")
        
        # Define various selectors for interactive elements
        interactive_selectors = [
            'button',
            'input[type="button"]',
            'input[type="submit"]',
            '[onclick]',
            '[role="button"]',
            '.btn',
            '.button',
            '.demo-button',
            'a[href="#"]',
            '[data-action]',
            '[data-click]'
        ]
        
        interactions = []
        
        for selector in interactive_selectors:
            try:
                elements = await page.locator(selector).all()
                logger.info(f"  📎 Found {len(elements)} elements matching '{selector}'")
                
                for i, element in enumerate(elements[:5]):  # Limit to 5 per selector
                    try:
                        # Get element info
                        is_visible = await element.is_visible()
                        is_enabled = await element.is_enabled()
                        
                        if not is_visible or not is_enabled:
                            continue
                            
                        # Get element text/attributes
                        text = await element.text_content() or ''
                        onclick = await element.get_attribute('onclick') or ''
                        data_action = await element.get_attribute('data-action') or ''
                        element_id = await element.get_attribute('id') or f'element_{i}'
                        
                        element_info = {
                            'selector': selector,
                            'text': text.strip(),
                            'onclick': onclick,
                            'data_action': data_action,
                            'id': element_id
                        }
                        
                        logger.info(f"    🎯 Interacting with: {element_info['text'] or element_info['id']}")
                        
                        # Capture page state before interaction
                        content_before = await page.content()
                        url_before = page.url
                        
                        # Perform the interaction
                        await element.click()
                        await asyncio.sleep(max(self.delay, 1))
                        
                        # Wait for potential navigation or content changes
                        try:
                            await page.wait_for_load_state('networkidle', timeout=5000)
                        except PlaywrightTimeoutError:
                            pass
                        
                        # Capture page state after interaction
                        content_after = await page.content()
                        url_after = page.url
                        
                        # Analyze changes
                        content_change = len(content_after) - len(content_before)
                        url_changed = url_after != url_before
                        
                        interaction_result = {
                            **element_info,
                            'content_change': content_change,
                            'url_changed': url_changed,
                            'url_before': url_before,
                            'url_after': url_after,
                            'timestamp': time.time()
                        }
                        
                        interactions.append(interaction_result)
                        
                        if content_change > 100:
                            logger.info(f"    ✅ Significant content change: +{content_change} characters")
                        if url_changed:
                            logger.info(f"    🔄 URL changed: {url_before} -> {url_after}")
                            
                        # If we navigated away, go back
                        if url_changed and url_after != url:
                            await page.go_back()
                            await asyncio.sleep(self.delay)
                            
                    except Exception as e:
                        logger.warning(f"    ⚠️ Error interacting with element: {e}")
                        
            except Exception as e:
                logger.warning(f"  ⚠️ Error with selector '{selector}': {e}")
        
        self.javascript_interactions.extend(interactions)
        logger.info(f"✅ Completed {len(interactions)} JavaScript interactions")
        return interactions
    
    async def _extract_dynamic_content(self, page):
        """Extract content that might be loaded dynamically"""
        logger.info("🔍 Extracting dynamic content...")
        
        dynamic_content = {}
        
        # Wait for any lazy-loaded content
        await asyncio.sleep(2)
        
        # Scroll to trigger any scroll-based loading
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        await asyncio.sleep(1)
        await page.evaluate("window.scrollTo(0, 0)")
        await asyncio.sleep(1)
        
        # Look for hidden elements that might become visible
        hidden_elements = await page.locator('[style*="display: none"], [hidden], .hidden').all()
        dynamic_content['hidden_elements'] = len(hidden_elements)
        
        # Check for AJAX endpoints in JavaScript
        js_content = await page.evaluate("""
            () => {
                const scripts = Array.from(document.scripts);
                const jsContent = scripts.map(script => script.innerHTML).join(' ');
                
                // Look for API endpoints
                const apiMatches = jsContent.match(/['"]\\/api\\/[^'"]+/g) || [];
                const fetchMatches = jsContent.match(/fetch\\s*\\([^)]+\\)/g) || [];
                const ajaxMatches = jsContent.match(/\\$\\.ajax\\s*\\([^)]+\\)/g) || [];
                
                return {
                    api_endpoints: apiMatches,
                    fetch_calls: fetchMatches,
                    ajax_calls: ajaxMatches
                };
            }
        """)
        
        dynamic_content['javascript_analysis'] = js_content
        
        # Look for data attributes that might indicate dynamic behavior
        data_elements = await page.locator('[data-action], [data-click], [data-toggle], [data-target]').all()
        data_attrs = []
        for element in data_elements[:10]:  # Limit to 10
            attrs = await element.evaluate("el => Array.from(el.attributes).filter(attr => attr.name.startsWith('data-')).map(attr => attr.name + '=' + attr.value)")
            data_attrs.extend(attrs)
        
        dynamic_content['data_attributes'] = data_attrs
        
        return dynamic_content
    
    async def _analyze_page_content(self, page, url, page_type="Unknown"):
        """Comprehensive analysis of page content"""
        logger.info(f"📊 Analyzing content for {page_type}: {url}")
        
        try:
            # Basic page information
            title = await page.title()
            content = await page.content()
            
            analysis = {
                'url': url,
                'page_type': page_type,
                'title': title,
                'content_length': len(content),
                'timestamp': time.time()
            }
            
            # Extract meta information
            meta_info = await page.evaluate("""
                () => {
                    const metas = Array.from(document.querySelectorAll('meta'));
                    return metas.map(meta => ({
                        name: meta.name || meta.property || meta.httpEquiv,
                        content: meta.content
                    })).filter(meta => meta.name);
                }
            """)
            analysis['meta_tags'] = meta_info
            
            # Extract headings structure
            headings = await page.evaluate("""
                () => {
                    const headings = [];
                    for (let i = 1; i <= 6; i++) {
                        const elements = document.querySelectorAll(`h${i}`);
                        elements.forEach(el => {
                            headings.push({
                                level: i,
                                text: el.textContent.trim(),
                                id: el.id
                            });
                        });
                    }
                    return headings;
                }
            """)
            analysis['headings'] = headings
            
            # Extract links and their types
            links = await page.evaluate("""
                () => {
                    const links = Array.from(document.querySelectorAll('a[href]'));
                    return links.map(link => ({
                        href: link.href,
                        text: link.textContent.trim(),
                        target: link.target,
                        rel: link.rel
                    }));
                }
            """)
            analysis['links'] = links
            
            # Extract forms and inputs
            forms = await page.evaluate("""
                () => {
                    const forms = Array.from(document.querySelectorAll('form'));
                    return forms.map(form => ({
                        action: form.action,
                        method: form.method,
                        inputs: Array.from(form.querySelectorAll('input, select, textarea')).map(input => ({
                            name: input.name,
                            type: input.type,
                            id: input.id,
                            placeholder: input.placeholder,
                            value: input.value
                        }))
                    }));
                }
            """)
            analysis['forms'] = forms
            
            # Extract sensitive patterns
            patterns = {
                'emails': re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', content),
                'phone_numbers': re.findall(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', content),
                'api_keys': re.findall(r'[A-Za-z0-9]{32,}', content),
                'urls': re.findall(r'https?://[^\s<>"]+', content),
                'ip_addresses': re.findall(r'\b(?:\d{1,3}\.){3}\d{1,3}\b', content)
            }
            analysis['patterns'] = {k: list(set(v))[:10] for k, v in patterns.items() if v}
            
            # Check for error indicators
            error_indicators = ['error', '404', '403', '500', 'not found', 'access denied', 'forbidden']
            found_errors = [error for error in error_indicators if error.lower() in content.lower()]
            analysis['error_indicators'] = found_errors
            
            logger.info(f"✅ Analysis complete: {len(content)} chars, {len(headings)} headings, {len(links)} links")
            return analysis
            
        except Exception as e:
            logger.error(f"❌ Error analyzing page content: {e}")
            return {'error': str(e), 'url': url, 'page_type': page_type}
    
    async def explore_private_endpoints(self, page):
        """Systematically explore private endpoints"""
        logger.info("🔒 Starting private endpoint exploration...")
        
        # Comprehensive list of private paths to test
        private_paths = [
            '/private',
            # '/private/',
            # '/private/index.html',
            '/private/index.html',
            # '/private/home.html',
            # '/private/dashboard.html',
            # '/private/admin.html',
            # '/private/user.html',
            # '/private/profile.html',
            # '/private/account.html',
            # '/private/settings.html',
            # '/private/config.html',
            # '/private/data.html',
            # '/private/api.html',
            # '/private/docs.html',
            # '/private/files.html',
            # '/private/uploads.html',
            # '/private/downloads.html',
            # '/private/secure.html',
            # '/private/protected.html',
            # '/private/internal.html',
            # '/private/staff.html',
            # '/private/employee.html',
            # '/private/management.html',
            # '/private/executive.html',
            # '/private/confidential.html',
            # '/private/secret.html',
            # '/private/hidden.html',
            # '/private/test.html',
            # '/private/dev.html',
            # '/private/staging.html',
            # '/private/beta.html',
            # '/private/alpha.html',
            # '/private/demo.html',
            # '/private/sample.html',
            # '/private/example.html',
            # '/private/backup.html',
            # '/private/archive.html',
            # '/private/old.html',
            # '/private/legacy.html',
            # '/private/temp.html',
            # '/private/tmp.html'
        ]
        
        # Also test without .html extension
        additional_paths = []
        for path in private_paths:
            if path.endswith('.html'):
                additional_paths.append(path[:-5])  # Remove .html
        private_paths.extend(additional_paths)
        
        # Remove duplicates
        private_paths = list(set(private_paths))
        
        logger.info(f"🎯 Testing {len(private_paths)} private endpoints...")
        
        private_results = {}
        
        for i, path in enumerate(private_paths):
            url = f"{self.base_url}{path}"
            logger.info(f"🔍 [{i+1}/{len(private_paths)}] Testing: {url}")
            
            try:
                # Navigate to the private endpoint
                response = await page.goto(url, wait_until='domcontentloaded', timeout=15000)
                status_code = response.status
                
                logger.info(f"  📊 Response: {status_code}")
                
                # Wait for content to load
                await asyncio.sleep(1)
                
                # Analyze the page
                analysis = await self._analyze_page_content(page, url, f"Private Endpoint ({status_code})")
                analysis['status_code'] = status_code
                analysis['accessible'] = status_code < 400
                
                # If accessible, perform deeper analysis
                if status_code < 400:
                    logger.info(f"  ✅ Accessible! Performing deep analysis...")
                    
                    # Look for JavaScript interactions
                    interactions = await self._interact_with_javascript_elements(page, url)
                    analysis['javascript_interactions'] = interactions
                    
                    # Extract dynamic content
                    dynamic_content = await self._extract_dynamic_content(page)
                    analysis['dynamic_content'] = dynamic_content
                    
                    # Look for additional private paths mentioned in content
                    content = await page.content()
                    mentioned_paths = re.findall(r'/private/[a-zA-Z0-9._/-]+', content)
                    new_paths = [p for p in mentioned_paths if p not in private_paths]
                    if new_paths:
                        logger.info(f"  🔍 Found {len(new_paths)} new private paths: {new_paths[:5]}")
                        analysis['discovered_paths'] = new_paths
                        # Add to our list for future testing
                        private_paths.extend(new_paths)
                
                private_results[path] = analysis
                
                # Rate limiting
                await asyncio.sleep(self.delay)
                
            except PlaywrightTimeoutError:
                logger.warning(f"  ⏰ Timeout accessing {url}")
                private_results[path] = {
                    'url': url,
                    'error': 'timeout',
                    'accessible': False,
                    'status_code': 'timeout'
                }
            except Exception as e:
                logger.warning(f"  ❌ Error accessing {url}: {e}")
                private_results[path] = {
                    'url': url,
                    'error': str(e),
                    'accessible': False,
                    'status_code': 'error'
                }
        
        self.scraping_results['private_endpoints'] = private_results
        
        # Summary
        accessible_count = sum(1 for result in private_results.values() 
                             if result.get('accessible', False))
        logger.info(f"✅ Private endpoint exploration complete: {accessible_count}/{len(private_results)} accessible")
        
        return private_results
    
    async def run_comprehensive_scan(self, page):
        """Run the complete bot scraping and private endpoint exploration"""
        logger.info("🚀 Starting comprehensive bot scraping scan...")
        
        # Step 1: Access and analyze bot demo page
        logger.info("\n" + "="*60)
        logger.info("STEP 1: BOT DEMO PAGE ANALYSIS")
        logger.info("="*60)
        
        bot_demo_result = await self.access_bot_demo_page(page)
        
        # Step 2: Explore private endpoints
        logger.info("\n" + "="*60)
        logger.info("STEP 2: PRIVATE ENDPOINT EXPLORATION")
        logger.info("="*60)
        
        private_results = await self.explore_private_endpoints(page)
        
        # Step 3: Generate comprehensive report
        logger.info("\n" + "="*60)
        logger.info("STEP 3: GENERATING COMPREHENSIVE REPORT")
        logger.info("="*60)
        
        self.generate_comprehensive_report()
        
        return {
            'bot_demo': bot_demo_result,
            'private_endpoints': private_results,
            'javascript_interactions': self.javascript_interactions,
            'session_data': self.session_data
        }
    
    def generate_comprehensive_report(self):
        """Generate and display comprehensive scraping results"""
        print("\n" + "="*100)
        print("🕷️  COMPREHENSIVE BOT SCRAPING REPORT")
        print("="*100)
        
        # Bot Demo Analysis
        if 'bot_demo' in self.scraping_results:
            bot_demo = self.scraping_results['bot_demo']
            print(f"\n🎯 BOT DEMO PAGE ANALYSIS:")
            print(f"   URL: {bot_demo.get('url', 'N/A')}")
            print(f"   Title: {bot_demo.get('title', 'N/A')}")
            print(f"   Content Length: {bot_demo.get('content_length', 0):,} characters")
            print(f"   Headings Found: {len(bot_demo.get('headings', []))}")
            print(f"   Links Found: {len(bot_demo.get('links', []))}")
            print(f"   Forms Found: {len(bot_demo.get('forms', []))}")
            
            # Display patterns found
            patterns = bot_demo.get('patterns', {})
            if patterns:
                print(f"\n   🔍 PATTERNS EXTRACTED:")
                for pattern_type, items in patterns.items():
                    print(f"     {pattern_type.title()}: {len(items)} found")
                    for item in items[:3]:  # Show first 3
                        print(f"       - {item}")
                    if len(items) > 3:
                        print(f"       ... and {len(items) - 3} more")
        
        # JavaScript Interactions Summary
        if self.javascript_interactions:
            print(f"\n🔄 JAVASCRIPT INTERACTIONS SUMMARY:")
            interaction_table = []
            for interaction in self.javascript_interactions:
                interaction_table.append([
                    interaction.get('text', 'N/A')[:30],
                    interaction.get('selector', 'N/A'),
                    interaction.get('content_change', 0),
                    'Yes' if interaction.get('url_changed', False) else 'No',
                    interaction.get('onclick', 'N/A')[:40]
                ])
            
            headers = ['Element Text', 'Selector', 'Content Δ', 'URL Changed', 'OnClick']
            print(tabulate(interaction_table, headers=headers, tablefmt='grid'))
        
        # Private Endpoints Analysis
        if 'private_endpoints' in self.scraping_results:
            private_results = self.scraping_results['private_endpoints']
            
            # Summary statistics
            total_tested = len(private_results)
            accessible = sum(1 for r in private_results.values() if r.get('accessible', False))
            errors = sum(1 for r in private_results.values() if 'error' in r)
            
            print(f"\n🔒 PRIVATE ENDPOINTS SUMMARY:")
            print(f"   Total Tested: {total_tested}")
            print(f"   Accessible: {accessible}")
            print(f"   Errors/Timeouts: {errors}")
            print(f"   Success Rate: {(accessible/total_tested)*100:.1f}%")
            
            # Accessible endpoints table
            accessible_endpoints = {k: v for k, v in private_results.items() 
                                  if v.get('accessible', False)}
            
            if accessible_endpoints:
                print(f"\n✅ ACCESSIBLE PRIVATE ENDPOINTS ({len(accessible_endpoints)} found):")
                endpoint_table = []
                for path, result in accessible_endpoints.items():
                    endpoint_table.append([
                        path,
                        result.get('status_code', 'N/A'),
                        result.get('title', 'N/A')[:40],
                        result.get('content_length', 0),
                        len(result.get('headings', [])),
                        len(result.get('links', [])),
                        len(result.get('javascript_interactions', []))
                    ])
                
                headers = ['Path', 'Status', 'Title', 'Content Size', 'Headings', 'Links', 'JS Interactions']
                print(tabulate(endpoint_table, headers=headers, tablefmt='grid'))
                
                # Detailed analysis for most interesting endpoints
                interesting_endpoints = sorted(accessible_endpoints.items(), 
                                             key=lambda x: x[1].get('content_length', 0), 
                                             reverse=True)[:3]
                
                for path, result in interesting_endpoints:
                    print(f"\n📋 DETAILED ANALYSIS: {path}")
                    print(f"   URL: {result.get('url')}")
                    print(f"   Status: {result.get('status_code')}")
                    print(f"   Title: {result.get('title')}")
                    
                    # Show headings
                    headings = result.get('headings', [])
                    if headings:
                        print(f"   Headings:")
                        for heading in headings[:5]:
                            print(f"     H{heading.get('level')}: {heading.get('text')}")
                    
                    # Show discovered patterns
                    patterns = result.get('patterns', {})
                    if patterns:
                        print(f"   Patterns Found:")
                        for pattern_type, items in patterns.items():
                            print(f"     {pattern_type.title()}: {items[:3]}")
                    
                    # Show JavaScript interactions
                    js_interactions = result.get('javascript_interactions', [])
                    if js_interactions:
                        print(f"   JavaScript Interactions: {len(js_interactions)}")
                        for interaction in js_interactions[:3]:
                            print(f"     - {interaction.get('text', 'N/A')} (Δ{interaction.get('content_change', 0)})")
            
            # Error summary
            error_endpoints = {k: v for k, v in private_results.items() 
                             if not v.get('accessible', False)}
            
            if error_endpoints:
                print(f"\n❌ INACCESSIBLE ENDPOINTS ({len(error_endpoints)} found):")
                error_table = []
                error_summary = defaultdict(int)
                
                for path, result in error_endpoints.items():
                    status = result.get('status_code', result.get('error', 'unknown'))
                    error_summary[str(status)] += 1
                    error_table.append([path, status])
                
                # Show error summary
                print("   Error Summary:")
                for error_type, count in error_summary.items():
                    print(f"     {error_type}: {count} endpoints")
        
        # Overall Statistics
        print(f"\n📊 OVERALL STATISTICS:")
        stats_table = [
            ['Total JavaScript Interactions', len(self.javascript_interactions)],
            ['Total Private Paths Tested', len(self.scraping_results.get('private_endpoints', {}))],
            ['Accessible Private Paths', sum(1 for r in self.scraping_results.get('private_endpoints', {}).values() if r.get('accessible', False))],
            ['Total Content Analyzed', sum(r.get('content_length', 0) for r in self.scraping_results.values() if isinstance(r, dict))],
            ['Scan Duration', f"{time.time() - self.session_data.get('start_time', time.time()):.1f} seconds"]
        ]
        print(tabulate(stats_table, headers=['Metric', 'Value'], tablefmt='grid'))

async def main():
    """Main execution function"""
    # Load environment variables
    env_path = Path(__file__).parent / '.env'
    load_dotenv(dotenv_path=env_path)
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Advanced Bot Scraper for Bot Demo and Private Endpoints')
    parser.add_argument('--url', 
                       default=os.getenv('TARGET_URL', 'https://d3mx9cjq6wwawz.cloudfront.net'),
                       help='Base URL for the website')
    parser.add_argument('--headless', 
                       type=str_to_bool,
                       default=str_to_bool(os.getenv('HEADLESS', 'true')),
                       help='Run in headless mode')
    parser.add_argument('--delay',
                       type=float,
                       default=float(os.getenv('DELAY', '2')),
                       help='Delay between requests in seconds')
    parser.add_argument('--timeout',
                       type=int,
                       default=int(os.getenv('TIMEOUT', '30')),
                       help='Browser timeout in seconds')
    parser.add_argument('--user-agent',
                       default=os.getenv('USER_AGENT', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36'),
                       help='User agent string to use')
    
    args = parser.parse_args()
    
    print(f"🕷️  ADVANCED BOT SCRAPER")
    print(f"📍 Target URL: {args.url}")
    print(f"🤖 User Agent: {args.user_agent}")
    print(f"⏱️  Delay: {args.delay}s")
    print(f"👁️  Headless: {args.headless}")
    print(f"⏰ Timeout: {args.timeout}s")
    print("-" * 100)
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=args.headless,
            args=[
                '--no-sandbox', 
                '--disable-setuid-sandbox',
                '--disable-web-security',
                '--disable-features=VizDisplayCompositor',
                '--disable-blink-features=AutomationControlled'
            ]
        )
        
        try:
            context = await browser.new_context(
                user_agent=args.user_agent,
                viewport={'width': 1920, 'height': 1080},
                extra_http_headers={
                    'Accept-Language': 'en-US,en;q=0.9',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
                }
            )
            
            context.set_default_timeout(args.timeout * 1000)
            page = await context.new_page()
            
            # Create scraper and run comprehensive scan
            scraper = BotDemoScraper(args.url, args.user_agent, args.delay, args.timeout)
            scraper.session_data['start_time'] = time.time()
            
            # Set up the page
            await scraper.setup_page(page)
            
            # Run the comprehensive scan
            results = await scraper.run_comprehensive_scan(page)
            
            logger.info("✅ Comprehensive bot scraping completed successfully!")
            return 0
            
        except Exception as e:
            logger.error(f"❌ Error during scraping: {str(e)}")
            return 1
        finally:
            await browser.close()

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
