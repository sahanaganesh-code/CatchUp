# Team Workflow - Avoiding Merge Conflicts

## 🎯 Work Division Strategy (3 People)

### Person 1: Backend Developer
**Files to Own:**
- `backend/app/rag.py` - Q&A logic
- `backend/app/actions.py` - Action proposals
- `backend/app/content_manager.py` - Notes/todos/events
- `backend/app/chatbot.py` - AI chatbot
- `backend/app/gemini_client.py` - Gemini integration

**Tasks:**
- Improve AI accuracy
- Add real Zoom/STT integration
- Optimize vector search
- Add more API endpoints

**Branch naming:** `backend/feature-name`

---

### Person 2: Frontend Developer
**Files to Own:**
- `frontend/app/components/TranscriptViewer.tsx`
- `frontend/app/components/TodoPanel.tsx`
- `frontend/app/components/CalendarPanel.tsx`
- `frontend/app/components/NotesPanel.tsx`
- `frontend/app/components/AIChatbot.tsx`
- `frontend/app/globals.css` - Styling

**Tasks:**
- Improve UI/UX design
- Add animations
- Mobile responsiveness
- Accessibility features

**Branch naming:** `frontend/feature-name`

---

### Person 3: Integration & Infrastructure
**Files to Own:**
- `backend/app/main.py` - API routes (coordinate with Person 1)
- `backend/app/store.py` - Database
- `frontend/app/lib/api.ts` - API client (coordinate with Person 2)
- All documentation files
- Configuration files
- Tests

**Tasks:**
- Write tests
- Update documentation
- Set up deployment
- Integration testing
- Bug fixes

**Branch naming:** `integration/feature-name` or `docs/feature-name`

---

## 🚫 Files to AVOID Editing Simultaneously

### High Conflict Risk (Coordinate Before Editing)
- `backend/app/main.py` - API routes (Person 1 & 3 coordinate)
- `backend/app/models.py` - Data models (Person 1 & 3 coordinate)
- `frontend/app/lib/api.ts` - API client (Person 2 & 3 coordinate)
- `frontend/app/components/ZoomMode.tsx` - Layout (Person 2 owns)
- `frontend/app/components/InPersonMode.tsx` - Layout (Person 2 owns)

### Safe to Edit Anytime (Low Conflict Risk)
- Individual component files (each person owns different ones)
- Documentation files (different docs per person)
- Test files (each person writes their own)
- New files (no conflicts if creating new)

---

## 📋 Daily Workflow (Prevents Conflicts)

### Morning Standup (5 minutes)
Everyone shares:
1. What file(s) will you work on today?
2. Any files you need to edit that others might touch?
3. When will you push your changes?

**Rule:** If two people need to edit the same file, coordinate timing!

### Work Session
```bash
# Start of day
git checkout main
git pull origin main

# Create your branch
git checkout -b backend/improve-rag  # or frontend/improve-ui

# Work on YOUR files only
# Commit frequently to your branch

# End of session - push your branch
git add .
git commit -m "Progress on feature X"
git push origin backend/improve-rag
```

### End of Day
- Create pull request
- Ask teammate to review
- Merge when approved
- Others pull latest main

---

## 🔄 Recommended Git Workflow

### Option 1: Feature Branches (Recommended for Hackathon)

```
main (always working)
  ├── backend/zoom-integration (Person 1)
  ├── frontend/ui-polish (Person 2)
  └── integration/tests (Person 3)
```

**Process:**
1. Each person works on their branch
2. Push frequently to their branch
3. Create PR when feature is done
4. Others review and approve
5. Merge to main
6. Everyone pulls latest main

**Pros:** Clean history, easy to review, safe
**Cons:** Slightly slower (need reviews)

### Option 2: Direct to Main (Faster but Riskier)

```bash
# Only if you're working on DIFFERENT files
git checkout main
git pull origin main
# Make changes to YOUR files
git add .
git commit -m "Update: my changes"
git pull origin main  # Get others' changes
git push origin main
```

**Pros:** Faster, simpler
**Cons:** More conflicts if not careful

