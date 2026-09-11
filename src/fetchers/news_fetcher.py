import asyncio
import aiohttp
from datetime import datetime, timezone
import logging
from typing import List
import time

from src.models.schemas import NewsEntity, NewsContent, SourceInfo
from src.exporter import DataExporter

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

async def fetch_recent_news(session: aiohttp.ClientSession) -> List[dict]:
    """Fetches AI news posted strictly within the last 24 hours."""
    timestamp_24h_ago = int(time.time()) - 86400
    url = f"https://hn.algolia.com/api/v1/search_by_date?query=Artificial+Intelligence&tags=story&numericFilters=created_at_i>{timestamp_24h_ago}&hitsPerPage=100"
    
    async with session.get(url) as response:
        if response.status == 200:
            data = await response.json()
            return data.get('hits', [])
        return []

async def gather_news():
    news_collected: List[NewsEntity] = []
    print("[*] Starting Extraction for 24-Hour Fresh News...")
    
    async with aiohttp.ClientSession() as session:
        hits = await fetch_recent_news(session)
        print(f"[*] Found {len(hits)} fresh news articles within the last 24 hours.")
        
        for hit in hits:
            # Date Normalization
            pub_date_str = hit.get('created_at')
            pub_date = datetime.strptime(pub_date_str, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
            
            title = hit.get('title', 'Unknown News')
            url = hit.get('url') or f"https://news.ycombinator.com/item?id={hit.get('objectID')}"

            content = NewsContent(
                title=title,
                date=pub_date,
                summary=hit.get('story_text', '')[:200] if hit.get('story_text') else None
            )
            
            source = SourceInfo(
                name="Hacker News (Fresh)",
                url=url
            )
            
            entity = NewsEntity(source=source, content=content)
            news_collected.append(entity)

    print("[*] Exporting News to CSV...")
    exporter = DataExporter()
    exporter.export_news(news_collected)
    print("[+] Done! '5_News.csv' is ready.")

if __name__ == "__main__":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(gather_news())

