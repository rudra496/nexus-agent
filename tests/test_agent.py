"""Comprehensive tests for NexusAgent."""

import json
import os
import tempfile
import pytest

from src.agent import NexusAgent
from src.memory import GraphMemory
from src.skills import SkillTree
from src.config import NexusConfig, load_config, save_config, get_config, ModelConfig
from src.plugins import PluginManager
from src.sandbox import Sandbox, SandboxResult
from src.export import (
    export_skills_json,
    export_memory_graph,
    export_markdown_report,
    export_skill_pack,
)


# ── Fixtures ────────────────────────────────────────────────────────

@pytest.fixture
def tmp_dir():
    with tempfile.TemporaryDirectory() as d:
        yield d


@pytest.fixture
def agent(tmp_dir):
    os.chdir(tmp_dir)
    return NexusAgent(model="mock-model")


@pytest.fixture
def memory(tmp_dir):
    path = os.path.join(tmp_dir, "memory.json")
    return GraphMemory(storage_path=path)


@pytest.fixture
def skill_tree(tmp_dir):
    d = os.path.join(tmp_dir, "skills")
    return SkillTree(skill_dir=d)


@pytest.fixture
def sandbox():
    return Sandbox(timeout=5, max_memory_mb=64)


# ── Agent Tests ─────────────────────────────────────────────────────

class TestNexusAgent:
    def test_initialization(self, agent):
        assert agent.model == "mock-model"
        assert isinstance(agent.memory, GraphMemory)
        assert isinstance(agent.skill_tree, SkillTree)

    def test_offline_mode_response(self, agent):
        response = agent.execute("Hello Nexus")
        assert "Nexus Offline Mode" in response
        assert "Hello Nexus" in response

    def test_evolve_scans_files(self, agent, tmp_dir):
        # Create some dummy files
        for name in ["app.py", "README.md", "config.txt"]:
            with open(os.path.join(tmp_dir, name), "w") as f:
                f.write("# dummy")
        stats = agent.evolve()
        assert stats["nodes"] >= 3

    def test_extract_skill_from_response(self, agent):
        fake_response = '[NEW SKILL: parse_logs]\n```python\nprint("hello")\n```'
        agent._extract_and_save_skill(fake_response)
        assert "parse_logs" in agent.skill_tree.skills


# ── Memory Tests ────────────────────────────────────────────────────

class TestGraphMemory:
    def test_add_node(self, memory):
        memory.add_node("test.py", {"type": "file"})
        stats = memory.get_stats()
        assert stats["nodes"] == 1

    def test_add_edge(self, memory):
        memory.add_node("a.py", {})
        memory.add_node("b.py", {})
        memory.add_edge("a.py", "b.py", "imports")
        stats = memory.get_stats()
        assert stats["edges"] == 1

    def test_retrieve_context_empty(self, memory):
        ctx = memory.retrieve_context("nonexistent query")
        assert "No prior context" in ctx

    def test_retrieve_context_match(self, memory):
        memory.add_node("auth.py", {"type": "module", "desc": "authentication"})
        ctx = memory.retrieve_context("authentication module")
        assert "auth.py" in ctx

    def test_persistence(self, tmp_dir):
        path = os.path.join(tmp_dir, "persist.json")
        mem1 = GraphMemory(storage_path=path)
        mem1.add_node("persist_test.py", {"type": "file"})
        del mem1
        mem2 = GraphMemory(storage_path=path)
        assert mem2.get_stats()["nodes"] == 1

    def test_stats(self, memory):
        assert "nodes" in memory.get_stats()
        assert "edges" in memory.get_stats()


# ── Skill Tree Tests ────────────────────────────────────────────────

class TestSkillTree:
    def test_add_skill(self, skill_tree):
        skill_tree.add_skill("test", "A test skill", "print('hello')")
        stats = skill_tree.get_stats()
        assert stats["total_skills"] == 1

    def test_list_skills_empty(self, skill_tree):
        result = skill_tree.list_skills()
        assert "No custom skills" in result

    def test_list_skills_with_data(self, skill_tree):
        skill_tree.add_skill("csv_parser", "Parse CSV files", "import csv")
        result = skill_tree.list_skills()
        assert "csv_parser" in result

    def test_skill_persistence(self, tmp_dir):
        d = os.path.join(tmp_dir, "skills2")
        st1 = SkillTree(skill_dir=d)
        st1.add_skill("perm", "Persistent", "pass")
        st2 = SkillTree(skill_dir=d)
        assert st2.get_stats()["total_skills"] == 1


# ── Config Tests ────────────────────────────────────────────────────

