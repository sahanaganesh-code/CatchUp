# Git Setup Guide for Team Collaboration

Follow these steps to upload CatchUp to GitHub and collaborate with your team.

---

## Step 1: Initialize Git Repository

Run these commands in your terminal:

```bash
cd /Users/sahanaganesh/catchup

# Initialize Git
git init

# Configure Git (use your actual name and email)
git config user.name "Your Name"
git config user.email "your.email@example.com"

# Check status
git status
```

---

## Step 2: Create Initial Commit

```bash
# Add all files (respects .gitignore)
git add .

# Create initial commit
git commit -m "Initial commit: CatchUp - Accessible Meeting Assistant

Health & Lifestyle Hackathon Project

Features:
- Real-time transcription (Zoom + In-person modes)
- Evidence-based Q&A with 2-5 timestamped quotes
- Auto-generated todos with priorities and due dates
- Calendar event extraction with dates/times
- Live note-taking with storage
- AI chatbot for querying all content
- Action proposals with approval gating

Tech Stack:
- Backend: FastAPI + ChromaDB + Google Gemini
- Frontend: Next.js + TypeScript + Tailwind CSS

Accessibility Focus:
- Hearing accessibility (real-time captions)
- ADHD support (structured info, auto todos)
- Cognitive support (evidence-based answers)
- Mental health (reduced stress and anxiety)"

# Verify commit
git log --oneline
```

---

## Step 3: Create GitHub Repository

### Option A: Using GitHub CLI (Recommended)

```bash
# Install GitHub CLI if you don't have it
# Mac: brew install gh
# Or download from: https://cli.github.com/

# Login to GitHub
gh auth login

# Create repository
gh repo create catchup --public --source=. --remote=origin --push

# Done! Your repo is now at: https://github.com/YOUR_USERNAME/catchup
```

### Option B: Using GitHub Website

1. Go to https://github.com/new
2. Repository name: `catchup`
3. Description: "Accessible Meeting Assistant for Health & Lifestyle - Hackathon Project"
4. Choose: **Public** (so your team can access)
5. **DO NOT** initialize with README, .gitignore, or license (we already have these)
6. Click "Create repository"

Then run these commands:

```bash
# Add GitHub as remote
git remote add origin https://github.com/YOUR_USERNAME/catchup.git

# Push to GitHub
git branch -M main
git push -u origin main
```

---

## Step 4: Invite Team Members

### On GitHub Website:

1. Go to your repository: `https://github.com/YOUR_USERNAME/catchup`
2. Click "Settings" tab
3. Click "Collaborators" in left sidebar
4. Click "Add people"
5. Enter your teammates' GitHub usernames or emails
6. They'll receive an invitation email

### Permissions:
- Give them "Write" access so they can push code
- They can create branches and pull requests

---

## Step 5: Team Members Clone Repository

Your teammates should run:

```bash
# Clone the repository
git clone https://github.com/YOUR_USERNAME/catchup.git
cd catchup

# Backend setup
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Add GEMINI_API_KEY to .env

# Frontend setup
cd ../frontend
npm install
cp .env.local.example .env.local

# Ready to work!
```

---

## Step 6: Collaboration Workflow

### Creating a Feature Branch

```bash
# Update main branch
git checkout main
git pull origin main

# Create feature branch
git checkout -b feature/your-feature-name

# Make changes, then:
git add .
git commit -m "Add: your feature description"
git push origin feature/your-feature-name

# Create pull request on GitHub
gh pr create --title "Add your feature" --body "Description of changes"
```

### Recommended Branch Names

- `feature/transcript-export` - For new features
- `fix/chatbot-bug` - For bug fixes
- `docs/update-readme` - For documentation
- `refactor/api-cleanup` - For refactoring

### Daily Workflow

```bash
# Start of day: Get latest changes
git checkout main
git pull origin main

# Create your branch
git checkout -b feature/my-work

# Work on your feature...

# Commit often
git add .
git commit -m "Progress on feature X"

# Push to GitHub
git push origin feature/my-work

# When done: Create pull request on GitHub
```

---

## Step 7: Handling Merge Conflicts

If you get merge conflicts:

