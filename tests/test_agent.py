import pytest
from src.agent import NexusAgent
from src.memory import GraphMemory
from src.skills import SkillTree
import os

def test_nexus_initialization():
    agent = NexusAgent(model="mock-model")
    assert agent.model == "mock-model"
    assert isinstance(agent.memory, GraphMemory)
    assert isinstance(agent.skill_tree, SkillTree)

def test_nexus_fallback_response():
    agent = NexusAgent(model="mock-model")
    response = agent.execute("Hello Nexus")
    assert "Nexus Offline Mode" in response
    assert "Hello Nexus" in response

def test_memory_add_node():
    mem = GraphMemory(storage_path=".nexus/test_memory.json")
    mem.add_node("test_file.py", {"type": "file"})
    stats = mem.get_stats()
    assert stats["nodes"] >= 1
    if os.path.exists(".nexus/test_memory.json"):
        os.remove(".nexus/test_memory.json")

def test_skill_tree_add():
    st = SkillTree(skill_dir=".nexus/test_skills")
    st.add_skill("test_skill", "A test", "print('hello')")
    stats = st.get_stats()
    assert stats["total_skills"] >= 1
    if os.path.exists(".nexus/test_skills/test_skill.json"):
        os.remove(".nexus/test_skills/test_skill.json")
