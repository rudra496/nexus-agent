@echo off
echo ===================================================
echo 🚀 Deploying NexusAgent to GitHub (Windows Version)
echo ===================================================

echo.
echo 1. Checking if inside a git repository...
if not exist .git (
    git init
)

echo.
echo 2. Adding and committing files...
git add .
git commit -m "Initial commit: The Dawn of NexusAgent 🧠"

echo.
echo 3. Creating remote GitHub repository...
gh repo create nexus-agent --public --source=. --remote=origin --description="The Zero-Config, Self-Evolving Local AI Agent Framework"

echo.
echo 4. Pushing code to origin main...
git branch -M main
git push -u origin main

echo.
echo 5. Setting repository topics...
for /f "tokens=*" %%i in ('gh api user -q ".login"') do set GITHUB_USER=%%i
gh api -X PUT /repos/%GITHUB_USER%/nexus-agent/topics -H "Accept: application/vnd.github.mercy-preview+json" -f names="[\"ai\", \"agent\", \"llm\", \"ollama\", \"python\", \"cli\", \"self-evolving\", \"privacy\", \"zero-config\", \"graphrag\"]"

echo.
echo 6. Setting repository homepage...
gh repo edit --homepage "https://%GITHUB_USER%.github.io/nexus-agent"

echo.
echo 7. Creating initial release v1.0.0...
gh release create v1.0.0 --title "NexusAgent v1.0.0: The Self-Evolving AI" --notes "First public release of NexusAgent. Includes local LLM integration via Ollama, zero-config GraphRAG memory, and beautiful CLI interface."

echo.
echo ===================================================
echo ✅ Deployment Complete! NexusAgent is now live.
echo ===================================================
pause
