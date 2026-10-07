# ⚡ EchoInsight — AI-Driven Customer Feedback to PRD Pipeline

> **Turn raw customer feedback into prioritized RICE clusters and complete Product Requirement Documents (PRDs) in seconds — powered by Google Gemini 3.6 Flash & ChromaDB Vector Memory.**

---

[![Live Demo](https://img.shields.io/badge/Live_Demo-EchoInsight-6366f1?style=for-the-badge&logo=vercel&logoColor=white)](https://echoinsight.onrender.com)
[![Backend API](https://img.shields.io/badge/API_Status-Online-00C853?style=for-the-badge&logo=render&logoColor=white)](https://echoinsight.onrender.com)
[![Swagger Docs](https://img.shields.io/badge/API_Docs-Swagger_UI-009688?style=for-the-badge&logo=swagger&logoColor=white)](https://echoinsight.onrender.com/docs)
[![GitHub Repository](https://img.shields.io/badge/GitHub-Repository-181717?style=for-the-badge&logo=github&logoColor=white)](https://github.com/SusheelSagar4/EchoInsight)

---

## 🔗 Live Links & Demo

* 🌐 **Live Website Application**: [https://echoinsight.onrender.com](https://echoinsight.onrender.com)
* ⚡ **Live Backend API**: [https://echoinsight.onrender.com](https://echoinsight.onrender.com)
* 📖 **Interactive API Documentation (Swagger)**: [https://echoinsight.onrender.com/docs](https://echoinsight.onrender.com/docs)
* 🐙 **GitHub Repository**: [https://github.com/SusheelSagar4/EchoInsight](https://github.com/SusheelSagar4/EchoInsight)

---

## 🌟 What We've Built So Far

Product Managers routinely receive hundreds of unorganized feedback items from emails, support tickets, CSV exports, and app store reviews. Manually grouping feedback, tagging severity, checking for past recurring issues, calculating priority, and drafting PRDs takes hours.

**EchoInsight** is an autonomous end-to-end intelligence engine designed to solve this exact problem:

### ✨ Core Features

1. **📥 Dual Ingestion Engine**:
   - Accepts raw multi-line unstructured text inputs or batch `.csv` file uploads.

2. **🤖 AI Sentiment & Intent Tagging (Google Gemini 3.6 Flash)**:
   - Categorizes every feedback item automatically by:
     - **Sentiment**: `Positive`, `Negative`, `Neutral`
     - **Intent**: `Bug Report`, `Feature Request`, `UX Friction`
     - **Urgency**: `Low`, `Medium`, `High`

3. **📊 RICE Prioritization Framework**:
   - Automatically computes Reach, Impact, Confidence, and Effort scores for every cluster to generate a unified **RICE Score**.
   - Highlights total affected user counts and friction/bug counts per cluster.

4. **🧠 Long-Term RAG Vector Memory (ChromaDB + Gemini Embeddings)**:
   - Uses `text-embedding-004` (768-dimensional vectors) to generate semantic embeddings for feedback items.
   - Queries ChromaDB vector store (`distance < 0.3`) to detect duplicate issues from previous sessions.
   - Displays a visual **`🔁 Seen Nx before`** badge on recurring user feedback items.

5. **📄 One-Click PRD Generator**:
   - Drafts complete, structured Product Requirements Documents for any selected cluster (Problem Statement, User Stories, Acceptance Criteria, KPIs).
   - Includes instant **"Copy as Markdown"** functionality for Jira, Notion, or GitHub issue templates.

6. **🎨 Premium Dark Liquid-Glass UI & Physics Particles**:
   - Built with React 19 + Vite 8 featuring glassmorphism styling, dark aesthetic, smooth entrance micro-animations, and noise texture.
   - Interactive hero canvas with **280 physics-driven dust particles** reacting dynamically to cursor movement and repulsion forces.
   - Includes an **Automated Live Typewriter Demo** on the landing page that automatically simulates typing feedback, cursor movements, clustering, and PRD generation.

---

## 🛠️ Tech Stack

### Frontend
- **Framework**: React 19 (`react` `^19.2.8`)
- **Build Tool**: Vite 8 (`vite` `^8.2.0`)
- **Styling**: Vanilla CSS3 (Custom Properties, Glassmorphism, CSS Grid, Entrance Animations)
- **Canvas Engine**: HTML5 Canvas (Interactive Particle System with Repulsion Physics)

### Backend
- **Framework**: FastAPI (`fastapi` `^0.110.0`)
- **Server**: Uvicorn (`uvicorn` `^0.28.0`)
- **Data Validation**: Pydantic (`pydantic` `^2.6.0`)
- **AI Engine**: Google Gemini AI (`google-generativeai` `^0.4.0`) — Gemini 3.6 Flash
- **Vector DB**: ChromaDB (`chromadb` `^0.4.24`) — Long-Term RAG Vector Memory
- **Embeddings**: Gemini `text-embedding-004`

---

## 🏗️ System Architecture & Data Flow

```text
               ┌──────────────────────────────────────────────┐
               │              React 19 Frontend               │
               │   (Landing Page Demo & Workspace View)      │
               └──────────────────────┬───────────────────────┘
                                      │
                         REST API Calls (JSON / CSV)
                                      ▼
               ┌──────────────────────────────────────────────┐
               │           FastAPI Python Backend             │
               │       (/cluster, /cluster-csv, /prd)         │
               └──────────────┬────────────────┬──────────────┘
                              │                │
             Gemini AI Calls  │                │ Vector Queries & Storage
                              ▼                ▼
         ┌────────────────────────┐        ┌────────────────────────┐
         │  Google Gemini 3.6     │        │    ChromaDB Vector     │
         │ Flash & Embeddings 004 │        │   Database Storage     │
         └────────────────────────┘        └────────────────────────┘
```

---

## 🔌 API Endpoints Summary

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/` | Health check endpoint |
| `GET` | `/docs` | Interactive Swagger UI API documentation |
| `POST` | `/feedback/cluster` | Analyzes raw text feedback, queries ChromaDB, groups into RICE clusters |
| `POST` | `/feedback/cluster-csv` | Parses column 1 of uploaded CSV file and executes clustering pipeline |
| `POST` | `/feedback/prd` | Generates a structured PRD document for a specific feedback cluster |

---

## 🚀 Getting Started

### Prerequisites
- **Python**: `3.10+`
- **Node.js**: `v18+` & `npm`
- **Google Gemini API Key**: Obtainable from [Google AI Studio](https://aistudio.google.com/)

---

### Option A: One-Click Startup Script (Windows)

Simply double-click or run `start.bat` at the repository root:
```cmd
start.bat
```
This automatically starts both the FastAPI backend (`http://127.0.0.1:8000`) and the Vite React frontend (`http://localhost:5173`).

---

### Option B: Manual Setup

#### 1. Setup Backend (`/backend`)
```bash
cd backend
python -m venv venv
# Activate venv:
# Windows: venv\Scripts\activate
# Linux/macOS: source venv/bin/activate

pip install -r requirements.txt
```

Create a `.env` file inside `/backend`:
```env
GEMINI_API_KEY=your_google_gemini_api_key_here
```

Start backend server:
```bash
uvicorn app.main:app --reload --port 8000
```

#### 2. Setup Frontend (`/frontend`)
```bash
cd frontend
npm install
```

Create a `.env` file inside `/frontend`:
```env
VITE_API_URL=http://127.0.0.1:8000
```

Start development server:
```bash
npm run dev
```

Open `http://localhost:5173` in your browser.

---

## 🤖 Agent Architecture

EchoInsight includes an autonomous AI Agent tool layer built in Python for executing product intelligence workflows.

### Design Principles:
1. **Error Classification & Retry Metadata**: Failure envelopes return:
   `{"ok": False, "error": "<msg>", "retryable": <bool>, "error_type": "<type>", "retry_after_seconds": <int|None>}`
   - `error_type` is categorized as `"rate_limited"`, `"timeout"`, `"quota_exhausted"`, or `"other"`.
   - `parse_duration_seconds` converts complex duration strings (e.g., `7h45m38.1s`, `44.45s`, `seconds: 27938`) to total seconds.
   - Long delays (> 120 seconds) or `PerDay` limits are accurately categorized as `quota_exhausted` with `retryable: False`.
2. **Unified LLM Client with Dev Caching (`backend/app/services/llm_client.py`)**:
   - Centralizes Gemini model calls via `generate_text(prompt, json_mode)`.
   - Reads model name from `GEMINI_MODEL` env var (default `"gemini-3.6-flash"`).
   - Supports local dev response caching when `LLM_CACHE=1`, saving prompt hashes and responses to `backend/data/llm_cache/`.
3. **Honest Test Suite Execution (`backend/test_tools.py`)**:
   - Executes each tool in sequence without hiding real API failures using mock fallbacks.
   - Retries transient errors (`retryable=True`) once after sleeping `N+2` seconds.
   - Outputs a summary table listing each tool's status (`PASS`, `FAIL`, or `SKIPPED`) and an overall result of `PASS` only if all tools pass.
4. **Declarative Tool Registry**: Central `TOOL_REGISTRY` mapping tool names to functions, clear descriptions, argument metadata, and approval flags (`requires_approval=True` ONLY for write operations like `create_backlog_item`).
5. **Resilient Local Persistence**: Engineering backlog items are assigned incremental IDs (`ENG-101`) and saved to `backend/data/backlog.json`.

### Available Tools:
- `get_customer_feedback()`: Reads customer feedback lines from CSV.
- `search_memory(query, top_k)`: Queries ChromaDB vector memory for semantic matches.
- `cluster_feedback_tool(feedback_lines)`: Calls Gemini AI to group lines into RICE-prioritized clusters.
- `rank_clusters(clusters)`: Sorts cluster dicts by RICE score descending.
- `generate_prd_tool(cluster)`: Generates a PRD object from a cluster dict.
- `create_backlog_item(title, description, priority)`: Appends an engineering ticket to `backlog.json` (requires approval). Includes `SIMULATE_FAILURES` flag for failure recovery testing.
- `verify_backlog_item(item_id)`: Confirms a ticket exists in `backlog.json`.

---

## 📝 Agent Upgrade Changelog

### [2026-10-07] - LLM Client Caching, Duration Error Parsing & Honest Test Suite
- **What Changed**:
  - Implemented `backend/app/services/llm_client.py` with dynamic model selection via `GEMINI_MODEL` and optional dev caching via `LLM_CACHE=1` stored in `backend/data/llm_cache/`.
  - Refactored `clustering_service.py` and `prd_service.py` to use `llm_client.generate_text()`.
  - Enhanced `classify_error()` in `tools.py` with `parse_duration_seconds()` to accurately parse `7h45m38.1s`, `44.45s`, and `seconds: X` patterns, and tag `error_type` (`"rate_limited"`, `"timeout"`, `"quota_exhausted"`, `"other"`).
  - Updated `test_tools.py` to remove mock fallbacks, track `PASS`/`FAIL`/`SKIPPED` per tool, and output an overall summary table.
  - Added `backend/.env.example` with commented `GEMINI_MODEL` and `LLM_CACHE` configuration examples.
  - Updated `.gitignore` to ignore `backend/data/llm_cache/`.
- **Files Touched**:
  - `backend/app/agent/tools.py`
  - `backend/test_tools.py`
  - `backend/app/services/llm_client.py`
  - `backend/app/services/clustering_service.py`
  - `backend/app/services/prd_service.py`
  - `backend/.env.example`
  - `.gitignore`
  - `README.md`
- **Why**: Prevents misclassifying hours as seconds in rate limits, distinguishes daily quota exhaustion from temporary per-minute limits, provides local LLM dev caching to protect API quota, and enforces honest test reporting without false positives.

### [2026-10-07] - Retryable Failure Metadata & Rate Limit Handler
- **What Changed**: Enhanced tool failure envelopes to include `retryable` (boolean) and `retry_after_seconds` (integer or None) fields parsed via `classify_error()`. Updated `test_tools.py` with an isolated retry helper `execute_with_test_retry` that waits `N+2` seconds when encountering transient errors.
- **Files Touched**:
  - `backend/app/agent/tools.py`
  - `backend/test_tools.py`
  - `README.md`
- **Why**: Allows autonomous agent loops to intelligently react to rate limits (HTTP 429), timeouts, and service unavailability by inspecting delay metadata before scheduling retries, preventing API spamming and agent crashes.

### [2026-10-07] - Initial Agent Tool Layer Implementation
- **What Changed**: Created the foundational tool layer for the autonomous agent workflow, including data ingestion, vector search, Gemini AI clustering, RICE ranking, PRD generation, backlog ticket creation, and verification tools. Added an isolated test script and runtime ignore rules.
- **Files Touched**:
  - `backend/data/sample_feedback.csv`
  - `backend/app/agent/__init__.py`
  - `backend/app/agent/tools.py`
  - `backend/test_tools.py`
  - `.gitignore`
  - `README.md`
- **Why**: Enables an autonomous agent to safely invoke modular tools with uniform error handling, approval safety checks, local JSON backlog persistence, and failure recovery testing capability.



---

## 📄 License & Attribution

Built with ❤️ for Product Managers by **Susheel Sagar**.
Detailed technical documentation and branch change logs can be found in [`PROJECT_ARCHITECTURE.md`](file:///c:/Bunty/IIT%20BBS/PM/EchoInsight/PROJECT_ARCHITECTURE.md).

