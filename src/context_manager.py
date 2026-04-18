"""
NexusAgent Context Window Manager
Intelligently manages LLM context by selecting the most relevant code, memory,
and conversation history to fit within token limits.
"""

import tiktoken
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class ContextEntry:
    content: str
    source: str  # e.g., "memory", "skill", "code", "conversation"
    priority: int = 5  # 1 (highest) to 10 (lowest)
    tokens: int = 0


@dataclass
class ContextBudget:
    total_tokens: int = 4096
    system_prompt: int = 500
    memory: int = 800
    skills: int = 600
    code_context: int = 1200
    conversation: int = 800
    response_reserve: int = 200

    def validate(self):
        allocated = self.system_prompt + self.memory + self.skills + self.code_context + self.conversation + self.response_reserve
        if allocated > self.total_tokens:
            raise ValueError(f"Budget overallocated: {allocated} > {total}")


class TokenCounter:
    """Count tokens using tiktoken (cl100k_base for GPT-like models)."""

    def __init__(self, model: str = "cl100k_base"):
        try:
            self._encoding = tiktoken.get_encoding(model)
        except Exception:
            self._encoding = None

    def count(self, text: str) -> int:
        if self._encoding:
            return len(self._encoding.encode(text))
        # Fallback: rough estimate (~4 chars per token)
        return len(text) // 4

    def count_messages(self, messages: List[Dict[str, str]]) -> int:
        return sum(self.count(m.get("content", "")) for m in messages)


class ContextWindowManager:
    """Manages what goes into the LLM context window."""

    def __init__(self, budget: Optional[ContextBudget] = None, model: str = "cl100k_base"):
        self.budget = budget or ContextBudget()
        self.counter = TokenCounter(model)
        self._conversation_history: List[Dict[str, str]] = []
        self._system_prompt: str = ""

    def set_system_prompt(self, prompt: str):
        tokens = self.counter.count(prompt)
        if tokens > self.budget.system_prompt:
            self._system_prompt = prompt[:self.budget.system_prompt * 4]  # rough truncation
        else:
            self._system_prompt = prompt

    def add_message(self, role: str, content: str):
        self._conversation_history.append({"role": role, "content": content})

    def add_conversation(self, messages: List[Dict[str, str]]):
        self._conversation_history.extend(messages)

    def get_conversation_budget_remaining(self) -> int:
        used = self.counter.count_messages(self._conversation_history)
        return max(0, self.budget.conversation - used)

    def truncate_conversation(self, max_tokens: Optional[int] = None):
        """Keep the most recent messages that fit within the token budget."""
        max_tok = max_tokens or self.budget.conversation
        truncated = []
        total = 0
        for msg in reversed(self._conversation_history):
            tokens = self.counter.count(msg["content"])
            if total + tokens > max_tok:
                break
            truncated.insert(0, msg)
            total += tokens
        self._conversation_history = truncated

    def select_context(self, candidates: List[ContextEntry]) -> List[ContextEntry]:
        """Select context entries that fit within budget, prioritized by priority and relevance."""
        budget_map = {
            "memory": self.budget.memory,
            "skill": self.budget.skills,
            "code": self.budget.code_context,
            "conversation": self.budget.conversation,
        }

        # Group by source and track used tokens
        used_by_source: Dict[str, int] = {}
        selected = []

        # Sort by priority (lower = higher priority)
        sorted_candidates = sorted(candidates, key=lambda c: c.priority)

        for entry in sorted_candidates:
            source_key = entry.source.split(".")[0]  # "memory.graph" -> "memory"
            budget = budget_map.get(source_key, 500)
            used = used_by_source.get(source_key, 0)

            if used + entry.tokens <= budget:
                selected.append(entry)
                used_by_source[source_key] = used + entry.tokens

        return selected

    def build_context_messages(self, candidates: List[ContextEntry]) -> List[Dict[str, str]]:
        """Build the full message list for the LLM."""
        selected = self.select_context(candidates)

        messages = []
        if self._system_prompt:
            messages.append({"role": "system", "content": self._system_prompt})

        # Add selected context
        context_parts = []
        for entry in selected:
            context_parts.append(f"[{entry.source}] {entry.content}")

        if context_parts:
            context_text = "\n\n".join(context_parts)
            messages.append({"role": "system", "content": f"Context:\n{context_text}"})

        # Add conversation (truncate if needed)
        self.truncate_conversation()
        messages.extend(self._conversation_history)

        return messages

    def get_usage_stats(self) -> Dict[str, Any]:
        conv_tokens = self.counter.count_messages(self._conversation_history)
        system_tokens = self.counter.count(self._system_prompt)
        return {
            "system_prompt_tokens": system_tokens,
            "conversation_tokens": conv_tokens,
            "conversation_messages": len(self._conversation_history),
            "total_budget": self.budget.total_tokens,
            "available_for_context": self.budget.total_tokens - system_tokens - conv_tokens - self.budget.response_reserve,
        }
