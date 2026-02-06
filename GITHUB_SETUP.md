# GitHub Repository Setup Guide

## ✅ Current Status

- [x] Git repository initialized
- [x] Initial commit created (34 files)
- [x] All sensitive files properly ignored (.env, data/, .venv/)
- [x] Ready to push to GitHub

---

## 📋 Quick Setup (Choose One Method)

### Option A: Using GitHub Website (Easiest)

1. **Go to GitHub** and sign in: https://github.com

2. **Create a new repository:**
   - Click the "+" icon in top-right → "New repository"
   - **Repository name:** `VenueHorn` (or `venuehorn-ai`)
   - **Description:** "AI-powered venue discovery platform for events"
   - **Visibility:** ✅ **Private** (important!)
   - **DO NOT** initialize with README, .gitignore, or license (we already have these)
   - Click "Create repository"

3. **Copy the repository URL** that GitHub shows you. It will look like:
   ```
   https://github.com/YOUR_USERNAME/VenueHorn.git
   ```

4. **Run these commands in your terminal:**
   ```bash
   # Add GitHub as remote
   git remote add origin https://github.com/YOUR_USERNAME/VenueHorn.git

   # Push your code
   git push -u origin main
   ```

5. **Done!** Your code is now on GitHub 🎉

---

### Option B: Using GitHub CLI (Automated)

If you want to install GitHub CLI for easier management:

```bash
# Install GitHub CLI
brew install gh  # macOS
# Or download from: https://cli.github.com/

# Login to GitHub
gh auth login

# Create private repository and push
gh repo create VenueHorn --private --source=. --remote=origin --push

# Done! Repository created and code pushed
```

---

## 🔐 Security Checklist

Before pushing, verify these sensitive files are **NOT** included:

```bash
# Check what will be pushed
git status

# Verify .env files are ignored
git check-ignore venuehorn/backend/.env

# Should show: venuehorn/backend/.env (means it's ignored ✅)

# Make sure these are in .gitignore:
cat .gitignore | grep -E "(\.env$|/data/|\.venv)"
```

**Sensitive files that MUST be ignored:**
- [x] `.env` files (except `.env.example`)
- [x] `/backend/data/` (vector indices, metadata)
- [x] `/backend/.venv/` (Python virtual environment)
- [x] API keys and secrets
- [x] Database credentials

---

## 📦 What's Being Pushed

Your repository includes:

### Documentation
- `README.md` - Project overview
- `FIXES_APPLIED.md` - API fixes (Step 1)
- `HYBRID_SEARCH_ARCHITECTURE.md` - Architecture design (Step 2)
- `IMPLEMENTATION_GUIDE.md` - Implementation guide
- `LICENSE` - MIT License

### Backend (Python/FastAPI)
- `venuehorn/backend/app/` - API code
  - `main.py` - API endpoints ✅ Fixed
  - `config.py` - Configuration ✅ Fixed model name
  - `models.py` - Database models
  - `vector_store.py` - FAISS vector search
  - `schemas.py` - Pydantic schemas
- `venuehorn/backend/scripts/` - Utility scripts
  - `ingest_csv.py` - Data ingestion
- `venuehorn/backend/test_api.py` - API tests
- `venuehorn/backend/requirements.txt` - Python dependencies
- `venuehorn/backend/.env.example` - Environment template ✅

### Frontend (Next.js/React)
- `venuehorn/app/` - Next.js pages
- `venuehorn/public/` - Static assets
- Configuration files (tsconfig, eslint, etc.)

**Total:** 34 files, ~2,800 lines of code

---

## 🚀 After Pushing to GitHub

### 1. Set Repository Settings

Go to: `https://github.com/YOUR_USERNAME/VenueHorn/settings`

**Recommended settings:**
- ✅ Disable "Allow merge commits" (use squash or rebase)
- ✅ Enable "Automatically delete head branches"
- ✅ Add repository topics: `ai`, `machine-learning`, `venue-booking`, `fastapi`, `nextjs`

### 2. Add Repository Secrets (for CI/CD later)

Go to: `Settings → Secrets and variables → Actions`

Add these secrets when you set up deployment:
- `OPENAI_API_KEY` - Your OpenAI API key
- `DATABASE_URL` - PostgreSQL connection string (when ready)

### 3. Create .github Workflows (Optional)

For automated testing:

```bash
mkdir -p .github/workflows
```

Create `.github/workflows/test.yml`:
```yaml
name: Run Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.9'
      - run: |
          cd venuehorn/backend
          pip install -r requirements.txt
          python -m pytest
```

### 4. Add Collaborators (if team project)

Go to: `Settings → Collaborators → Add people`

---

## 📝 Common Git Commands

```bash
# Check status
git status

# View commit history
git log --oneline

# Create a new branch
git checkout -b feature/new-feature

# Add changes
git add .

# Commit changes
git commit -m "Description of changes"

# Push to GitHub
git push origin main

# Pull latest changes
git pull origin main

# View remote repositories
git remote -v
```

---

## 🔄 Workflow for Future Changes

```bash
# 1. Make changes to your code
# 2. Check what changed
git status
git diff

# 3. Stage changes
git add .

# 4. Commit with descriptive message
git commit -m "Add hybrid search endpoint"

# 5. Push to GitHub
git push origin main
```

---

## 🆘 Troubleshooting

### "Permission denied" when pushing

```bash
# If using HTTPS, you may need a Personal Access Token
# Go to: GitHub → Settings → Developer settings → Personal access tokens
# Generate token with 'repo' scope
# Use token as password when prompted
```

### Already pushed .env file by accident?

```bash
# Remove from git but keep local file
git rm --cached venuehorn/backend/.env
git commit -m "Remove .env from version control"
git push origin main

# Then change all secrets in that .env file!
```

### Wrong repository URL

```bash
# Check current remote
git remote -v

# Change remote URL
git remote set-url origin https://github.com/YOUR_USERNAME/VenueHorn.git
```

---

## ✅ Next Steps After GitHub Setup

1. **Share repository** with team members (if applicable)
2. **Set up CI/CD** for automated testing and deployment
3. **Create development branch** for ongoing work
4. **Start implementing** hybrid search (see IMPLEMENTATION_GUIDE.md)
5. **Deploy backend** to cloud provider (AWS, GCP, Render, etc.)

---

## 📚 Resources

- [GitHub Docs](https://docs.github.com/)
- [Git Cheat Sheet](https://education.github.com/git-cheat-sheet-education.pdf)
- [GitHub CLI](https://cli.github.com/)
- [Managing Secrets](https://docs.github.com/en/actions/security-guides/encrypted-secrets)

---

**Ready to push?** Let's get your code on GitHub! 🚀
