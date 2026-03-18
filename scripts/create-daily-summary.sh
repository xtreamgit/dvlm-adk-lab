#!/bin/bash
#
# create-daily-summary.sh
# Creates a new session summary file from template for today's date
#

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Use current working directory as project root
PROJECT_ROOT="$(pwd)"
OUTPUT_DIR="$PROJECT_ROOT/cascade-logs"

# Get today's date in YYYY-MM-DD format
TODAY=$(date +%Y-%m-%d)
READABLE_DATE=$(date +"%B %d, %Y")  # e.g., "January 06, 2026"
START_TIME=$(date +"%I:%M %p")      # e.g., "09:38 AM"

# Date-based folder for today's documents
DATE_FOLDER="$OUTPUT_DIR/$TODAY"

# Output files
OUTPUT_FILE="$DATE_FOLDER/SESSION_SUMMARY_${TODAY}.md"
NOTES_FILE="$DATE_FOLDER/DailyNotes.md"

# Create output directory if it doesn't exist
mkdir -p "$OUTPUT_DIR"

# Create date-based folder for today's documents
if [ ! -d "$DATE_FOLDER" ]; then
    mkdir -p "$DATE_FOLDER"
    echo -e "${GREEN}📁 Created folder: $DATE_FOLDER${NC}"
else
    echo -e "${BLUE}📁 Using existing folder: $DATE_FOLDER${NC}"
fi
echo ""

# Check if today's summary already exists
if [ -f "$OUTPUT_FILE" ]; then
    echo -e "${YELLOW}⚠️  Session summary for $TODAY already exists:${NC}"
    echo -e "${BLUE}   $OUTPUT_FILE${NC}"
    echo ""
    read -p "Do you want to overwrite it? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${GREEN}✅ Keeping existing file.${NC}"
        echo -e "${BLUE}   File: $OUTPUT_FILE${NC}"
        exit 0
    fi
fi

# Create session summary with embedded template
echo -e "${BLUE}📝 Creating session summary for $READABLE_DATE...${NC}"

cat > "$OUTPUT_FILE" << 'TEMPLATE_EOF'
# Coding Session Summary - [DATE]

## ⚠️ **Daily Startup Checklist**

Run these commands each morning to begin your coding session:

### 1. **Create Session Summary**
```bash
start
```
Creates today's session summary file automatically (alias for create-daily-summary.sh).

### 2. **Login to Google Cloud**
```bash
gcloud auth application-default login
```
Required for Vertex AI RAG access (document counts, corpus operations).

### 3. **Start Backend Server**
```bash
cd ~/github.com/xtreamgit/adk-multi-agents/backend
python -m uvicorn src.api.server:app --host 0.0.0.0 --port 8000 --reload
```
- Server: `http://localhost:8000`
- Keep terminal open or run in background

### 4. **Start Frontend Development Server** (new terminal)
```bash
cd ~/github.com/xtreamgit/adk-multi-agents/frontend
npm run dev
```
- Frontend: `http://localhost:3000`
- Keep terminal open

### 5. **Verify Everything is Running**
```bash
# Backend health check
curl http://localhost:8000/api/health

# Frontend: Open browser to http://localhost:3000
```

**Common Issues:**
- "Load failed" → Backend not running (step 2)
- "Connection refused" → Wrong port or server not started
- Document counts = 0 → Not logged into Google Cloud (step 1)

---

## 📋 **Session Overview**

**Date:** [DATE]  
**Start Time:** [TIME]  
**Duration:** [DURATION]  
**Focus Areas:** [BRIEF DESCRIPTION]

---

## 🎯 **Goals for Today**

- [ ] Goal 1
- [ ] Goal 2
- [ ] Goal 3

---

## � **Changes Made**

### Feature/Fix #1: [Title]
**Commit:** `[commit-hash]` - "[commit message]"

**Problem:**
- Describe the issue or requirement

**Solution:**
- What was implemented
- Technical approach

**Files Changed:**
- `path/to/file1.ext` - Description of changes
- `path/to/file2.ext` - Description of changes

**Testing:**
- How it was tested
- Results

---

### Feature/Fix #2: [Title]
**Commit:** `[commit-hash]` - "[commit message]"

**Problem:**
- Describe the issue or requirement

**Solution:**
- What was implemented
- Technical approach

**Files Changed:**
- `path/to/file1.ext` - Description of changes
- `path/to/file2.ext` - Description of changes

**Testing:**
- How it was tested
- Results

---

## 🐛 **Bugs Fixed**

### Bug: [Description]
- **Issue:** What was broken
- **Root Cause:** Why it was broken
- **Fix:** How it was fixed
- **Files:** `path/to/file.ext`
- **Commit:** `[hash]`

---

## 📊 **Technical Details**

### Backend Changes
- List significant backend modifications
- API endpoint changes
- Database schema updates
- Service/logic changes

### Frontend Changes
- UI/UX improvements
- Component modifications
- State management updates
- New features added

### Database Changes
```sql
-- Any SQL changes made
```

### Configuration Changes
- Environment variables
- Config file updates
- Deployment changes

---

## 🧪 **Testing Notes**

### Manual Testing
- [ ] Feature X tested and working
- [ ] Edge case Y verified
- [ ] User flow Z validated

### Issues Found
- Issue 1: Description
- Issue 2: Description

### Issues Fixed
- Fix 1: Description
- Fix 2: Description

---

## 📝 **Code Quality**

### Refactoring Done
- What was refactored and why

