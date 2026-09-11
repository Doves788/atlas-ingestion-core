from pydantic import BaseModel, Field, HttpUrl
from typing import List, Optional
from datetime import datetime, timezone
from enum import Enum

# --- Shared Base Models ---

class SourceInfo(BaseModel):
    name: str = Field(..., description="Name of the source site (e.g., 'TechCrunch', 'Arxiv')")
    url: HttpUrl = Field(..., description="Original source URL")

class PricingModel(str, Enum):
    FREE = "FREE"
    FREEMIUM = "FREEMIUM"
    PAID = "PAID"
    ENTERPRISE = "ENTERPRISE"

# --- Entity Specific Content Models ---

class StartupContent(BaseModel):
    entityName: str = Field(..., description="Canonical startup name")
    employeeCount: Optional[int] = Field(None, description="Number of employees if explicitly stated")

class ProductContent(BaseModel):
    startupName: str = Field(..., description="Canonical startup name associated with the product")
    pricingModel: PricingModel = Field(..., description="The pricing model of the product")

class ResearchPaperContent(BaseModel):
    title: str = Field(..., description="Title of the research paper")
    authors: List[str] = Field(..., description="List of author names")
    paper_url: HttpUrl = Field(..., description="Link to the Arxiv/PDF page")
    github_url: Optional[HttpUrl] = Field(None, description="Link to the associated code repository (if any)")
    github_stars: Optional[int] = Field(None, description="Current number of stars on the GitHub repository")
    published_date: datetime = Field(..., description="ISO-8601 publication date")

class JobContent(BaseModel):
    company: str = Field(..., description="Canonical company name")
    date: datetime = Field(..., description="ISO-8601 publication date")
    is_remote: bool = Field(..., description="Is the job eligible for remote work?")
    role_family: str = Field(..., description="Functional category (e.g., 'Engineering', 'Product')")

class NewsContent(BaseModel):
    title: str = Field(..., description="Headline of the news article")
    date: datetime = Field(..., description="ISO-8601 publication date")
    summary: Optional[str] = Field(None, description="Brief summary of the article")

# --- Top-Level Entity Models ---

class StartupEntity(BaseModel):
    schemaVersion: str = Field(default="1.0")
    recordType: str = Field(default="STARTUP")
    source: SourceInfo
    content: StartupContent
    collectedAt: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class ProductEntity(BaseModel):
    schemaVersion: str = Field(default="1.0")
    recordType: str = Field(default="PRODUCT")
    source: SourceInfo
    content: ProductContent
    collectedAt: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class ResearchPaperEntity(BaseModel):
    schemaVersion: str = Field(default="1.0")
    recordType: str = Field(default="RESEARCH_PAPER")
    content: ResearchPaperContent
    collectedAt: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class JobEntity(BaseModel):
    schemaVersion: str = Field(default="1.0")
    recordType: str = Field(default="JOB")
    content: JobContent
    collectedAt: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class NewsEntity(BaseModel):
    schemaVersion: str = Field(default="1.0")
    recordType: str = Field(default="NEWS")
    source: SourceInfo
    content: NewsContent
    collectedAt: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
