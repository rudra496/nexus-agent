"""NexusAgent — The Zero-Config, Self-Evolving Local AI Agent Framework."""

__version__ = "1.0.0"

from src.agent import NexusAgent
from src.config import NexusConfig, load_config, save_config
from src.memory import GraphMemory
from src.skills import SkillTree
from src.plugins import PluginManager
from src.sandbox import Sandbox

__all__ = [
    "NexusAgent",
    "NexusConfig",
    "load_config",
    "save_config",
    "GraphMemory",
    "SkillTree",
    "PluginManager",
    "Sandbox",
]
