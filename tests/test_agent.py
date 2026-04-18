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


# ── Cloud Sync Tests ──────────────────────────────────────────────

class TestCloudSync:
    def test_sync_config_defaults(self):
        from src.cloud_sync import SyncConfig, SyncTarget, ConflictStrategy
        cfg = SyncConfig()
        assert cfg.target == SyncTarget.LOCAL
        assert cfg.conflict_strategy == ConflictStrategy.LAST_WRITE_WINS

    def test_manifest_serialization(self):
        from src.cloud_sync import SyncManifest
        m = SyncManifest(files={"test.py": {"hash": "abc123", "mtime": 1000, "size": 100}})
        j = m.to_json()
        m2 = SyncManifest.from_json(j)
        assert m2.files["test.py"]["hash"] == "abc123"

    def test_cloud_sync_push(self, tmp_dir):
        from src.cloud_sync import CloudSync, SyncConfig
        src_dir = os.path.join(tmp_dir, "src")
        os.makedirs(src_dir)
        with open(os.path.join(src_dir, "test.py"), "w") as f:
            f.write("print('hello')")
        dest = os.path.join(tmp_dir, "dest")
        cfg = SyncConfig(target_path=dest, source_dirs=[src_dir])
        sync = CloudSync(cfg)
        result = sync.push()
        assert result["status"] == "ok"
        assert result["synced"] >= 1

    def test_cloud_sync_pull(self, tmp_dir):
        from src.cloud_sync import CloudSync, SyncConfig
        dest = os.path.join(tmp_dir, "dest")
        os.makedirs(dest)
        with open(os.path.join(dest, "test.py"), "w") as f:
            f.write("pulled")
        cfg = SyncConfig(target_path=dest)
        sync = CloudSync(cfg)
        result = sync.pull()
        assert result["status"] == "ok"

    def test_cloud_sync_status(self, tmp_dir):
        from src.cloud_sync import CloudSync, SyncConfig
        cfg = SyncConfig(target_path=os.path.join(tmp_dir, "dest"))
        sync = CloudSync(cfg)
        status = sync.status()
        assert status["target"] == "local"
        assert "changed_files" in status

    def test_cloud_sync_no_target(self):
        from src.cloud_sync import CloudSync, SyncConfig
        sync = CloudSync(SyncConfig(target_path=""))
        assert sync.push()["status"] == "error"

    def test_file_hash(self, tmp_dir):
        from src.cloud_sync import _file_hash
        fp = os.path.join(tmp_dir, "h.txt")
        with open(fp, "w") as f:
            f.write("test content")
        h = _file_hash(fp)
        assert len(h) == 16

    def test_delta_sync(self, tmp_dir):
        from src.cloud_sync import CloudSync, SyncConfig
        src = os.path.join(tmp_dir, "src")
        os.makedirs(src)
        with open(os.path.join(src, "a.py"), "w") as f:
            f.write("a")
        dest = os.path.join(tmp_dir, "dest")
        cfg = SyncConfig(target_path=dest, source_dirs=[src])
        sync = CloudSync(cfg)
        sync.push()
        # Second push should have 0 changed
        r2 = sync.push()
        assert r2["synced"] == 0


# ── Audit & RBAC Tests ────────────────────────────────────────────

class TestAudit:
    def test_audit_entry_serialization(self):
        from src.audit import AuditEntry, LogLevel
        e = AuditEntry(timestamp=1000, level=LogLevel.INFO, action="test_action", actor="user1")
        j = e.to_json()
        e2 = AuditEntry.from_json(j)
        assert e2.level == LogLevel.INFO
        assert e2.action == "test_action"

    def test_audit_logger_file(self, tmp_dir):
        from src.audit import AuditLogger, LogLevel
        log_path = os.path.join(tmp_dir, "audit.log")
        logger = AuditLogger(log_path=log_path)
        logger.info("test_event", actor="bot")
        entries = logger.read_logs()
        assert len(entries) == 1
        assert entries[0].action == "test_event"

    def test_audit_logger_filter_by_level(self, tmp_dir):
        from src.audit import AuditLogger, LogLevel
        log_path = os.path.join(tmp_dir, "audit2.log")
        logger = AuditLogger(log_path=log_path)
        logger.info("info_event")
        logger.error("error_event")
        assert len(logger.read_logs(level=LogLevel.ERROR)) == 1

    def test_audit_stats(self, tmp_dir):
        from src.audit import AuditLogger, LogLevel
        log_path = os.path.join(tmp_dir, "audit3.log")
        logger = AuditLogger(log_path=log_path)
        logger.info("a")
        logger.error("b")
        logger.security("c")
        stats = logger.stats()
        assert stats["total"] == 3
        assert stats["security"] == 1

    def test_rbac_user_permissions(self):
        from src.audit import RBACUser, Role, Permission
        admin = RBACUser("admin", Role.ADMIN)
        viewer = RBACUser("viewer", Role.VIEWER)
        assert admin.has_permission(Permission.MANAGE)
        assert not viewer.has_permission(Permission.WRITE)
        assert viewer.has_permission(Permission.READ)

    def test_rbac_manager(self):
        from src.audit import RBACManager, Role, Permission
        mgr = RBACManager()
        mgr.add_user("alice", Role.ADMIN)
        mgr.add_user("bob", Role.VIEWER)
        assert mgr.check_permission("alice", Permission.MANAGE)
        assert not mgr.check_permission("bob", Permission.WRITE)
        assert not mgr.check_permission("unknown", Permission.READ)
        users = mgr.list_users()
        assert len(users) == 2

    def test_rbac_remove_user(self):
        from src.audit import RBACManager, Role
        mgr = RBACManager()
        mgr.add_user("temp", Role.USER)
        mgr.remove_user("temp")
        assert len(mgr.list_users()) == 0


