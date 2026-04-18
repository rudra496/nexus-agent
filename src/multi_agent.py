"""
NexusAgent Multi-Agent Orchestration
Multi-agent task delegation, routing, collaborative memory, and communication protocol.
"""

import json
import os
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from .agent import NexusAgent
from .memory import GraphMemory


class AgentRole(Enum):
    CODER = "coder"
    REVIEWER = "reviewer"
    TESTER = "tester"
    PLANNER = "planner"
    RESEARCHER = "researcher"
    GENERAL = "general"


@dataclass
class AgentConfig:
    role: AgentRole = AgentRole.GENERAL
    model: str = "ollama/llama3"
    max_tokens: int = 1024
    priority: int = 5  # 1 (highest) to 10 (lowest)


@dataclass
class Task:
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    prompt: str = ""
    status: str = "pending"  # pending, assigned, in_progress, completed, failed
    result: Optional[str] = None
    assigned_to: Optional[str] = None
    priority: int = 5
    created_at: float = field(default_factory=time.time)
    completed_at: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class AgentMessage:
    """Message for inter-agent communication."""

    def __init__(self, sender: str, content: str, msg_type: str = "info", target: Optional[str] = None):
        self.id = str(uuid.uuid4())[:8]
        self.sender = sender
        self.content = content
        self.msg_type = msg_type  # info, task_result, request, error
        self.target = target  # None = broadcast
        self.timestamp = time.time()

    def to_dict(self) -> dict:
        return {"id": self.id, "sender": self.sender, "content": self.content,
                "type": self.msg_type, "target": self.target, "timestamp": self.timestamp}


class CollaborativeMemory:
    """Shared memory accessible by multiple agents."""

    def __init__(self, storage_path: str = ".nexus/collaborative_memory.json"):
        self.storage_path = storage_path
        self.graph = GraphMemory(storage_path=storage_path)
        self._shared_state: Dict[str, Any] = {}
        self._load_state()

    def _load_state(self):
        path = Path(self.storage_path).parent / "collaborative_state.json"
        if path.exists():
            try:
                self._shared_state = json.loads(path.read_text())
            except Exception:
                self._shared_state = {}

    def _save_state(self):
        path = Path(self.storage_path).parent / "collaborative_state.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self._shared_state, indent=2))

    def set(self, key: str, value: Any):
        self._shared_state[key] = {"value": value, "updated_at": time.time()}
        self._save_state()

    def get(self, key: str, default=None) -> Any:
        entry = self._shared_state.get(key)
        return entry["value"] if entry else default

    def add_shared_node(self, node_id: str, attributes: Dict[str, Any]):
        self.graph.add_node(node_id, {**attributes, "shared": True})

    def get_stats(self) -> dict:
        return {
            "shared_variables": len(self._shared_state),
            "graph_nodes": self.graph.get_stats()["nodes"],
            "graph_edges": self.graph.get_stats()["edges"],
        }


class SubAgent:
    """A specialized agent within the multi-agent system."""

    def __init__(self, name: str, config: AgentConfig, shared_memory: CollaborativeMemory):
        self.name = name
        self.config = config
        self.shared_memory = shared_memory
        self.agent = NexusAgent(model=config.model)
        self.completed_tasks: List[str] = []
        self.inbox: List[AgentMessage] = []

    def execute(self, task: Task) -> str:
        """Execute a task using the underlying agent."""
        system_context = f"You are a {self.config.role.value} agent named {self.name}. "
        system_context += f"Shared context: {self.shared_memory.get('context', 'None')}\n"
        system_context += f"Previously completed: {', '.join(self.completed_tasks[-5:])}\n"

        # Inject shared context into the prompt
        enhanced_prompt = f"{system_context}\nTask: {task.prompt}"
        result = self.agent.execute(enhanced_prompt)
        self.completed_tasks.append(task.id)
        return result


