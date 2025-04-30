"""Minimal Pydantic schema for processed document used in Phase-1 validation."""
from __future__ import annotations

from typing import List, Optional
from pydantic import BaseModel, Field, validator


class Location(BaseModel):
    name: str
    lat: Optional[float] = None
    lng: Optional[float] = None


class EntitiesBlock(BaseModel):
    people: List[dict] = Field(default_factory=list)
    organizations: List[dict] = Field(default_factory=list)
    companies: List[dict] = Field(default_factory=list)


class ProcessedDocument(BaseModel):
    document_type: str
    project: Optional[dict] = None
    patent: Optional[dict] = None
    research: Optional[dict] = None
    locations: List[Location] = Field(default_factory=list)
    entities: Optional[EntitiesBlock] = None
    relationships: List[dict] = Field(default_factory=list)
    funding: Optional[dict] = None
    contact_info: Optional[dict] = None
    dates: List[dict] = Field(default_factory=list)
    text_content: Optional[str] = None

    @validator('document_type')
    def validate_doc_type(cls, v):
        allowed = {"project", "patent", "research", "other"}
        if v not in allowed:
            raise ValueError(f"document_type must be one of {allowed}")
        return v
