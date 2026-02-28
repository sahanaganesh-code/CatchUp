#!/bin/bash
# Git setup script for CatchUp

echo "🚀 CatchUp - Git Setup Script"
echo "================================"
echo ""

# Check if already initialized
if [ -d ".git" ]; then
    echo "✓ Git already initialized"
else
    echo "Initializing Git repository..."
    git init
    echo "✓ Git initialized"
fi

# Configure Git
echo ""
echo "Setting up Git configuration..."
read -p "Enter your name: " git_name
read -p "Enter your email: " git_email

git config user.name "$git_name"
git config user.email "$git_email"
echo "✓ Git configured"

# Check for sensitive files
echo ""
echo "Checking for sensitive files..."
if [ -f "backend/.env" ]; then
    echo "⚠️  WARNING: backend/.env exists (contains API keys)"
    echo "   This file is in .gitignore and won't be committed"
fi

# Show status
echo ""
echo "Current status:"
git status

# Stage all files
echo ""
read -p "Stage all files for commit? (y/n): " stage_files
if [ "$stage_files" = "y" ]; then
    git add .
    echo "✓ Files staged"
    
    echo ""
    echo "Files to be committed:"
    git status --short
fi

# Create initial commit
echo ""
read -p "Create initial commit? (y/n): " create_commit
if [ "$create_commit" = "y" ]; then
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
    
    echo "✓ Initial commit created"
fi

# GitHub setup
echo ""
echo "================================"
echo "Next Steps:"
echo "================================"
echo ""
echo "Option 1: Using GitHub CLI (Recommended)"
echo "  gh auth login"
echo "  gh repo create catchup --public --source=. --remote=origin --push"
echo ""
echo "Option 2: Using GitHub Website"
echo "  1. Go to https://github.com/new"
echo "  2. Create repository named 'catchup'"
echo "  3. Run these commands:"
echo "     git remote add origin https://github.com/YOUR_USERNAME/catchup.git"
echo "     git branch -M main"
echo "     git push -u origin main"
echo ""
echo "Then invite your teammates as collaborators!"
echo ""
echo "See GIT_SETUP_GUIDE.md for detailed instructions."