### Tech Debt
- New tech debt introduced (if any)
- Tech debt resolved

### Performance
- Any performance improvements
- Benchmarks if applicable

---

## 💡 **Learnings & Notes**

### What I Learned
- Key insight 1
- Key insight 2
- Key insight 3

### Challenges Faced
- Challenge 1 and how it was overcome
- Challenge 2 and solution

### Best Practices Applied
- Practice 1
- Practice 2

---

## 📦 **Files Modified**

### Backend ([N] files)
- `backend/path/to/file1.py` - Description
- `backend/path/to/file2.py` - Description

### Frontend ([N] files)
- `frontend/src/path/to/file1.tsx` - Description
- `frontend/src/path/to/file2.ts` - Description

### Configuration ([N] files)
- `config/file.yaml` - Description

### Documentation ([N] files)
- `docs/file.md` - Description

**Total Lines Changed:** ~[N]+ additions, ~[N]+ deletions

---

## 🚀 **Commits Summary**

1. `[hash]` - [Commit message]
2. `[hash]` - [Commit message]
3. `[hash]` - [Commit message]

**Total:** [N] commits

---

## 🔮 **Next Steps**

### Immediate Tasks (Today/Tomorrow)
- [ ] Task 1
- [ ] Task 2
- [ ] Task 3

### Short-term (This Week)
- [ ] Feature to implement
- [ ] Bug to fix
- [ ] Improvement to make

### Future Enhancements
- Idea 1
- Idea 2
- Idea 3

---

## ⚙️ **Environment Status**

### Current Configuration
- **Backend:** Running on port 8000
- **Frontend:** Running on port 3000
- **Database:** PostgreSQL (Docker container: adk-postgres-dev, port 5433)
- **Google Cloud Project:** `adk-rag-ma`
- **Vertex AI Region:** `us-west1`

### Active Corpora
- `ai-books` (AI Books Collection) - [N] documents
- `test-corpus` (Test Corpus) - [N] documents

---

## ✅ **Session Complete**

**End Time:** [TIME]  
**Total Duration:** [DURATION]  
**Goals Achieved:** [N]/[N]  
**Commits Made:** [N]  
**Files Changed:** [N]  

**Summary:**
[Brief 2-3 sentence summary of what was accomplished]

---

## 📌 **Remember for Next Session**

- Important note 1
- Important note 2
- Where you left off
TEMPLATE_EOF

# Replace placeholders with actual values
sed -i '' -e "s/\[DATE\]/$READABLE_DATE/g" \
    -e "s/\[TIME\]/$START_TIME/g" \
    -e "s/\[DURATION\]/TBD/g" \
    "$OUTPUT_FILE"

echo -e "${GREEN}✅ Created: $OUTPUT_FILE${NC}"

# Create DailyNotes.md file
echo -e "${BLUE}📝 Creating daily notes file...${NC}"

cat > "$NOTES_FILE" << 'NOTES_EOF'
---
**Author:** Hector  
**Date:** [DATE]  
**Purpose:** All the notes created during the day will be collected here. The notes could include temporary pieces of information, prompts used during the coding process, and other miscellaneous information about the project.

---

## Project Summary

**ADK Multi-Agents RAG System** is a multi-agent Retrieval-Augmented Generation (RAG) application built on Google Cloud Platform. The system enables intelligent document search and question-answering across multiple knowledge corpora using Vertex AI RAG.

**Key Components:**
- **Backend:** FastAPI-based Python server with PostgreSQL database
- **Frontend:** Next.js React application with TypeScript
- **AI/RAG:** Google Vertex AI RAG for document retrieval and semantic search
- **Authentication:** Identity-Aware Proxy (IAP) with local username/password fallback
- **Deployment:** Google Cloud Run (containerized microservices)
- **Infrastructure:** Terraform-managed GCP resources

**Core Features:**
- Multi-corpus document management and search
- Role-based access control (RBAC) for users, groups, and agents
- Multiple specialized AI agents with different capabilities
- Admin panel for managing users, groups, corpora, and agents
- Document upload, retrieval, and audit logging
- Real-time chat interface with RAG-powered responses

**Tech Stack:**
- Python 3.11, FastAPI, PostgreSQL, SQLAlchemy
- Next.js 15, React 19, TypeScript, TailwindCSS
- Google Cloud: Vertex AI, Cloud Run, Cloud SQL, IAP
- Docker, Terraform, GitHub Actions (CI/CD)

---

## Daily Notes

### [TIME] - Note Title
[Note content goes here...]

---

### [TIME] - Note Title
[Note content goes here...]

---

NOTES_EOF

# Replace placeholders in notes file
sed -i '' -e "s/\[DATE\]/$READABLE_DATE/g" "$NOTES_FILE"

echo -e "${GREEN}✅ Created: $NOTES_FILE${NC}"
echo ""
echo -e "${BLUE}📋 Next steps:${NC}"
echo "   1. Fill in session goals and focus areas"
echo "   2. Document changes as you make them"
echo "   3. Update at end of day with completion status"
echo ""

echo -e "${BLUE}📂 File: $OUTPUT_FILE${NC}"
echo ""
echo -e "${GREEN}✨ Ready to start coding! Don't forget:${NC}"
echo "   • gcloud auth application-default login"
echo "   • Start backend: cd backend && python -m uvicorn src.api.server:app --host 0.0.0.0 --port 8000 --reload"
echo "   • Start frontend: cd frontend && npm run dev"
