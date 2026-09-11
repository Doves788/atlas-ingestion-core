import asyncio
import os
from dotenv import load_dotenv

from src.scraper.async_worker import AsyncCrawler
from src.llm.orchestrator import LLMOrchestrator
from src.resolution.entity_mapper import EntityResolver
from src.models.schemas import StartupEntity, ResearchPaperEntity

load_dotenv()

async def main():
    print("🚀 Initializing Atlas Ingestion Core...")
    
    # 1. Initialize our heavily concurrent crawler
    crawler = AsyncCrawler(concurrency_limit=5)
    
    # 2. Initialize our Fallback LLM Orchestrator
    orchestrator = LLMOrchestrator(
        groq_key=os.getenv("GROQ_API_KEY", "mock_key"),
        gemini_key=os.getenv("GEMINI_API_KEY", "mock_key"),
        deepseek_key=os.getenv("DEEPSEEK_API_KEY", "mock_key")
    )
    
    # 3. Initialize Deterministic Entity Resolver
    resolver = EntityResolver()
    
    print("✅ System initialized. Ready for massive bulk extraction.")
    print("Current Modules Configured:")
    print("- Asynchronous Worker Pool (aiohttp + Playwright)")
    print("- Multi-Tier LLM Fallback (Groq -> Gemini -> DeepSeek)")
    print("- Strict Pydantic Schema Validation")
    print("- Deterministic Entity Canonicalization (RapidFuzz)")

    print("\n--- Testing Entity Resolution Engine ---")
    test_names = ["Open AI", "OpenAI, Inc.", "Anthropic Corp", "Google Deep Mind", "Random Startup LLC"]
    for name in test_names:
        resolved, matched, score = resolver.resolve(name)
        status = "✅ Mapped" if matched else "🆕 New Entity"
        print(f"Raw: {name:<20} | Canonical: {resolved:<15} | Score: {score:>6.2f} | {status}")
    
if __name__ == "__main__":
    asyncio.run(main())