```bash
# Pull latest changes
git pull origin main

# Git will show conflicting files
# Open each file and look for:
<<<<<<< HEAD
your changes
=======
their changes
>>>>>>> main

# Edit the file to keep the correct version
# Remove the conflict markers

# Mark as resolved
git add <conflicted-file>
git commit -m "Resolve merge conflicts"
git push
```

---

## Important: Protecting Sensitive Data

### ⚠️ NEVER commit these files:
- `backend/.env` (contains API keys!)
- `frontend/.env.local`
- `chroma_db/` directory
- `node_modules/` directory
- `venv/` directory

### ✅ Safe to commit:
- `backend/.env.example` (template without keys)
- `frontend/.env.local.example` (template)
- All source code files
- Documentation
- Configuration files

### If you accidentally commit API keys:

```bash
# Remove from Git history
git filter-branch --force --index-filter \
  "git rm --cached --ignore-unmatch backend/.env" \
  --prune-empty --tag-name-filter cat -- --all

# Force push (dangerous - coordinate with team!)
git push origin --force --all

# Then: Rotate your API keys immediately!
```

---

## Step 8: Team Communication

### Use GitHub Issues
Create issues for tasks:
- Go to "Issues" tab
- Click "New issue"
- Title: "Implement real Zoom integration"
- Assign to team member
- Add labels: `enhancement`, `high-priority`

### Use GitHub Projects (Optional)
- Create a project board
- Add columns: To Do, In Progress, Done
- Move issues across columns
- Great for tracking hackathon progress

---

## Quick Reference Commands

```bash
# Check status
git status

# See what changed
git diff

# See commit history
git log --oneline

# Switch branches
git checkout branch-name

# Pull latest changes
git pull origin main

# Push your changes
git push origin your-branch-name

# Create pull request
gh pr create

# See all branches
git branch -a

# Delete local branch
git branch -d branch-name

# Undo last commit (keep changes)
git reset --soft HEAD~1
```

---

## Collaboration Best Practices

### 1. Communicate
- Tell team what you're working on
- Use descriptive commit messages
- Comment on pull requests

### 2. Small Commits
- Commit often with clear messages
- Each commit should be one logical change
- Makes it easier to review and rollback

### 3. Pull Before Push
- Always `git pull` before starting work
- Reduces merge conflicts
- Keeps everyone in sync

### 4. Code Review
- Review each other's pull requests
- Test changes before merging
- Give constructive feedback

### 5. Branch Strategy
- `main` - Always working, deployable code
- `feature/*` - New features
- `fix/*` - Bug fixes
- Never commit directly to `main` (use PRs)

---

## Troubleshooting

### "Permission denied"
- Check you have write access to the repository
- Make sure you're logged in: `gh auth status`

### "Merge conflict"
- Pull latest: `git pull origin main`
- Resolve conflicts in files
- Commit resolution: `git commit -m "Resolve conflicts"`

### "Diverged branches"
- Pull with rebase: `git pull --rebase origin main`
- Or merge: `git pull origin main`

### "Can't push"
- Check remote: `git remote -v`
- Check branch: `git branch`
- Try: `git push -u origin branch-name`

---

## Team Roles (Suggested)

### Person 1: Backend
- Focus on: API endpoints, Gemini integration, database
- Files: `backend/app/*.py`

### Person 2: Frontend
- Focus on: UI components, user experience, styling
- Files: `frontend/app/components/*.tsx`

### Person 3: Integration & Testing
- Focus on: End-to-end testing, documentation, deployment
- Files: Tests, docs, configuration

---

## Next Steps

1. **You**: Run the commands in Step 1-3 to initialize and push
2. **Share**: Send GitHub repo URL to teammates
3. **Invite**: Add teammates as collaborators (Step 4)
4. **Coordinate**: Decide who works on what
5. **Hack**: Start building together!

---

## Need Help?

Run these in your terminal:

```bash
# Check if Git is initialized
cd /Users/sahanaganesh/catchup
git status

# If not initialized, run:
git init
git add .
git commit -m "Initial commit"

# Create GitHub repo and push
gh repo create catchup --public --source=. --remote=origin --push
```

Good luck with your hackathon! 🚀
