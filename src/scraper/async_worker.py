import asyncio
import aiohttp
from playwright.async_api import async_playwright
import logging
from typing import List, Dict

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AsyncCrawler:
    """
    Handles Phase I & Phase V: Massive Data Acquisition & Anti-Bot Navigation.
    Uses an asyncio Worker Pool and Playwright for Cloudflare evasion.
    """
    def __init__(self, concurrency_limit: int = 10):
        # Semaphore controls exactly how many concurrent requests are active
        self.semaphore = asyncio.Semaphore(concurrency_limit)
    
    async def fetch_static(self, session: aiohttp.ClientSession, url: str) -> str:
        """Fast, lightweight request for unprotected domains (e.g., Arxiv)"""
        async with self.semaphore:
            try:
                async with session.get(url, timeout=15) as response:
                    response.raise_for_status()
                    return await response.text()
            except Exception as e:
                logger.error(f"Static fetch failed for {url}: {e}")
                return ""

    async def fetch_dynamic(self, url: str) -> str:
        """
        Anti-Bot Navigation using Playwright.
        Used for high-value sources blocked by Cloudflare/Datadome.
        """
        async with self.semaphore:
            try:
                async with async_playwright() as p:
                    # Launching chromium with stealth settings (args to avoid bot detection)
                    browser = await p.chromium.launch(
                        headless=True,
                        args=["--disable-blink-features=AutomationControlled"]
                    )
                    context = await browser.new_context(
                        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                    )
                    page = await context.new_page()
                    
                    # Wait until network is idle to ensure JS framework has rendered data
                    await page.goto(url, wait_until="networkidle", timeout=30000)
                    
                    # Extract full HTML
                    html = await page.content()
                    await browser.close()
                    return html
            except Exception as e:
                logger.error(f"Dynamic fetch failed for {url}: {e}")
                return ""

    async def process_batch(self, urls: List[Dict[str, str]]):
        """
        Processes a massive batch of URLs using the worker pool pattern.
        """
        async with aiohttp.ClientSession() as session:
            tasks = []
            for item in urls:
                url = item['url']
                source_type = item['type']
                
                # Route based on domain protection level
                if source_type == "static":
                    tasks.append(self.fetch_static(session, url))
                elif source_type == "protected":
                    tasks.append(self.fetch_dynamic(url))
                    
            # Execute all tasks concurrently up to the semaphore limit
            results = await asyncio.gather(*tasks)
            return results

# Example Usage:
# async def main():
#     crawler = AsyncCrawler(concurrency_limit=5)
#     urls = [
#         {"url": "https://arxiv.org/abs/2303.08774", "type": "static"},
#         {"url": "https://news.ycombinator.com", "type": "protected"} # Example protected
#     ]
#     html_results = await crawler.process_batch(urls)

