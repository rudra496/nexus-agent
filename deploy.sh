#!/bin/bash
set -e

echo "🚀 Deploying NexusAgent..."

# Install dependencies
pip install -e ".[all]"

# Run tests
pytest tests/ -v

# Build docs
echo "📦 Building documentation..."

# Stage and status
git add -A
git status

echo "✅ Ready to commit and push!"
echo "Run: git commit -m 'your message' && git push"
