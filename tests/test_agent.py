"""Comprehensive tests for NexusAgent."""

import json
import os
import tempfile
import pytest

from src.agent import NexusAgent
from src.memory import GraphMemory
from src.skills import SkillTree
from src.config import NexusConfig, load_config, save_config, get_config, ModelConfig, PluginConfig
from src.plugins import PluginManager
from src.sandbox import Sandbox, SandboxResult
from src.export import (
    export_skills_json,
    export_memory_graph,
    export_markdown_report,
    export_skill_pack,
)
from src.multi_agent import (
    AgentRole,
    AgentConfig,
    Task,
    AgentMessage,
    CollaborativeMemory,
    SubAgent,
    AgentOrchestrator,
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


@pytest.fixture
def collab_memory(tmp_dir):
    return CollaborativeMemory(storage_path=os.path.join(tmp_dir, "collab.json"))


@pytest.fixture
def orchestrator(tmp_dir):
    os.chdir(tmp_dir)
    return AgentOrchestrator()


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
        assert memory.get_stats()["nodes"] == 1

    def test_add_edge(self, memory):
        memory.add_node("a.py", {})
        memory.add_node("b.py", {})
        memory.add_edge("a.py", "b.py", "imports")
        assert memory.get_stats()["edges"] == 1

    def test_retrieve_context_empty(self, memory):
        assert "No prior context" in memory.retrieve_context("nonexistent")

    def test_retrieve_context_match(self, memory):
        memory.add_node("auth.py", {"type": "module", "desc": "authentication"})
        assert "auth.py" in memory.retrieve_context("authentication module")

    def test_persistence(self, tmp_dir):
        path = os.path.join(tmp_dir, "persist.json")
        mem1 = GraphMemory(storage_path=path)
        mem1.add_node("persist_test.py", {"type": "file"})
        del mem1
        mem2 = GraphMemory(storage_path=path)
        assert mem2.get_stats()["nodes"] == 1


# ── Skill Tree Tests ────────────────────────────────────────────────

class TestSkillTree:
    def test_add_skill(self, skill_tree):
        skill_tree.add_skill("test", "A test skill", "print('hello')")
        assert skill_tree.get_stats()["total_skills"] == 1

    def test_list_skills_empty(self, skill_tree):
        assert "No custom skills" in skill_tree.list_skills()

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
        assert cfg.web.port == 8420

    def test_custom_model(self):
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
        assert "model" in d and "memory" in d


# ── Plugin Tests ────────────────────────────────────────────────────

class TestPlugins:
    def test_plugin_manager_init(self):
        pm = PluginManager()
        assert len(pm.plugins) == 0

    def test_load_plugin(self, tmp_dir):
        plugin_dir = os.path.join(tmp_dir, "plugins")
        os.makedirs(plugin_dir)
        with open(os.path.join(plugin_dir, "hello.py"), "w") as f:
            f.write("def nexus_on_task(task): return f'handled: {task}'\n")
        pm = PluginManager()
        pm._config = NexusConfig(plugins=PluginConfig(directory=plugin_dir))
        pm.load_all()
        assert "hello" in pm.plugins

    def test_call_hook(self, tmp_dir):
        plugin_dir = os.path.join(tmp_dir, "plugins2")
        os.makedirs(plugin_dir)
        with open(os.path.join(plugin_dir, "echo.py"), "w") as f:
            f.write("def nexus_echo(msg): return msg.upper()\n")
        pm = PluginManager()
        pm._config = NexusConfig(plugins=PluginConfig(directory=plugin_dir))
        pm.load_all()
        results = pm.call_hook("nexus_echo", "hello")
        assert "HELLO" in results[0]

    def test_list_plugins(self):
        assert isinstance(PluginManager().list_plugins(), list)


# ── Sandbox Tests ───────────────────────────────────────────────────

class TestSandbox:
    def test_execute_python(self, sandbox):
        result = sandbox.execute("print('hello world')")
        assert result.success and "hello world" in result.stdout

    def test_execute_error(self, sandbox):
        result = sandbox.execute("raise ValueError('test')")
        assert not result.success and "test" in result.stderr

    def test_timeout(self):
        result = Sandbox(timeout=1).execute("import time; time.sleep(10)")
        assert result.timed_out

    def test_unsupported_language(self, sandbox):
        result = sandbox.execute("console.log('hi')", language="javascript")
        assert "Unsupported" in result.stderr

    def test_result_repr(self):
        assert "OK" in repr(SandboxResult("out", "err", 0))
        assert "TIMEOUT" in repr(SandboxResult("", "", -1, timed_out=True))


# ── Export Tests ────────────────────────────────────────────────────

class TestExport:
    def test_export_skills_json(self, agent):
        agent.skill_tree.add_skill("test", "desc", "pass")
        data = json.loads(export_skills_json(agent))
        assert data[0]["name"] == "test"

    def test_export_memory_graph(self, agent):
        agent.memory.add_node("test.py", {})
        data = json.loads(export_memory_graph(agent))
        assert len(data["nodes"]) == 1

    def test_export_markdown_report(self, agent):
        assert "# NexusAgent Report" in export_markdown_report(agent)

    def test_export_skill_pack(self, agent, tmp_dir):
        agent.skill_tree.add_skill("pack", "desc", "print('x')")
        path = os.path.join(tmp_dir, "pack.zip")
        output = export_skill_pack(agent, output=path)
        assert os.path.exists(output) and os.path.getsize(output) > 0


# ── Multi-Agent Tests ──────────────────────────────────────────────

class TestMultiAgent:
    def test_register_agent(self, orchestrator):
        agent = orchestrator.register_agent("coder", AgentConfig(role=AgentRole.CODER))
        assert "coder" in orchestrator.agents
        assert agent.config.role == AgentRole.CODER

    def test_register_multiple_agents(self, orchestrator):
        orchestrator.register_agent("agent1")
        orchestrator.register_agent("agent2")
        orchestrator.register_agent("agent3")
        assert len(orchestrator.agents) == 3

    def test_submit_task(self, orchestrator):
        task = orchestrator.submit_task("Write a test", priority=1)
        assert task.status == "pending"
        assert task.priority == 1
        assert len(orchestrator.task_queue) == 1

    def test_route_task_to_specific_agent(self, orchestrator):
        orchestrator.register_agent("coder", AgentConfig(role=AgentRole.CODER))
        task = orchestrator.submit_task("Fix bug", target_agent="coder")
        routed = orchestrator.route_task(task)
        assert routed.name == "coder"

    def test_route_task_to_role(self, orchestrator):
        orchestrator.register_agent("reviewer", AgentConfig(role=AgentRole.REVIEWER))
        task = orchestrator.submit_task("Review code", role=AgentRole.REVIEWER)
        routed = orchestrator.route_task(task)
        assert routed.config.role == AgentRole.REVIEWER

    def test_route_task_load_balancing(self, orchestrator):
        orchestrator.register_agent("agent1")
        orchestrator.register_agent("agent2")
        task = orchestrator.submit_task("Generic task")
        routed = orchestrator.route_task(task)
        assert routed.name in orchestrator.agents

    def test_execute_task_offline(self, orchestrator):
        orchestrator.register_agent("worker")
        task = orchestrator.submit_task("Do something")
        result = orchestrator.execute_task(task)
        assert result.status == "completed" or result.status == "failed"
        assert result.assigned_to == "worker"

    def test_run_all_tasks(self, orchestrator):
        orchestrator.register_agent("worker")
        orchestrator.submit_task("Task 1")
        orchestrator.submit_task("Task 2")
        results = orchestrator.run_all()
        assert len(results) == 2

    def test_broadcast_message(self, orchestrator):
        orchestrator.register_agent("agent1")
        orchestrator.register_agent("agent2")
        orchestrator.broadcast("system", "Hello all")
        assert len(orchestrator.message_bus) == 1
        assert len(orchestrator.agents["agent1"].inbox) == 1
        assert len(orchestrator.agents["agent2"].inbox) == 1

    def test_direct_message(self, orchestrator):
        orchestrator.register_agent("agent1")
        orchestrator.register_agent("agent2")
        orchestrator.send_message("agent1", "agent2", "Direct msg")
        assert len(orchestrator.agents["agent2"].inbox) == 1
        assert orchestrator.agents["agent2"].inbox[0].content == "Direct msg"

    def test_orchestrator_status(self, orchestrator):
        orchestrator.register_agent("coder", AgentConfig(role=AgentRole.CODER))
        orchestrator.register_agent("reviewer", AgentConfig(role=AgentRole.REVIEWER))
        status = orchestrator.get_status()
        assert "coder" in status["agents"]
        assert "reviewer" in status["agents"]
        assert status["tasks"]["pending"] == 0


# ── Collaborative Memory Tests ─────────────────────────────────────

class TestCollaborativeMemory:
    def test_set_and_get(self, collab_memory):
        collab_memory.set("project_name", "NexusAgent")
        assert collab_memory.get("project_name") == "NexusAgent"

    def test_get_default(self, collab_memory):
        assert collab_memory.get("nonexistent") is None
        assert collab_memory.get("nonexistent", "default") == "default"

    def test_shared_node(self, collab_memory):
        collab_memory.add_shared_node("shared_file.py", {"type": "file"})
        stats = collab_memory.get_stats()
        assert stats["graph_nodes"] == 1

    def test_persistence(self, tmp_dir):
        path = os.path.join(tmp_dir, "collab2.json")
        mem1 = CollaborativeMemory(storage_path=path)
        mem1.set("key1", "value1")
        mem2 = CollaborativeMemory(storage_path=path)
        assert mem2.get("key1") == "value1"


# ── Agent Message Tests ────────────────────────────────────────────

class TestAgentMessage:
    def test_message_creation(self):
        msg = AgentMessage("agent1", "Hello", "info", "agent2")
        assert msg.sender == "agent1"
        assert msg.target == "agent2"

    def test_message_serialization(self):
        msg = AgentMessage("agent1", "Test", "info")
        d = msg.to_dict()
        assert d["sender"] == "agent1"
        assert d["type"] == "info"
        assert "timestamp" in d

    def test_broadcast_message(self):
        msg = AgentMessage("system", "Alert", "info")
        assert msg.target is None


# ── Task Tests ──────────────────────────────────────────────────────

class TestTask:
    def test_task_creation(self):
        task = Task(prompt="Do something", priority=3)
        assert task.status == "pending"
        assert task.priority == 3
        assert len(task.id) == 8

    def test_task_default_priority(self):
        task = Task(prompt="Test")
        assert task.priority == 5


# ── Voice Tests ─────────────────────────────────────────────────────

class TestVoice:
    def test_voice_config_defaults(self):
        from src.voice import VoiceConfig, STTEngine, TTSEngine
        cfg = VoiceConfig()
        assert cfg.stt_engine == STTEngine.MOCK
        assert cfg.tts_engine == TTSEngine.MOCK
        assert cfg.language == "en"

    def test_mock_stt(self):
        from src.voice import SpeechToText, VoiceConfig, STTEngine
        stt = SpeechToText(VoiceConfig(stt_engine=STTEngine.MOCK))
        result = stt.transcribe_file("nonexistent.wav")
        assert "mock" in result.text

    def test_mock_tts(self):
        from src.voice import TextToSpeech, VoiceConfig, TTSEngine
        tts = TextToSpeech(VoiceConfig(tts_engine=TTSEngine.MOCK))
        assert tts.speak("hello") is None

    def test_transcription_result(self):
        from src.voice import TranscriptionResult
        r = TranscriptionResult(text="hello world", language="en", confidence=0.95)
        assert r.text == "hello world"
        assert "hello" in repr(r)

    def test_voice_interface(self):
        from src.voice import VoiceInterface, VoiceConfig, STTEngine, TTSEngine
        vi = VoiceInterface(VoiceConfig(stt_engine=STTEngine.MOCK, tts_engine=TTSEngine.MOCK))
        assert vi.config.language == "en"


# ── AST Memory Tests ───────────────────────────────────────────────

class TestASTMemory:
    def test_parse_file(self, tmp_dir):
        from src.ast_memory import ASTParser
        f = os.path.join(tmp_dir, "test.py")
        with open(f, "w") as fh:
            fh.write("def hello(name):\n    return f'Hello {name}'\n\nclass Foo:\n    def bar(self):\n        pass\n")
        parser = ASTParser()
        analysis = parser.parse_file(f)
        assert analysis is not None
        assert len(analysis.functions) == 1
        assert analysis.functions[0].name == "hello"
        assert len(analysis.classes) == 1
        assert analysis.classes[0].name == "Foo"

    def test_parse_imports(self, tmp_dir):
        from src.ast_memory import ASTParser
        f = os.path.join(tmp_dir, "test2.py")
        with open(f, "w") as fh:
            fh.write("import os\nfrom pathlib import Path\nimport json\n")
        parser = ASTParser()
        analysis = parser.parse_file(f)
        assert len(analysis.imports) == 3
        assert analysis.imports[0].is_from is False
        assert analysis.imports[1].is_from is True

    def test_parse_async_function(self, tmp_dir):
        from src.ast_memory import ASTParser
        f = os.path.join(tmp_dir, "test3.py")
        with open(f, "w") as fh:
            fh.write("async def fetch():\n    pass\n")
        parser = ASTParser()
        analysis = parser.parse_file(f)
        assert analysis.functions[0].is_async is True

    def test_get_function_signature(self, tmp_dir):
        from src.ast_memory import ASTParser
        f = os.path.join(tmp_dir, "test4.py")
        with open(f, "w") as fh:
            fh.write("def add(a, b) -> int:\n    return a + b\n")
        parser = ASTParser()
        sig = parser.get_function_signature(f, "add")
        assert "add(a, b)" in sig
        assert "-> int" in sig

    def test_dependency_graph(self, tmp_dir):
        from src.ast_memory import ASTParser
        f1 = os.path.join(tmp_dir, "mod_a.py")
        f2 = os.path.join(tmp_dir, "mod_b.py")
        with open(f1, "w") as fh:
            fh.write("")
        with open(f2, "w") as fh:
            fh.write("import mod_a\n")
        parser = ASTParser()
        deps = parser.get_dependency_graph([f1, f2])
        assert f2 in deps
        assert f1 in deps[f2]

    def test_search_symbols(self, tmp_dir):
        from src.ast_memory import ASTParser
        f = os.path.join(tmp_dir, "test5.py")
        with open(f, "w") as fh:
            fh.write("def my_function():\n    pass\nclass MyClass:\n    pass\n")
        parser = ASTParser()
        results = parser.search_symbols([f], "my")
        assert len(results) == 2

    def test_parse_invalid_syntax(self, tmp_dir):
        from src.ast_memory import ASTParser
        f = os.path.join(tmp_dir, "bad.py")
        with open(f, "w") as fh:
            fh.write("def broken(\n")
        parser = ASTParser()
        assert parser.parse_file(f) is None

    def test_cache(self, tmp_dir):
        from src.ast_memory import ASTParser
        f = os.path.join(tmp_dir, "cached.py")
        with open(f, "w") as fh:
            fh.write("x = 1\n")
        parser = ASTParser()
        parser.parse_file(f)
        assert parser.get_stats()["files_cached"] == 1
        parser.clear_cache()
        assert parser.get_stats()["files_cached"] == 0


# ── Context Manager Tests ──────────────────────────────────────────

class TestContextManager:
    def test_token_counter(self):
        from src.context_manager import TokenCounter
        tc = TokenCounter()
        assert tc.count("hello world") > 0
        assert tc.count("") == 0

    def test_context_budget(self):
        from src.context_manager import ContextBudget
        b = ContextBudget(total_tokens=1000, system_prompt=200)
        assert b.total_tokens == 1000

    def test_add_messages(self):
        from src.context_manager import ContextWindowManager
        cm = ContextWindowManager()
        cm.add_message("user", "hello")
        cm.add_message("assistant", "hi there")
        assert len(cm._conversation_history) == 2

    def test_set_system_prompt(self):
        from src.context_manager import ContextWindowManager
        cm = ContextWindowManager()
        cm.set_system_prompt("You are Nexus.")
        assert "Nexus" in cm._system_prompt

    def test_truncate_conversation(self):
        from src.context_manager import ContextWindowManager
        cm = ContextWindowManager()
        for i in range(100):
            cm.add_message("user", f"message {i}")
        cm.truncate_conversation(max_tokens=50)
        assert len(cm._conversation_history) < 100

    def test_select_context(self):
        from src.context_manager import ContextWindowManager, ContextEntry
        cm = ContextWindowManager()
        entries = [
            ContextEntry(content="important context", source="memory", priority=1, tokens=50),
            ContextEntry(content="less important", source="memory", priority=8, tokens=100),
        ]
        selected = cm.select_context(entries)
        assert len(selected) >= 1

    def test_usage_stats(self):
        from src.context_manager import ContextWindowManager
        cm = ContextWindowManager()
        stats = cm.get_usage_stats()
        assert "total_budget" in stats
        assert "conversation_messages" in stats

    def test_build_context_messages(self):
        from src.context_manager import ContextWindowManager, ContextEntry
        cm = ContextWindowManager()
        cm.set_system_prompt("You are Nexus.")
        cm.add_message("user", "hello")
        entries = [ContextEntry(content="context info", source="memory", priority=1, tokens=20)]
        msgs = cm.build_context_messages(entries)
        assert msgs[0]["role"] == "system"


# ── IDE Tests ───────────────────────────────────────────────────────

class TestIDE:
    def test_ide_config_defaults(self):
        from src.ide import IDEConfig, IDEType
        cfg = IDEConfig()
        assert cfg.ide_type == IDEType.GENERIC
        assert cfg.port == 8421

    def test_jsonrpc_handler(self):
        from src.ide import IDEServer
        server = IDEServer()
        server.register_handler("test/hello", lambda params: f"hello {params.get('name', 'world')}")
        result = server.handle_request({"method": "test/hello", "params": {"name": "nexus"}, "id": 1})
        assert result["result"] == "hello nexus"

    def test_jsonrpc_unknown_method(self):
        from src.ide import IDEServer
        server = IDEServer()
        result = server.handle_request({"method": "unknown", "id": 1})
        assert "error" in result

    def test_code_action(self):
        from src.ide import CodeAction
        action = CodeAction(title="Fix import", kind="quickfix")
        assert action.title == "Fix import"

    def test_diagnostic(self):
        from src.ide import Diagnostic
        d = Diagnostic(file="test.py", line=10, column=5, severity="error", message="unused var")
        assert d.severity == "error"

    def test_completion_item(self):
        from src.ide import CompletionItem
        item = CompletionItem(label="my_func", kind=3, detail="function")
        assert item.label == "my_func"

    def test_vscode_manifest(self):
        from src.ide import generate_vscode_extensionManifest
        manifest = generate_vscode_extensionManifest()
        assert manifest["name"] == "nexus-agent"
        assert len(manifest["contributes"]["commands"]) == 4

    def test_ide_client_init(self):
        from src.ide import IDEClient
        client = IDEClient("127.0.0.1", 9999)
        assert client.port == 9999
