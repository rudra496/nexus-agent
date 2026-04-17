@echo off
echo Deploying NexusAgent...

pip install -e ".[all]"
pytest tests/ -v

git add -A
git status

echo Ready to commit and push!
echo Run: git commit -m "your message" ^&^& git push