**Use this only if:**
- You're editing completely different files
- You coordinate who edits what
- You pull before every push

---

## 🎯 Specific Task Assignments

### Person 1: Backend Features
**Week 1 Tasks:**
- [ ] Improve todo extraction accuracy
- [ ] Improve calendar event extraction
- [ ] Add real Zoom RTMS integration
- [ ] Optimize Gemini prompts

**Files:** `backend/app/rag.py`, `backend/app/content_manager.py`

**Branch:** `backend/improvements`

### Person 2: Frontend Polish
**Week 1 Tasks:**
- [ ] Improve UI design and colors
- [ ] Add loading animations
- [ ] Mobile responsive design
- [ ] Accessibility improvements (keyboard nav)

**Files:** `frontend/app/components/*.tsx`, `frontend/app/globals.css`

**Branch:** `frontend/ui-polish`

### Person 3: Testing & Docs
**Week 1 Tasks:**
- [ ] Write comprehensive tests
- [ ] Update documentation
- [ ] Set up deployment
- [ ] Create demo video

**Files:** `backend/test_*.py`, `*.md` files, deployment configs

**Branch:** `integration/testing`

---

## 🚨 Merge Conflict Prevention Rules

### Rule 1: Own Your Files
- Each person "owns" specific files
- Don't edit others' files without asking
- Create new files instead of modifying shared ones

### Rule 2: Communicate Before Editing Shared Files
**Shared files that need coordination:**
- `backend/app/main.py` - API routes
- `backend/app/models.py` - Data models
- `frontend/app/lib/api.ts` - API client

**Before editing, post in team chat:**
> "I need to add a new API endpoint to main.py. Anyone else working on it?"

### Rule 3: Pull Before Push
```bash
# ALWAYS do this before pushing
git pull origin main

# If conflicts, resolve them
# Then push
git push origin main
```

### Rule 4: Small, Frequent Commits
```bash
# Bad: Work for 8 hours, one giant commit
# Good: Commit every 30-60 minutes

git add .
git commit -m "Add todo priority sorting"
git push origin your-branch
```

### Rule 5: Merge Main into Your Branch Daily
```bash
# While on your feature branch
git checkout your-branch
git merge main  # Get latest changes from main
# Resolve any conflicts NOW (easier than later)
git push origin your-branch
```

---

## 📞 Communication Protocol

### Before Starting Work
Post in team chat:
> "Working on: frontend/TodoPanel.tsx
> ETA: 2 hours
> Will push by: 3pm"

### When Pushing to Main
Post in team chat:
> "Pushed changes to main
> Files changed: backend/app/rag.py
> Everyone please pull!"

### When Creating PR
Post in team chat:
> "PR ready for review: backend/zoom-integration
> Link: [GitHub PR URL]
> Please review by EOD"

---

## 🔧 Conflict Resolution Guide

### If You Get a Merge Conflict

```bash
# 1. Pull latest
git pull origin main

# 2. Git shows conflicting files
# Example: backend/app/main.py

# 3. Open the file, look for:
<<<<<<< HEAD
your changes
=======
their changes
>>>>>>> main

# 4. Edit to keep correct version
# Remove the <<<<<<, =======, >>>>>>> markers

# 5. Test that it works!
python -m uvicorn app.main:app --reload  # Backend
npm run dev  # Frontend

# 6. Mark as resolved
git add backend/app/main.py
git commit -m "Resolve merge conflict in main.py"
git push
```

### Conflict Prevention Tips
1. **Pull frequently** - Every 1-2 hours
2. **Push frequently** - Don't hoard changes
3. **Small commits** - Easier to resolve
4. **Communicate** - Tell team what you're editing

---

## 📊 Example Work Split

### Day 1 (Today)
- **Person 1**: Set up real Zoom integration stub
- **Person 2**: Polish UI and add animations
- **Person 3**: Write tests and update docs

### Day 2
- **Person 1**: Improve AI prompts for better extraction
- **Person 2**: Make mobile responsive
- **Person 3**: Set up deployment

