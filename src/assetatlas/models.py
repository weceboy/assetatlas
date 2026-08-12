from __future__ import annotations
from datetime import datetime, timezone
from enum import Enum
from typing import Any
from pydantic import BaseModel, Field

class AssetType(str, Enum):
    fx = "fx"
    prop = "prop"
    character = "character"
    background = "background"
    texture = "texture"
    light = "light"
    particle = "particle"
    ui = "ui"
    unknown = "unknown"

class Priority(str, Enum):
    high = "high"
    medium = "medium"
    low = "low"

class Scene(BaseModel):
    scene_id: str
    location: str | None = None
    mood: str | None = None
    action: str | None = None
    required_elements: list[str] = Field(default_factory=list)
    raw: dict[str, Any] = Field(default_factory=dict)

class AssetRequirement(BaseModel):
    name: str
    type: AssetType = AssetType.unknown
    priority: Priority = Priority.medium
    reusable: bool = True
    quantity: int = 1
    tags: list[str] = Field(default_factory=list)
    scenes: list[str] = Field(default_factory=list)
    variant_of: str | None = None

class AssetSpec(AssetRequirement):
    canonical_name: str
    prompt: str
    atlas_group: str
    generation_count: int = 1

class AtlasCell(BaseModel):
    asset_name: str
    x: int
    y: int
    width: int
    height: int

class AtlasPlan(BaseModel):
    atlas_id: str
    width: int = 2048
    height: int = 2048
    padding: int = 32
    cells: list[AtlasCell]

class AssetMetadata(BaseModel):
    id: str
    filename: str
    category: str
    subcategory: str | None = None
    tags: list[str] = Field(default_factory=list)
    style: str | None = None
    orientation: str | None = None
    width: int
    height: int
    alpha: bool
    source: str = "ai_generated"
    model: str | None = None
    prompt: str | None = None
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    version: int = 1
    scenes: list[str] = Field(default_factory=list)
    quality_status: str = "GENERATED"
    variant_of: str | None = None
    bbox: dict[str, int] | None = None
    atlas_id: str | None = None
    embedding: list[float] | None = None
