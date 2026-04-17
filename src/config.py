"""
NexusAgent Configuration Management
Supports YAML/JSON config files, model selection, memory limits, skill directories, and custom system prompts.
"""

import json
import os
from pathlib import Path
from typing import Any, Optional

try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False

from pydantic import BaseModel, Field


DEFAULT_CONFIG_DIR = Path.home() / ".nexus"
DEFAULT_CONFIG_FILE = DEFAULT_CONFIG_DIR / "config.yaml"


class ModelConfig(BaseModel):
    default: str = "ollama/llama3"
    fallback: Optional[str] = None
    max_tokens: int = 2048
    temperature: float = 0.7
    api_base: Optional[str] = "http://localhost:11434"


class MemoryConfig(BaseModel):
    max_nodes: int = 10000
    max_edges: int = 50000
    persistence_file: str = ".nexus/memory/graph.pkl"
    auto_save: bool = True
    context_retrieval_limit: int = 5


class SkillConfig(BaseModel):
    directory: str = ".nexus/skills"
    auto_evolve: bool = True
    sandbox_enabled: bool = True
    timeout_seconds: int = 30


class PluginConfig(BaseModel):
    directory: str = ".nexus/plugins"
    hot_reload: bool = True
    allowed_extensions: list[str] = Field(default_factory=lambda: [".py", ".toml"])


class WebConfig(BaseModel):
    enabled: bool = False
    host: str = "127.0.0.1"
    port: int = 8420


class NexusConfig(BaseModel):
    model: ModelConfig = Field(default_factory=ModelConfig)
    memory: MemoryConfig = Field(default_factory=MemoryConfig)
    skills: SkillConfig = Field(default_factory=SkillConfig)
    plugins: PluginConfig = Field(default_factory=PluginConfig)
    web: WebConfig = Field(default_factory=WebConfig)
    system_prompt: Optional[str] = None
    version: str = "0.2.0"


def load_config(path: Optional[str] = None) -> NexusConfig:
    """Load configuration from YAML or JSON file."""
    config_path = Path(path) if path else DEFAULT_CONFIG_FILE

    if not config_path.exists():
        DEFAULT_CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        cfg = NexusConfig()
        save_config(cfg, config_path)
        return cfg

    raw = config_path.read_text(encoding="utf-8")
    suffix = config_path.suffix.lower()

    if suffix in (".yaml", ".yml") and HAS_YAML:
        data = yaml.safe_load(raw) or {}
    elif suffix == ".json":
        data = json.loads(raw)
    else:
        # Fallback: try JSON then YAML
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            if HAS_YAML:
                data = yaml.safe_load(raw) or {}
            else:
                data = {}

    return NexusConfig(**data)


def save_config(config: NexusConfig, path: Optional[str] = None):
    """Save configuration to file."""
    config_path = Path(path) if path else DEFAULT_CONFIG_FILE
    config_path.parent.mkdir(parents=True, exist_ok=True)

    data = config.model_dump(exclude_none=True)
    suffix = config_path.suffix.lower()

    if suffix in (".yaml", ".yml") and HAS_YAML:
        config_path.write_text(yaml.dump(data, default_flow_style=False, sort_keys=False), encoding="utf-8")
    else:
        config_path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def get_config() -> NexusConfig:
    """Get or create default config."""
    return load_config()