### Day 3
- **Person 1**: Add error handling and logging
- **Person 2**: Accessibility features
- **Person 3**: Integration testing

### Day 4 (Demo Day)
- **Everyone**: Final testing, demo prep, pitch practice

---

## 🎯 File Ownership Matrix

| File | Owner | Others Can |
|------|-------|------------|
| `backend/app/rag.py` | Person 1 | Read only |
| `backend/app/main.py` | Person 3 | Coordinate with P1 |
| `backend/app/models.py` | Person 3 | Coordinate with P1 |
| `frontend/app/components/*.tsx` | Person 2 | Read only |
| `frontend/app/lib/api.ts` | Person 3 | Coordinate with P2 |
| `*.md` docs | Person 3 | Anyone can update |
| Tests | Person 3 | Anyone can add |

---

## 🚀 Quick Commands for Each Person

### Person 1 (Backend)
```bash
git checkout -b backend/my-feature
# Edit backend/app/*.py files
git add backend/
git commit -m "Backend: description"
git push origin backend/my-feature
gh pr create
```

### Person 2 (Frontend)
```bash
git checkout -b frontend/my-feature
# Edit frontend/app/components/*.tsx files
git add frontend/
git commit -m "Frontend: description"
git push origin frontend/my-feature
gh pr create
```

### Person 3 (Integration)
```bash
git checkout -b integration/my-feature
# Edit tests, docs, configs
git add .
git commit -m "Integration: description"
git push origin integration/my-feature
gh pr create
```

---

## 📱 Team Communication Checklist

### Before Editing Shared Files
- [ ] Post in team chat: "Need to edit [filename]"
- [ ] Wait for confirmation no one else is editing
- [ ] Make changes quickly
- [ ] Push immediately
- [ ] Notify team: "Done with [filename]"

### Before Pushing to Main
- [ ] Pull latest: `git pull origin main`
- [ ] Test locally
- [ ] Check no conflicts
- [ ] Push
- [ ] Notify team

### Before Creating PR
- [ ] Branch is up to date with main
- [ ] All tests pass
- [ ] No console errors
- [ ] Descriptive PR title and description

---

## 🎓 Pro Tips

### 1. Use GitHub Desktop (Optional)
- Visual interface for Git
- Easier to see conflicts
- Download: https://desktop.github.com/

### 2. Use VS Code Git Integration
- Built-in Git UI
- See changes inline
- Resolve conflicts visually

### 3. Pair Programming
- Work together on video call
- One person codes, others review
- No merge conflicts!

### 4. Lock Files
Post in team chat:
> "🔒 Editing main.py for next 30 min - please don't touch!"

### 5. Code Reviews
- Review each other's PRs
- Catch bugs early
- Learn from each other

---

## ✅ Success Checklist

Your team workflow is good if:
- [ ] Everyone knows what files they own
- [ ] No one edits same file simultaneously
- [ ] Everyone pulls before pushing
- [ ] Commits are small and frequent
- [ ] Communication is clear
- [ ] Conflicts are rare
- [ ] Main branch always works

---

## 🆘 Emergency: "Everything is Broken!"

```bash
# Option 1: Revert to last working commit
git log --oneline  # Find last good commit
git reset --hard <commit-hash>
git push --force origin main  # Coordinate with team first!

# Option 2: Create hotfix branch
git checkout -b hotfix/emergency-fix
# Fix the issue
git commit -m "Hotfix: description"
git push origin hotfix/emergency-fix
# Merge immediately

# Option 3: Start fresh from last working state
git checkout main
git pull origin main
git checkout -b fresh-start
# Copy working code
```

---

## 📞 Quick Reference

**Avoid conflicts:**
- Own your files
- Communicate
- Pull often
- Push often

**If conflict happens:**
- Stay calm
- Pull latest
- Resolve carefully
- Test before pushing

**Best practice:**
- Feature branches
- Pull requests
- Code reviews
- Small commits

---

**Remember:** Communication > Clever Git tricks

Talk to your team, coordinate who edits what, and you'll avoid 90% of merge conflicts! 🎉
