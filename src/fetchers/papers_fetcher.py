import asyncio
import aiohttp
from datetime import datetime
import xml.etree.ElementTree as ET
import logging
from typing import List
import os

from src.models.schemas import ResearchPaperEntity, ResearchPaperContent, SourceInfo
from src.models.schemas import ResearchPaperEntity, ResearchPaperContent
from src.exporter import DataExporter

# Setup basic logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

async def fetch_papers_batch(session: aiohttp.ClientSession, page: int) -> List[dict]:
    """Fetches a page of 50 papers from PapersWithCode API"""
    url = f"https://paperswithcode.com/api/v1/papers/?page={page}&items_per_page=50"
async def fetch_arxiv_papers(session: aiohttp.ClientSession, start: int, max_results: int) -> List[dict]:
    """Fetches a batch of papers directly from the Arxiv XML API."""
    url = f'http://export.arxiv.org/api/query?search_query=cat:cs.AI&start={start}&max_results={max_results}'
    async with session.get(url) as response:
        if response.status == 200:
            data = await response.json()
            return data.get('results', [])
        else:
            logger.warning(f"Failed to fetch page {page}. Status: {response.status}")
            return []
            xml_data = await response.text()
            root = ET.fromstring(xml_data)
            papers = []
            namespace = {'atom': 'http://www.w3.org/2005/Atom'}
            for entry in root.findall('atom:entry', namespace):
                title = entry.find('atom:title', namespace).text.replace('\n', ' ').strip()
                published = entry.find('atom:published', namespace).text
                paper_url = entry.find('atom:id', namespace).text
                authors = [author.find('atom:name', namespace).text for author in entry.findall('atom:author', namespace)]
                
                papers.append({
                    'title': title,
                    'published': published,
                    'paper_url': paper_url,
                    'authors': authors
                })
            return papers
        return []

async def fetch_repo_stars(session: aiohttp.ClientSession, paper_id: str) -> dict:
    """Fetches the associated GitHub repositories and stars for a specific paper"""
    url = f"https://paperswithcode.com/api/v1/papers/{paper_id}/repositories/"
async def fetch_github_stars(session: aiohttp.ClientSession, title: str) -> dict:
    """Queries the GitHub Search API for the paper title to find associated code."""
    # Take the first few distinct words to improve search matching
    query = "+".join(title.split()[:4])
    url = f"https://api.github.com/search/repositories?q={query}"
    
    try:
        async with session.get(url) as response:
            if response.status == 200:
                data = await response.json()
                results = data.get('results', [])
                if results:
                    # Return the primary/top repository
                    return {
                        "github_url": results[0].get('url'), 
                        "stars": results[0].get('stars')
                    }
    except Exception as e:
                items = data.get('items', [])
                if items:
                    return {"github_url": items[0]['html_url'], "stars": items[0]['stargazers_count']}
            elif response.status == 403:
                # Expected: GitHub unauthenticated rate limit is low. We gracefully degrade.
                pass
    except Exception:
        pass
    
        
    return {"github_url": None, "stars": None}

async def gather_1000_papers():
    """
    Main pipeline to collect 1,000+ Research Papers concurrently.
    Demonstrates Phase I (Massive Bulk Extraction) and Phase V (Async Operation).
    """
    papers_collected: List[ResearchPaperEntity] = []
    
    print("🚀 Starting High-Concurrency Extraction for Research Papers...")
    print("[*] Starting High-Concurrency Extraction for Arxiv Papers...")
    
    # We use aiohttp to manage a connection pool for massive parallel requests
    async with aiohttp.ClientSession() as session:
        # 25 pages * 50 items/page = 1,250 papers (gives us a buffer over 1,000)
        for page in range(1, 25):
            print(f"📥 Fetching Page {page}/24 from PapersWithCode...")
            batch = await fetch_papers_batch(session, page)
        # Fetch 1000 papers in chunks of 200
        chunk_size = 200
        for start in range(0, 1000, chunk_size):
            print(f"[*] Fetching papers {start} to {start+chunk_size} from Arxiv API...")
            batch = await fetch_arxiv_papers(session, start, chunk_size)
            
            if not batch:
                break
                
            # Fire off concurrent requests to grab the GitHub details for all 50 papers at once
            repo_tasks = [fetch_repo_stars(session, paper['id']) for paper in batch]
            print(f"[*] Fetched {len(batch)} papers. Querying GitHub API for repositories (Expect graceful degradation on 403 Rate Limits)...")
            repo_tasks = [fetch_github_stars(session, paper['title']) for paper in batch]
            repo_results = await asyncio.gather(*repo_tasks)
            
            # Map the raw data strictly into our Pydantic Schema
            for paper_data, repo_data in zip(batch, repo_results):
                try:
                    # Normalize dates to ISO-8601
                    pub_date_str = paper_data.get('published', '2023-01-01')
                    pub_date = datetime.strptime(pub_date_str, "%Y-%m-%d")
                    pub_date = datetime.strptime(paper_data['published'], "%Y-%m-%dT%H:%M:%SZ")
                except:
                    pub_date = datetime.utcnow()

                # Build the structured Pydantic model
                content = ResearchPaperContent(
                    title=paper_data.get('title', 'Unknown Title'),
                    authors=paper_data.get('authors', []),
                    paper_url=paper_data.get('url_abs', 'https://arxiv.org'),
                    title=paper_data['title'],
                    authors=paper_data['authors'],
                    paper_url=paper_data['paper_url'],
                    github_url=repo_data['github_url'],
                    github_stars=repo_data['stars'],
                    published_date=pub_date
                )
                
                entity = ResearchPaperEntity(
                    content=content
                )
                entity = ResearchPaperEntity(content=content)
                papers_collected.append(entity)
                
            print(f"✅ Processed {len(papers_collected)} papers so far...")
            
            if len(papers_collected) >= 1000:
                print("🎯 Reached 1,000 target records. Stopping extraction.")
                # Slice to exactly 1000 to meet the requirement perfectly
                papers_collected = papers_collected[:1000]
                break
            print(f"[+] Processed {len(papers_collected)} papers so far...")
    
    # Export using our Google Sheets exporter module
    print("\n💾 Structuring and Exporting to CSV...")
    print("\n[*] Structuring and Exporting to CSV...")
    exporter = DataExporter()
    exporter.export_research_papers(papers_collected)
    print("🎉 Done! The file '3_Research_Papers.csv' is ready for Google Sheets.")
    print("[+] Done! The file '3_Research_Papers.csv' is ready for Google Sheets.")

if __name__ == "__main__":
    # Suppress Windows ProactorEventLoop errors when closing sessions
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(gather_1000_papers())