# ── Marketplace Tests ─────────────────────────────────────────────

class TestMarketplace:
    def test_marketplace_item(self):
        from src.marketplace import MarketplaceItem, SkillCategory
        item = MarketplaceItem("test", "1.0", "desc", "author", SkillCategory.WEB, ["tag"])
        d = item.to_dict()
        item2 = MarketplaceItem.from_dict(d)
        assert item2.name == "test"
        assert item2.category == SkillCategory.WEB

    def test_marketplace_search(self, tmp_dir):
        from src.marketplace import MarketplaceClient, SkillCategory
        cache_dir = os.path.join(tmp_dir, "cache")
        client = MarketplaceClient(skills_dir=cache_dir)
        client.populate_sample()
        results = client.search("docker")
        assert len(results) >= 1
        assert any("docker" in r.name.lower() for r in results)

    def test_marketplace_search_by_category(self, tmp_dir):
        from src.marketplace import MarketplaceClient, SkillCategory
        client = MarketplaceClient(skills_dir=os.path.join(tmp_dir, "mp"))
        client.populate_sample()
        results = client.list_all(category=SkillCategory.SECURITY)
        assert all(r.category == SkillCategory.SECURITY for r in results)

    def test_marketplace_install(self, tmp_dir):
        from src.marketplace import MarketplaceClient
        skills_dir = os.path.join(tmp_dir, "skills")
        client = MarketplaceClient(skills_dir=skills_dir)
        client.populate_sample()
        result = client.install("linter_plus")
        assert result["status"] == "ok"
        assert os.path.exists(os.path.join(skills_dir, "linter_plus.py"))

    def test_marketplace_install_not_found(self, tmp_dir):
        from src.marketplace import MarketplaceClient
        client = MarketplaceClient(skills_dir=os.path.join(tmp_dir, "s"))
        result = client.install("nonexistent")
        assert result["status"] == "error"

    def test_marketplace_uninstall(self, tmp_dir):
        from src.marketplace import MarketplaceClient
        skills_dir = os.path.join(tmp_dir, "s")
        os.makedirs(skills_dir)
        with open(os.path.join(skills_dir, "rem.py"), "w") as f:
            f.write("pass")
        client = MarketplaceClient(skills_dir=skills_dir)
        result = client.uninstall("rem")
        assert result["status"] == "ok"
        assert not os.path.exists(os.path.join(skills_dir, "rem.py"))

    def test_marketplace_rate(self, tmp_dir):
        from src.marketplace import MarketplaceClient
        client = MarketplaceClient(skills_dir=os.path.join(tmp_dir, "s"))
        client.populate_sample()
        result = client.rate("linter_plus", 5)
        assert result["status"] == "ok"
        item = client.search("linter_plus")[0]
        assert item.rating > 0

    def test_marketplace_invalid_rating(self, tmp_dir):
        from src.marketplace import MarketplaceClient
        client = MarketplaceClient(skills_dir=os.path.join(tmp_dir, "s"))
        result = client.rate("anything", 10)
        assert result["status"] == "error"

    def test_marketplace_get_installed(self, tmp_dir):
        from src.marketplace import MarketplaceClient
        skills_dir = os.path.join(tmp_dir, "s")
        os.makedirs(skills_dir)
        with open(os.path.join(skills_dir, "a.py"), "w") as f:
            f.write("pass")
        client = MarketplaceClient(skills_dir=skills_dir)
        assert "a" in client.get_installed()


# ── Benchmarks Tests ──────────────────────────────────────────────

