import litellm
import os
from .memory import GraphMemory
from .skills import SkillTree

class NexusAgent:
    """
    Core AI orchestrator. Handles local models via LiteLLM, 
    persistent state via GraphRAG memory, and dynamic tool creation.
    """
    def __init__(self, model="ollama/llama3"):
        self.model = model
        self.memory = GraphMemory()
        self.skill_tree = SkillTree()
        # Disable verbose litellm logs to keep CLI clean
        litellm.set_verbose = False
        
    def execute(self, prompt: str) -> str:
        """
        Takes a prompt, retrieves relevant GraphRAG context, passes to local LLM,
        and automatically identifies if new skills should be memorized.
        """
        context = self.memory.retrieve_context(prompt)
        skills = self.skill_tree.list_skills()

        system_prompt = f"""You are Nexus, an advanced, self-evolving local AI agent.
Your core principles: Absolute privacy (you run locally) and self-evolution (you write your own tools).

Here is your current knowledge graph context related to the user's query:
{context}

Here are the custom skills you have developed so far:
{skills}

If the user's request requires a tool you do not have, write a short, robust Python snippet to solve it, and prefix it with [NEW SKILL: skill_name].
"""
        try:
            # Main execution call
            response = litellm.completion(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                api_base="http://localhost:11434" if "ollama" in self.model else None,
                max_tokens=1024,
            )
            content = response.choices[0].message.content

            # Naive evolution mechanism: Parse response for new skills to memorize
            if "[NEW SKILL:" in content:
                self._extract_and_save_skill(content)

            return content
        except Exception as e:
            # Fallback gracefully for demonstration if the local model daemon isn't running
            return (
                f"**Nexus Offline Mode:**\n\n"
                f"I received your prompt: `{prompt}`\n\n"
                f"Context loaded from GraphRAG: `{context}`\n"
                f"Skills loaded: `{len(self.skill_tree.skills)}`\n\n"
                f"_Note: Could not connect to {self.model}. Is Ollama running? Error: {str(e)[:150]}_"
            )

    def _extract_and_save_skill(self, content: str):
        """
        Parses LLM output for '[NEW SKILL: name]' and saves the code snippet to the Skill Tree.
        """
        import re
        import textwrap

        # Extremely naive parser for demonstration
        match = re.search(r"\[NEW SKILL:\s*([\w_]+)\]", content)
        if match:
            skill_name = match.group(1)
            code_block = re.search(r"```python\s*(.*?)\s*```", content, re.DOTALL)
            
            if code_block:
                code_snippet = textwrap.dedent(code_block.group(1))
                self.skill_tree.add_skill(
                    name=skill_name, 
                    description="Automatically generated skill during runtime.", 
                    code_snippet=code_snippet
                )
                
    def evolve(self):
        """
        Forces the agent to scan the current directory and populate the GraphRAG memory.
        """
        for root, dirs, files in os.walk("."):
            if ".git" in root or ".nexus" in root:
                continue
            for file in files:
                if file.endswith((".py", ".md", ".txt")):
                    filepath = os.path.join(root, file)
                    self.memory.add_node(filepath, {"type": "file", "path": filepath})
                    
        return self.memory.get_stats()