class TestConfig:
    def test_default_config(self):
        cfg = NexusConfig()
        assert cfg.model.default == "ollama/llama3"
        assert cfg.memory.max_nodes == 10000
        assert cfg.skills.directory == ".nexus/skills"
        assert cfg.web.port == 8420

    def test_custom_model_config(self):
        cfg = NexusConfig(model=ModelConfig(default="ollama/phi3"))
        assert cfg.model.default == "ollama/phi3"

    def test_save_and_load_json(self, tmp_dir):
        path = os.path.join(tmp_dir, "config.json")
        cfg = NexusConfig()
        save_config(cfg, path)
        loaded = load_config(path)
        assert loaded.model.default == cfg.model.default

    def test_config_serialization(self):
        cfg = NexusConfig()
        d = cfg.model_dump()
        assert "model" in d
        assert "memory" in d
        assert "skills" in d
        assert "plugins" in d
        assert "web" in d


# ── Plugin Tests ────────────────────────────────────────────────────

class TestPlugins:
    def test_plugin_manager_init(self):
        pm = PluginManager()
        assert len(pm.plugins) == 0

    def test_load_plugin(self, tmp_dir):
        plugin_dir = os.path.join(tmp_dir, "plugins")
        os.makedirs(plugin_dir)
        plugin_file = os.path.join(plugin_dir, "hello.py")
        with open(plugin_file, "w") as f:
            f.write("def nexus_on_task(task): return f'handled: {task}'\n")
        pm = PluginManager()
        # Temporarily override plugin dir
        from src.config import get_config
        cfg = get_config()
        cfg.plugins.directory = plugin_dir
        pm.load_all()
        assert "hello" in pm.plugins
        assert "nexus_on_task" in pm.plugins["hello"].hooks

    def test_call_hook(self, tmp_dir):
        plugin_dir = os.path.join(tmp_dir, "plugins2")
        os.makedirs(plugin_dir)
        plugin_file = os.path.join(plugin_dir, "echo.py")
        with open(plugin_file, "w") as f:
            f.write("def nexus_echo(msg): return msg.upper()\n")
        pm = PluginManager()
        from src.config import get_config
        cfg = get_config()
        cfg.plugins.directory = plugin_dir
        pm.load_all()
        results = pm.call_hook("nexus_echo", "hello")
        assert "HELLO" in results[0]

    def test_list_plugins(self):
        pm = PluginManager()
        result = pm.list_plugins()
        assert isinstance(result, list)


# ── Sandbox Tests ───────────────────────────────────────────────────

class TestSandbox:
    def test_execute_python(self, sandbox):
        result = sandbox.execute("print('hello world')")
        assert result.success
        assert "hello world" in result.stdout

    def test_execute_error(self, sandbox):
        result = sandbox.execute("raise ValueError('test error')")
        assert not result.success
        assert "test error" in result.stderr

    def test_timeout(self):
        sb = Sandbox(timeout=1)
        result = sb.execute("import time; time.sleep(10)")
        assert result.timed_out

    def test_unsupported_language(self, sandbox):
        result = sandbox.execute("console.log('hi')", language="javascript")
        assert not result.success
        assert "Unsupported" in result.stderr

    def test_sandbox_result_repr(self):
        ok = SandboxResult("out", "err", 0)
        assert "OK" in repr(ok)
        fail = SandboxResult("out", "err", 1)
        assert "ERR" in repr(fail)
        timeout = SandboxResult("", "", -1, timed_out=True)
        assert "TIMEOUT" in repr(timeout)


# ── Export Tests ────────────────────────────────────────────────────

class TestExport:
    def test_export_skills_json(self, agent):
        agent.skill_tree.add_skill("test_exp", "desc", "pass")
        result = export_skills_json(agent)
        data = json.loads(result)
        assert len(data) == 1
        assert data[0]["name"] == "test_exp"

    def test_export_skills_to_file(self, agent, tmp_dir):
        agent.skill_tree.add_skill("file_test", "desc", "pass")
        path = os.path.join(tmp_dir, "skills.json")
        export_skills_json(agent, output=path)
        assert os.path.exists(path)

    def test_export_memory_graph(self, agent):
        agent.memory.add_node("test.py", {})
        result = export_memory_graph(agent)
        data = json.loads(result)
        assert len(data["nodes"]) == 1

    def test_export_markdown_report(self, agent):
        result = export_markdown_report(agent)
        assert "# NexusAgent Report" in result
        assert "Memory Graph" in result

    def test_export_skill_pack(self, agent, tmp_dir):
        agent.skill_tree.add_skill("pack_skill", "desc", "print('pack')")
        path = os.path.join(tmp_dir, "pack.zip")
        output = export_skill_pack(agent, output=path)
        assert os.path.exists(output)
        assert os.path.getsize(output) > 0
