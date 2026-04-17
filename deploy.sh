#!/bin/bash
set -e

echo "🚀 Deploying NexusAgent to GitHub..."

# Ensure we are in a git repository
if [ ! -d .git ]; then
  echo "Error: Not a git repository. Run 'git init' first."
  exit 1
fi

# Add all files and commit if there are changes
if [[ -n $(git status -s) ]]; then
    git add .
    git commit -m "Initial commit: The Dawn of NexusAgent 🧠"
fi

# Create a new public GitHub repository
echo "📦 Creating remote GitHub repository..."
gh repo create nexus-agent --public --source=. --remote=origin --description="The Zero-Config, Self-Evolving Local AI Agent Framework"

# Set GitHub topics (viral tags)
echo "🏷️ Setting repository topics..."
gh api -X PUT /repos/{owner}/{repo}/topics \
  -H "Accept: application/vnd.github.mercy-preview+json" \
  -f names='["ai", "agent", "llm", "ollama", "python", "cli", "self-evolving", "privacy", "zero-config", "graphrag"]'

# Set the homepage URL to GitHub Pages
echo "🌐 Setting repository homepage..."
USERNAME=$(gh api user -q ".login")
gh repo edit --homepage "https://${USERNAME}.github.io/nexus-agent"

# Push the code to the main branch
echo "⬆️ Pushing code to origin main..."
git push -u origin main

# Create a v1.0.0 release
echo "🎉 Creating initial release v1.0.0..."
gh release create v1.0.0 --title "NexusAgent v1.0.0: The Self-Evolving AI" --notes "First public release of NexusAgent. Includes local LLM integration via Ollama, zero-config GraphRAG memory, and beautiful CLI interface."

echo "✅ Deployment Complete! NexusAgent is now live on GitHub."