class AgentOrchestrator:
    """Orchestrates multiple agents for task delegation and routing."""

    def __init__(self):
        self.agents: Dict[str, SubAgent] = {}
        self.shared_memory = CollaborativeMemory()
        self.task_queue: List[Task] = []
        self.message_bus: List[AgentMessage] = []
        self._hooks: Dict[str, List[Callable]] = {}

    def register_agent(self, name: str, config: Optional[AgentConfig] = None) -> SubAgent:
        """Register a new agent."""
        config = config or AgentConfig()
        agent = SubAgent(name=name, config=config, shared_memory=self.shared_memory)
        self.agents[name] = agent
        return agent

    def submit_task(self, prompt: str, priority: int = 5, target_agent: Optional[str] = None,
                    role: Optional[AgentRole] = None) -> Task:
        """Submit a task to the queue."""
        task = Task(prompt=prompt, priority=priority)
        if target_agent and target_agent in self.agents:
            task.assigned_to = target_agent
        elif role:
            task.metadata["preferred_role"] = role.value
        self.task_queue.append(task)
        self.task_queue.sort(key=lambda t: t.priority)
        return task

    def route_task(self, task: Task) -> Optional[SubAgent]:
        """Route a task to the best available agent."""
        if task.assigned_to and task.assigned_to in self.agents:
            return self.agents[task.assigned_to]

        preferred_role = task.metadata.get("preferred_role")
        if preferred_role:
            for name, agent in self.agents.items():
                if agent.config.role.value == preferred_role:
                    return agent

        # Route to the agent with the fewest completed tasks (load balancing)
        available = [(n, a) for n, a in self.agents.items() if len(a.completed_tasks) < 100]
        if not available:
            available = list(self.agents.items())
        if not available:
            return None

        available.sort(key=lambda x: len(x[1].completed_tasks))
        return available[0][1]

    def execute_task(self, task: Task) -> Task:
        """Execute a single task."""
        agent = self.route_task(task)
        if not agent:
            task.status = "failed"
            task.result = "No available agent to handle this task."
            return task

        task.assigned_to = agent.name
        task.status = "in_progress"
        self._broadcast(AgentMessage("orchestrator", f"Task {task.id} assigned to {agent.name}", "info"))

        try:
            result = agent.execute(task)
            task.result = result
            task.status = "completed"
            task.completed_at = time.time()
            self._broadcast(AgentMessage(agent.name, f"Completed task {task.id}", "task_result"))
        except Exception as e:
            task.status = "failed"
            task.result = str(e)
            self._broadcast(AgentMessage(agent.name, f"Failed task {task.id}: {e}", "error"))

        return task

    def run_all(self) -> List[Task]:
        """Execute all pending tasks in the queue."""
        results = []
        for task in list(self.task_queue):
            if task.status == "pending":
                results.append(self.execute_task(task))
        return results

    def broadcast(self, sender: str, content: str, msg_type: str = "info"):
        """Send a message to all agents."""
        msg = AgentMessage(sender, content, msg_type)
        self._broadcast(msg)

    def send_message(self, sender: str, target: str, content: str, msg_type: str = "info"):
        """Send a direct message to a specific agent."""
        msg = AgentMessage(sender, content, msg_type, target=target)
        if target in self.agents:
            self.agents[target].inbox.append(msg)
        self.message_bus.append(msg)

    def _broadcast(self, msg: AgentMessage):
        self.message_bus.append(msg)
        for agent in self.agents.values():
            agent.inbox.append(msg)

    def get_status(self) -> dict:
        """Get orchestrator status."""
        pending = sum(1 for t in self.task_queue if t.status == "pending")
        completed = sum(1 for t in self.task_queue if t.status == "completed")
        failed = sum(1 for t in self.task_queue if t.status == "failed")
        return {
            "agents": {name: {"role": a.config.role.value, "tasks_completed": len(a.completed_tasks)}
                       for name, a in self.agents.items()},
            "tasks": {"pending": pending, "completed": completed, "failed": failed, "total": len(self.task_queue)},
            "shared_memory": self.shared_memory.get_stats(),
            "messages": len(self.message_bus),
        }
