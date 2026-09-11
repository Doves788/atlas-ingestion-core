import pandas as pd
import os
import logging
from typing import List
from src.models.schemas import StartupEntity, ProductEntity, ResearchPaperEntity, JobEntity, NewsEntity

logger = logging.getLogger(__name__)

class DataExporter:
    """
    Handles Deliverable 1: Data Output (Google Sheets).
    Flattens complex Pydantic models into CSV files ready for easy import into the 6 required Google Sheet tabs.
    """
    def __init__(self, output_dir: str = "data/output"):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)

    def export_startups(self, startups: List[StartupEntity]):
        data = []
        for s in startups:
            data.append({
                "schemaVersion": s.schemaVersion,
                "recordType": s.recordType,
                "source.name": s.source.name,
                "source.url": str(s.source.url),
                "content.entityName": s.content.entityName,
                "content.data.employeeCount": s.content.employeeCount,
                "collectedAt": s.collectedAt.isoformat()
            })
        df = pd.DataFrame(data)
        path = os.path.join(self.output_dir, "1_Startups.csv")
        df.to_csv(path, index=False)
        logger.info(f"Exported {len(data)} startups to {path}")

    def export_products(self, products: List[ProductEntity]):
        data = []
        for p in products:
            data.append({
                "schemaVersion": p.schemaVersion,
                "recordType": p.recordType,
                "source.name": p.source.name,
                "source.url": str(p.source.url),
                "content.startupName": p.content.startupName,
                "content.pricingModel": p.content.pricingModel.value,
                "collectedAt": p.collectedAt.isoformat()
            })
        df = pd.DataFrame(data)
        path = os.path.join(self.output_dir, "2_Products.csv")
        df.to_csv(path, index=False)
        logger.info(f"Exported {len(data)} products to {path}")

    def export_research_papers(self, papers: List[ResearchPaperEntity]):
        data = []
        for p in papers:
            data.append({
                "schemaVersion": p.schemaVersion,
                "recordType": p.recordType,
                "content.title": p.content.title,
                "content.authors": ", ".join(p.content.authors),
                "content.paper_url": str(p.content.paper_url),
                "content.github_url": str(p.content.github_url) if p.content.github_url else "",
                "content.github_stars": p.content.github_stars,
                "content.published_date": p.content.published_date.isoformat(),
                "collectedAt": p.collectedAt.isoformat()
            })
        df = pd.DataFrame(data)
        path = os.path.join(self.output_dir, "3_Research_Papers.csv")
        df.to_csv(path, index=False)
        logger.info(f"Exported {len(data)} research papers to {path}")

    def export_jobs(self, jobs: List[JobEntity]):
        data = []
        for j in jobs:
            data.append({
                "schemaVersion": j.schemaVersion,
                "recordType": j.recordType,
                "content.company": j.content.company,
                "content.date": j.content.date.isoformat(),
                "content.is_remote": j.content.is_remote,
                "content.role_family": j.content.role_family,
                "collectedAt": j.collectedAt.isoformat()
            })
        df = pd.DataFrame(data)
        path = os.path.join(self.output_dir, "4_Jobs.csv")
        df.to_csv(path, index=False)
        logger.info(f"Exported {len(data)} jobs to {path}")

    def export_news(self, news: List[NewsEntity]):
        data = []
        for n in news:
            data.append({
                "schemaVersion": n.schemaVersion,
                "recordType": n.recordType,
                "source.name": n.source.name,
                "source.url": str(n.source.url),
                "content.title": n.content.title,
                "content.date": n.content.date.isoformat(),
                "content.summary": n.content.summary,
                "collectedAt": n.collectedAt.isoformat()
            })
        df = pd.DataFrame(data)
        path = os.path.join(self.output_dir, "5_News.csv")
        df.to_csv(path, index=False)
        logger.info(f"Exported {len(data)} news articles to {path}")

    def export_entity_mapping_log(self, mapping_log: List[dict]):
        df = pd.DataFrame(mapping_log)
        path = os.path.join(self.output_dir, "6_Entity_Mapping_Log.csv")
        df.to_csv(path, index=False)
        logger.info(f"Exported {len(mapping_log)} entity mappings to {path}")
