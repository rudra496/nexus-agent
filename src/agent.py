import litellm
import os

class NexusAgent:
    def __init__(self, model="ollama/llama3"):
        self.model = model
        # Disable logging for cleaner CLI output
        litellm.set_verbose = False
        
    def execute(self, prompt: str) -> str:
        """
        Executes a task using the local model.
        Falls back to a mock response if Ollama is not running.
        """
        try:
            # We assume Ollama is running locally for the 'viral' local AI pitch.
            response = litellm.completion(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are Nexus, an advanced, self-evolving local AI agent."},
                    {"role": "user", "content": prompt}
                ],
                api_base="http://localhost:11434" if "ollama" in self.model else None,
                max_tokens=1024,
            )
            return response.choices[0].message.content
        except Exception as e:
            # Fallback for demo purposes when local Ollama is not installed
            return f"**Nexus Offline Mode:** I received your prompt: `{prompt}`.\n\n_Note: Could not connect to {self.model}. Is Ollama running? Error: {str(e)[:100]}_"