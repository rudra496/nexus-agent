"""Skill & Plugin Marketplace for NexusAgent."""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class SkillCategory(str, Enum):
    CODE_QUALITY = "code-quality"
    DATA_PROCESSING = "data-processing"
    DEVOPS = "devops"
    RESEARCH = "research"
    WEB = "web"
    SECURITY = "security"


@dataclass
class MarketplaceItem:
    name: str
    version: str
    description: str
    author: str
    category: SkillCategory
    tags: list[str] = field(default_factory=list)
    downloads: int = 0
    rating: float = 0.0
    rating_count: int = 0
    url: str = ""

    def to_dict(self) -> dict:
        return {
            "name": self.name, "version": self.version, "description": self.description,
            "author": self.author, "category": self.category.value, "tags": self.tags,
            "downloads": self.downloads, "rating": self.rating, "rating_count": self.rating_count,
            "url": self.url,
        }

    @classmethod
    def from_dict(cls, d: dict) -> MarketplaceItem:
        return cls(
            name=d["name"], version=d.get("version", "1.0.0"), description=d.get("description", ""),
            author=d.get("author", ""), category=SkillCategory(d.get("category", "web")),
            tags=d.get("tags", []), downloads=d.get("downloads", 0),
            rating=d.get("rating", 0.0), rating_count=d.get("rating_count", 0),
            url=d.get("url", ""),
        )


class MarketplaceClient:
    """Client for the NexusAgent skill marketplace."""

    DEFAULT_REGISTRY = "https://registry.nexus-agent.dev"
    CACHE_FILE = ".nexus/marketplace_cache.json"

    def __init__(self, registry_url: Optional[str] = None, skills_dir: Optional[str] = None):
        self.registry_url = registry_url or self.DEFAULT_REGISTRY
        self.skills_dir = skills_dir or ".nexus/skills"
        self._cache: list[MarketplaceItem] = []
        self._user_ratings: dict[str, int] = {}  # name -> rating
        self._load_cache()

    def _load_cache(self):
        cache_path = self.CACHE_FILE
        if os.path.exists(cache_path):
            try:
                with open(cache_path) as f:
                    data = json.load(f)
                self._cache = [MarketplaceItem.from_dict(d) for d in data.get("items", [])]
                self._user_ratings = data.get("ratings", {})
            except (json.JSONDecodeError, KeyError):
                self._cache = []

    def _save_cache(self):
        os.makedirs(os.path.dirname(self.CACHE_FILE) or ".", exist_ok=True)
        with open(self.CACHE_FILE, "w") as f:
            json.dump({"items": [i.to_dict() for i in self._cache], "ratings": self._user_ratings, "updated": time.time()}, f, indent=2)

    def refresh(self) -> int:
        """Fetch latest listings from registry. Returns count of items."""
        # In production, this would fetch from registry_url
        # For now, return cached count
        return len(self._cache)

    def search(self, query: str, category: Optional[SkillCategory] = None, tag: Optional[str] = None) -> list[MarketplaceItem]:
        """Search skills by name, description, category, or tag."""
        results = []
        q = query.lower()
        for item in self._cache:
            match = q in item.name.lower() or q in item.description.lower()
            if category and item.category != category:
                match = False
            if tag and tag not in item.tags:
                match = False
            if match:
                results.append(item)
        return sorted(results, key=lambda x: x.downloads, reverse=True)

    def list_all(self, category: Optional[SkillCategory] = None) -> list[MarketplaceItem]:
        """List all available skills."""
        if category:
            return [i for i in self._cache if i.category == category]
        return list(self._cache)

    def install(self, name: str) -> dict:
        """Install a skill from the marketplace."""
        item = next((i for i in self._cache if i.name == name), None)
        if not item:
            return {"status": "error", "message": f"Skill '{name}' not found in marketplace"}

        dest = os.path.join(self.skills_dir, f"{name}.py")
        os.makedirs(self.skills_dir, exist_ok=True)

        # In production, this would download from item.url
        # For now, create a placeholder
        with open(dest, "w") as f:
            f.write(f'"""{item.description}"""\n# Installed from NexusAgent Marketplace\n# Author: {item.author}\n# Version: {item.version}\n\npass\n')

        item.downloads += 1
        self._save_cache()
        return {"status": "ok", "name": name, "path": dest}

    def uninstall(self, name: str) -> dict:
        """Uninstall a skill."""
        path = os.path.join(self.skills_dir, f"{name}.py")
        if os.path.exists(path):
            os.unlink(path)
            return {"status": "ok", "name": name}
        return {"status": "error", "message": f"Skill '{name}' not found locally"}

    def rate(self, name: str, rating: int) -> dict:
        """Rate a skill (1-5 stars)."""
        if not 1 <= rating <= 5:
            return {"status": "error", "message": "Rating must be 1-5"}
        self._user_ratings[name] = rating
        item = next((i for i in self._cache if i.name == name), None)
        if item:
            item.rating_count += 1
            item.rating = round((item.rating * (item.rating_count - 1) + rating) / item.rating_count, 2)
        self._save_cache()
        return {"status": "ok", "name": name, "rating": rating}

    def get_installed(self) -> list[str]:
        """List locally installed marketplace skills."""
        if not os.path.exists(self.skills_dir):
            return []
        return [f[:-3] for f in os.listdir(self.skills_dir) if f.endswith(".py")]

    def populate_sample(self):
        """Add sample items for testing/demo."""
        samples = [
            MarketplaceItem("linter_plus", "1.2.0", "Advanced Python linter with auto-fix", "nexus-team", SkillCategory.CODE_QUALITY, ["linting", "auto-fix"], 1250, 4.5, 89),
            MarketplaceItem("csv_merger", "0.8.0", "Merge and transform CSV files intelligently", "data-tools", SkillCategory.DATA_PROCESSING, ["csv", "data", "merge"], 890, 4.2, 45),
            MarketplaceItem("docker_builder", "2.1.0", "Generate optimized Dockerfiles from projects", "devops-guru", SkillCategory.DEVOPS, ["docker", "container", "build"], 2100, 4.7, 156),
            MarketplaceItem("paper_summarizer", "1.0.0", "Summarize research papers with key findings", "research-ai", SkillCategory.RESEARCH, ["papers", "summary", "nlp"], 670, 4.0, 32),
            MarketplaceItem("api_scanner", "1.5.0", "Scan REST APIs for security vulnerabilities", "sec-tools", SkillCategory.SECURITY, ["security", "api", "scanner"], 1800, 4.8, 210),
            MarketplaceItem("web_scraper_pro", "3.0.0", "Smart web scraper with anti-detection", "web-tools", SkillCategory.WEB, ["scraping", "web", "automation"], 3200, 4.6, 278),
        ]
        self._cache = samples
        self._save_cache()
