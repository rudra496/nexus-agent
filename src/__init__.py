"""NexusAgent — The Zero-Config, Self-Evolving Local AI Agent Framework."""

__version__ = "1.0.0"

import sys
import typing

# Compatibility polyfill for Python <3.11 where NotRequired lives in typing_extensions
if sys.version_info < (3, 11):
    try:
        import typing_extensions
        if not hasattr(typing, "NotRequired"):
            typing.NotRequired = typing_extensions.NotRequired
    except ImportError:
        pass

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
