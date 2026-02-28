# Quick Commands Reference

## 🚀 For You (Project Owner)

### Set Up Git and Push to GitHub

```bash
cd /Users/sahanaganesh/catchup

# Initialize Git
git init
git config user.name "Your Name"
git config user.email "your.email@example.com"

# Stage all files
git add .

# Create initial commit
git commit -m "Initial commit: CatchUp - Accessible Meeting Assistant"

# Create GitHub repo and push (using GitHub CLI)
gh auth login
gh repo create catchup --public --source=. --remote=origin --push

# OR manually create repo on GitHub, then:
git remote add origin https://github.com/YOUR_USERNAME/catchup.git
git branch -M main
git push -u origin main
```

### Share with Team

1. Go to: https://github.com/YOUR_USERNAME/catchup
2. Click "Settings" → "Collaborators"
3. Click "Add people"
4. Enter teammates' GitHub usernames
5. Send them the repo URL

---

## 👥 For Teammates

### Clone and Setup

```bash
# Clone repository
git clone https://github.com/YOUR_USERNAME/catchup.git
cd catchup

# Backend setup
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env and add GEMINI_API_KEY

# Frontend setup
cd ../frontend
npm install
cp .env.local.example .env.local
```

### Run the App

```bash
# Terminal 1: Backend
cd backend
source venv/bin/activate
python -m uvicorn app.main:app --reload

# Terminal 2: Frontend
cd frontend
npm run dev

# Browser: http://localhost:3000
```

---

## 💻 Daily Development

### Start Working

```bash
# Get latest code
git checkout main
git pull origin main

# Create feature branch
git checkout -b feature/my-feature

# Make changes...
```

### Commit and Push

```bash
# Check what changed
git status
git diff

# Stage changes
git add .

# Commit
git commit -m "Add: description of changes"

# Push to GitHub
git push origin feature/my-feature

# Create pull request
gh pr create
# OR go to GitHub and click "Compare & pull request"
```

### Update Your Branch

```bash
# Get latest from main
git checkout main
git pull origin main

# Go back to your branch
git checkout feature/my-feature

# Merge latest changes
git merge main

# Or rebase (cleaner history)
git rebase main
```

---

## 🔧 Useful Commands

```bash
# See commit history
git log --oneline --graph

# See all branches
git branch -a

# Switch branches
git checkout branch-name

# Delete local branch
git branch -d branch-name

# Undo last commit (keep changes)
git reset --soft HEAD~1

# Discard all local changes
git reset --hard HEAD

# See who changed what
git blame filename

# Search commits
git log --grep="keyword"
```

---

## 🚨 Emergency Commands

### Accidentally Committed API Key

```bash
# Remove file from Git (keeps local copy)
git rm --cached backend/.env

# Commit the removal
git commit -m "Remove .env from Git"

# Push
git push origin main

# IMPORTANT: Rotate your API key immediately!
```

### Need to Undo Last Push

```bash
# Revert last commit (creates new commit)
git revert HEAD
git push origin main

# OR reset (dangerous - coordinate with team!)
git reset --hard HEAD~1
git push --force origin main
```

### Merge Conflict

```bash
# Pull latest
git pull origin main

# Git shows conflicting files
# Open each file, look for:
# <<<<<<< HEAD
# your changes
# =======
# their changes
# >>>>>>> main

# Edit to keep correct version, remove markers

# Mark as resolved
git add .
git commit -m "Resolve merge conflicts"
git push
```

---

## 📦 Dependency Management

### Backend (Python)

```bash
# Add new package
pip install package-name

# Update requirements.txt
pip freeze > requirements.txt

# Commit
git add requirements.txt
git commit -m "Add: package-name dependency"
```

### Frontend (Node)

```bash
# Add new package
npm install package-name

# Commit (package.json and package-lock.json)
git add package.json package-lock.json
git commit -m "Add: package-name dependency"
```

---

## 🎯 Feature Branch Naming

```bash
feature/transcript-export      # New feature
fix/chatbot-crash             # Bug fix
docs/update-readme            # Documentation
refactor/api-cleanup          # Code refactoring
test/add-unit-tests           # Tests
style/improve-ui              # UI/styling
```

---

## 🔍 Code Review Checklist

Before creating pull request:
- [ ] Code runs without errors
- [ ] Tests pass
- [ ] No console errors
- [ ] Follows project style
- [ ] Documentation updated
- [ ] No API keys committed
- [ ] Commit messages are clear

---

## 🏃 Quick Start (Copy-Paste)

### For Project Owner
```bash
cd /Users/sahanaganesh/catchup
git init
git add .
git commit -m "Initial commit: CatchUp"
gh repo create catchup --public --source=. --remote=origin --push
```

### For Teammates
```bash
git clone https://github.com/USERNAME/catchup.git
cd catchup
cd backend && python -m venv venv && source venv/bin/activate && pip install -r requirements.txt && cp .env.example .env
cd ../frontend && npm install && cp .env.local.example .env.local
```

---

## 📞 Need Help?

- **Git Issues**: See GIT_SETUP_GUIDE.md
- **Project Setup**: See TEAM_SETUP.md
- **Features**: See README.md
- **Demo**: See DEMO_SCRIPT.md

---

**Happy collaborating!** 🎉
