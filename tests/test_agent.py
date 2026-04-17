import pytest
from src.agent import NexusAgent

def test_nexus_initialization():
    agent = NexusAgent(model="mock-model")
    assert agent.model == "mock-model"

def test_nexus_fallback_response():
    agent = NexusAgent(model="mock-model")
    response = agent.execute("Hello Nexus")
    assert "Nexus Offline Mode" in response
    assert "Hello Nexus" in response
