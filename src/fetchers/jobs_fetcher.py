import asyncio
import aiohttp
from datetime import datetime, timezone
import logging
from typing import List
import time

from src.models.schemas import JobEntity, JobContent
from src.exporter import DataExporter

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

async def fetch_recent_jobs(session: aiohttp.ClientSession) -> List[dict]:
    """Fetches AI jobs posted strictly within the last 24 hours."""
    timestamp_24h_ago = int(time.time()) - 86400
    url = f"https://hn.algolia.com/api/v1/search_by_date?query=hiring+AI&tags=comment&numericFilters=created_at_i>{timestamp_24h_ago}&hitsPerPage=100"
    
    async with session.get(url) as response:
        if response.status == 200:
            data = await response.json()
            return data.get('hits', [])
        return []

async def gather_jobs():
    jobs_collected: List[JobEntity] = []
    print("[*] Starting Extraction for 24-Hour Fresh Jobs...")
    
    async with aiohttp.ClientSession() as session:
        hits = await fetch_recent_jobs(session)
        print(f"[*] Found {len(hits)} fresh job postings within the last 24 hours.")
        
        for hit in hits:
            # Date Normalization explicitly mapping ISO-8601
            pub_date_str = hit.get('created_at')
            pub_date = datetime.strptime(pub_date_str, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
            
            text = hit.get('comment_text', '')
            is_remote = 'remote' in text.lower()
            
            # Simple heuristic for role
            role = "Engineering" if 'engineer' in text.lower() or 'developer' in text.lower() else "General"
            
            # Extract company name via heuristic (first word usually in 'Who is hiring' threads)
            company = hit.get('story_title', 'Unknown Company').split()[0]
            if len(company) < 2: company = "AI Startup"

            content = JobContent(
                company=company,
                date=pub_date,
                is_remote=is_remote,
                role_family=role
            )
            
            entity = JobEntity(content=content)
            jobs_collected.append(entity)

    print("[*] Exporting Jobs to CSV...")
    exporter = DataExporter()
    exporter.export_jobs(jobs_collected)
    print("[+] Done! '4_Jobs.csv' is ready.")

if __name__ == "__main__":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(gather_jobs())

