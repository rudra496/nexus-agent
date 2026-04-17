"""
NexusAgent Plugin System
Load external plugins from .nexus/plugins/, with hot-reload support.
"""

import importlib.util
import os
import time
from pathlib import Path
from typing import Any, Callable, Optional

from .config import get_config


class Plugin:
    def __init__(self, name: str, path: Path, module: Any):
        self.name = name
        self.path = path
        self.module = module
        self.loaded_at = time.time()
        self.hooks: dict[str, Callable] = {}

        # Auto-discover hooks
        for attr in dir(module):
            if attr.startswith("nexus_") and callable(getattr(module, attr)):
                self.hooks[attr] = getattr(module, attr)


class PluginManager:
    def __init__(self):
        self.plugins: dict[str, Plugin] = {}
        self._mtimes: dict[str, float] = {}
        self._config = get_config()

    @property
    def plugin_dir(self) -> Path:
        return Path(self._config.plugins.directory)

    def load_all(self):
        """Load all plugins from the plugin directory."""
        self.plugin_dir.mkdir(parents=True, exist_ok=True)
        for f in self.plugin_dir.iterdir():
            if f.suffix == ".py" and not f.name.startswith("_"):
                self.load_plugin(f)

    def load_plugin(self, path: Path) -> Optional[Plugin]:
        """Load a single plugin from a .py file."""
        name = path.stem
        try:
            spec = importlib.util.spec_from_file_location(f"nexus_plugin_{name}", path)
            if spec and spec.loader:
                mod = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(mod)
                plugin = Plugin(name=name, path=path, module=mod)
                self.plugins[name] = plugin
                self._mtimes[name] = path.stat().st_mtime
                return plugin
        except Exception as e:
            print(f"[Plugin] Failed to load {name}: {e}")
        return None

    def unload_plugin(self, name: str):
        """Unload a plugin by name."""
        self.plugins.pop(name, None)
        self._mtimes.pop(name, None)

    def hot_reload(self) -> list[str]:
        """Check for changed plugins and reload them. Returns list of reloaded plugin names."""
        if not self._config.plugins.hot_reload:
            return []
        reloaded = []
        for name, plugin in list(self.plugins.items()):
            if plugin.path.exists():
                mtime = plugin.path.stat().st_mtime
                if mtime != self._mtimes.get(name):
                    self.unload_plugin(name)
                    if self.load_plugin(plugin.path):
                        reloaded.append(name)
        return reloaded

    def call_hook(self, hook_name: str, *args, **kwargs) -> list[Any]:
        """Call a hook across all plugins, return list of results."""
        results = []
        for plugin in self.plugins.values():
            fn = plugin.hooks.get(hook_name)
            if fn:
                try:
                    results.append(fn(*args, **kwargs))
                except Exception as e:
                    print(f"[Plugin] Hook {hook_name} failed in {plugin.name}: {e}")
        return results

    def list_plugins(self) -> list[dict]:
        """Return info about all loaded plugins."""
        return [
            {"name": p.name, "path": str(p.path), "hooks": list(p.hooks.keys()), "loaded_at": p.loaded_at}
            for p in self.plugins.values()
        ]