class TestBenchmarks:
    def test_benchmark_result(self):
        from src.benchmarks import BenchmarkResult
        r = BenchmarkResult(name="test", wall_time_s=0.123, memory_mb=5.0, iterations=10)
        d = r.to_dict()
        r2 = BenchmarkResult.from_dict(d)
        assert r2.name == "test"
        assert r2.wall_time_s == 0.123

    def test_benchmark_suite(self):
        from src.benchmarks import BenchmarkSuite, BenchmarkResult
        suite = BenchmarkSuite(name="test", timestamp=1000, results=[
            BenchmarkResult(name="a", wall_time_s=0.1),
            BenchmarkResult(name="b", wall_time_s=0.2),
        ])
        j = suite.to_json()
        suite2 = BenchmarkSuite.from_dict(json.loads(j))
        assert len(suite2.results) == 2

    def test_benchmark_markdown(self):
        from src.benchmarks import BenchmarkSuite, BenchmarkResult
        suite = BenchmarkSuite(name="test", timestamp=time.time(), results=[
            BenchmarkResult(name="mem", wall_time_s=0.05, memory_mb=2.0),
        ])
        md = suite.to_markdown()
        assert "mem" in md
        assert "0.05" in md

    def test_benchmark_memory_retrieval(self):
        from src.benchmarks import BenchmarkRunner
        runner = BenchmarkRunner()
        result = runner.benchmark_memory_retrieval(iterations=10)
        assert result.success
        assert result.wall_time_s > 0

    def test_benchmark_skill_execution(self):
        from src.benchmarks import BenchmarkRunner
        runner = BenchmarkRunner()
        result = runner.benchmark_skill_execution(iterations=10)
        assert result.success

    def test_benchmark_context_building(self):
        from src.benchmarks import BenchmarkRunner
        runner = BenchmarkRunner()
        result = runner.benchmark_context_building(iterations=10)
        assert result.success

    def test_benchmark_ast_parsing(self):
        from src.benchmarks import BenchmarkRunner
        runner = BenchmarkRunner()
        result = runner.benchmark_ast_parsing(iterations=10)
        assert result.success

    def test_benchmark_save_and_compare(self, tmp_dir):
        from src.benchmarks import BenchmarkRunner, BenchmarkSuite, BenchmarkResult
        runner = BenchmarkRunner()
        runner.RESULTS_DIR = tmp_dir
        suite = BenchmarkSuite(name="test", timestamp=1000, results=[
            BenchmarkResult(name="a", wall_time_s=0.1),
        ])
        path = runner.save_results(suite, "run1.json")
        assert os.path.exists(path)
        suite2 = BenchmarkSuite(name="test", timestamp=2000, results=[
            BenchmarkResult(name="a", wall_time_s=0.05),
        ])
        path2 = runner.save_results(suite2, "run2.json")
        md = runner.compare(path, path2)
        assert "a" in md
        assert "%" in md


# ── Mobile API Tests ──────────────────────────────────────────────

class TestMobile:
    def test_mobile_config_defaults(self):
        from src.mobile import MobileConfig
        cfg = MobileConfig()
        assert cfg.port == 8430
        assert cfg.host == "0.0.0.0"

    def test_jwt_generation_and_verification(self):
        from src.mobile import _generate_jwt, _verify_jwt
        token = _generate_jwt({"sub": "test", "exp": time.time() + 3600}, "secret")
        data = _verify_jwt(token, "secret")
        assert data is not None
        assert data["sub"] == "test"

    def test_jwt_expired(self):
        from src.mobile import _generate_jwt, _verify_jwt
        token = _generate_jwt({"sub": "test", "exp": time.time() - 10}, "secret")
        data = _verify_jwt(token, "secret")
        assert data is None

    def test_password_hash(self):
        from src.mobile import _hash_password
        h = _hash_password("password")
        assert h != "password"
        assert _hash_password("password") == h

    def test_mobile_api_authenticate(self):
        from src.mobile import MobileAPI
        api = MobileAPI()
        api.add_user("testuser", "testpass")
        token = api.authenticate("testuser", "testpass")
        assert token is not None
        assert api.verify_token(token) == "testuser"
        assert api.authenticate("testuser", "wrong") is None

    def test_mobile_api_submit_task(self):
        from src.mobile import MobileAPI
        api = MobileAPI()
        task = api.submit_task("Do something")
        assert task.status == "pending"
        tasks = api.get_tasks()
        assert len(tasks) == 1

    def test_mobile_api_status(self):
        from src.mobile import MobileAPI
        api = MobileAPI()
        status = api.get_status()
        assert "status" in status
        assert "tasks" in status

    def test_mobile_api_build_app(self):
        from src.mobile import MobileAPI
        api = MobileAPI()
        try:
            app = api.build_app()
            assert app is not None
        except ImportError:
            pass  # fastapi not installed

    def test_task_status_dataclass(self):
        from src.mobile import TaskStatus
        t = TaskStatus(id="abc", prompt="test")
        assert t.status == "pending"
        t.status = "completed"
        t.result = "done"
        assert t.result == "done"
