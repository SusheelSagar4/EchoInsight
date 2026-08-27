# ⚡ EchoInsight — AI-Driven Customer Feedback to PRD Pipeline

> **Turn raw customer feedback into prioritized RICE clusters and complete Product Requirement Documents (PRDs) in seconds — powered by Google Gemini 3.6 Flash & ChromaDB Vector Memory.**

---

[![Live Demo](https://img.shields.io/badge/Live_Demo-EchoInsight-6366f1?style=for-the-badge&logo=vercel&logoColor=white)](https://echo-insight.vercel.app/)
[![Backend API](https://img.shields.io/badge/API_Status-Online-00C853?style=for-the-badge&logo=render&logoColor=white)](https://echoinsight.onrender.com)
[![Swagger Docs](https://img.shields.io/badge/API_Docs-Swagger_UI-009688?style=for-the-badge&logo=swagger&logoColor=white)](https://echoinsight.onrender.com/docs)
[![GitHub Repository](https://img.shields.io/badge/GitHub-Repository-181717?style=for-the-badge&logo=github&logoColor=white)](https://github.com/SusheelSagar4/EchoInsight)

---

## 🔗 Live Links & Demo

* 🌐 **Live Website Application**: [https://echo-insight.vercel.app/](https://echo-insight.vercel.app/)
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

## 📄 License & Attribution

Built with ❤️ for Product Managers by **Susheel Sagar**.
Detailed technical documentation and branch change logs can be found in [`PROJECT_ARCHITECTURE.md`](file:///c:/Bunty/IIT%20BBS/PM/EchoInsight/PROJECT_ARCHITECTURE.md).
