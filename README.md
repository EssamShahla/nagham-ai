# Nagham AI 🎵

**Nagham AI** is an intelligent Arabic and Oriental music discovery platform designed to help musicians, music students, and listeners explore songs using musical structure, meaning, mood, and natural-language queries.

Instead of relying only on traditional keyword search, Nagham AI combines structured musical metadata, semantic embeddings, hybrid search, and an AI agent to understand requests such as:

> "I want emotional songs in Bayati about longing."

or:

> "Give me songs composed by Baligh Hamdi."

The system can reason about artist, composer, maqam, mood, topic, difficulty, year, and other musical information before selecting the appropriate search strategy.

---

## Project Goal

Musicians often know many songs but may struggle to quickly remember which songs match a specific maqam, mood, topic, composer, or musical situation.

Nagham AI provides an intelligent searchable knowledge base for Arabic and Oriental music.

The platform is designed to support queries based on:

- Song title
- Artist
- Composer
- Maqam
- Mood
- Topic
- Difficulty
- Year
- Semantic meaning
- Multiple combined constraints

The AI assistant automatically analyzes the user's natural-language request and chooses the appropriate search strategy.

---

## Main Features

### AI Music Assistant

Nagham AI includes a LangGraph-based AI agent that analyzes natural-language music requests.

The current flow is approximately:

```text
User Query
    ↓
Intent Analysis
    ↓
LangGraph Router
    ↓
┌─────────────────────┐
│ Structured Search   │
│ Semantic Search     │
│ Hybrid Search       │
└─────────────────────┘
    ↓
Ranking / Filtering
    ↓
RAG Answer
    ↓
User
```

The local LLM is used for query understanding and response generation, while actual song retrieval is grounded in the PostgreSQL database.

---

### Structured Search

Structured search handles explicit musical constraints such as:

- Artist
- Composer
- Maqam
- Difficulty
- Year

Example:

```text
أغاني لأم كلثوم من ألحان بليغ حمدي
```

The system can combine multiple structured conditions.

---

### Semantic Search

Semantic search allows users to search by meaning rather than exact words.

Example:

```text
أريد أغاني عن الاشتياق والغربة
```

Songs are represented using multilingual vector embeddings generated locally with:

```text
sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2
```

Embedding dimension:

```text
384
```

Embeddings are stored directly in PostgreSQL using `pgvector`.

---

### Hybrid Search

Hybrid Search combines structured musical constraints with semantic meaning.

Example:

```text
أريد أغنية حزينة عن الفراق على مقام الصبا
```

This can combine:

- Primary maqam = Saba
- Mood = sad
- Topic = separation
- Semantic similarity

The results are then reranked using semantic similarity and metadata matches.

---

### Boolean Filter Groups

The assistant supports more complex conditions using AND/OR filter groups.

Example:

```text
اقترح لي أغنيتين عن الاشتياق للملحن محمد عبد الوهاب أو لفيروز
```

Conceptually:

```text
(composer = محمد عبد الوهاب OR artist = فيروز)
AND
semantic topic = الاشتياق
```

---

## Maqam Architecture

Arabic music frequently contains more than one maqam inside the same composition.

Nagham AI therefore distinguishes between:

### Primary Maqam

The main maqam used to classify a song.

### Additional Maqamat

Other maqamat that appear in the composition.

The `SongMaqam` relationship represents the maqamat associated with each song and distinguishes the primary maqam using `is_primary`.

Conceptually:

```text
Song
 ├── Primary Maqam
 └── Additional Maqamat
```

This is important for accurate search behavior.

A normal query such as:

```text
أغاني على مقام الصبا
```

means that **Saba must be the primary maqam**.

A query explicitly asking about modulation or maqam occurrence, such as:

```text
أغاني فيها انتقال إلى مقام الصبا
```

may also consider additional maqamat or section-level maqam information.

---

## Song Sections

Nagham AI can represent detailed musical structure using song sections.

A section may contain information such as:

- Section order
- Section name
- Maqam
- Rhythm
- Tonic
- Notes

Conceptually:

```text
Song
 ├── Section 1 → Maqam / Rhythm
 ├── Section 2 → Maqam / Rhythm
 ├── Section 3 → Maqam / Rhythm
 └── ...
```

This architecture allows the project to represent maqam and rhythm changes within long Arabic compositions instead of assuming that every song contains only one maqam or rhythm.

Detailed section information is only stored when reliable musical data is available.

---

## Music Metadata

Depending on available verified information, songs can contain:

- Title
- Artist
- Composer
- Year
- Description
- Difficulty
- Moods
- Topics
- Primary maqam
- Additional maqamat
- Rhythm
- Musical sections
- Sources

The project avoids inventing uncertain music-theory information. Unknown factual metadata can remain empty until it is verified.

---

## Song Library

The Song Library provides a visual interface for browsing the music database.

It supports:

- Browsing songs
- Artist-based organization
- Song detail pages
- Searching by song title
- Searching by artist
- Musical metadata display

---

## Authentication

Nagham AI includes user authentication with:

- Registration
- Login
- JWT authentication
- Email verification using OTP
- User profiles

The backend also contains configuration support for Google OAuth.

Sensitive credentials are stored in local `.env` files and are never committed to the repository.

---

## Technology Stack

### Frontend

- Next.js 16
- React 19
- TypeScript
- Tailwind CSS
- shadcn/ui
- Lucide React

### Backend

- Python
- FastAPI
- SQLAlchemy
- Pydantic
- Alembic
- JWT Authentication

### Database

- PostgreSQL
- pgvector

### AI / Retrieval

- LangGraph
- Ollama
- Qwen 2.5 3B
- sentence-transformers
- Multilingual MiniLM embeddings
- Semantic Search
- Structured Search
- Hybrid Search
- Retrieval-Augmented Generation (RAG)

### Development / Infrastructure

- Docker
- Docker Compose
- Git
- Swagger / OpenAPI

---

## Project Structure

```text
nagham-ai/
│
├── backend/
│   ├── alembic/
│   ├── app/
│   │   ├── ai/
│   │   ├── core/
│   │   ├── database/
│   │   ├── models/
│   │   ├── routers/
│   │   ├── schemas/
│   │   ├── scripts/
│   │   ├── services/
│   │   └── utils/
│   │
│   ├── .env.example
│   ├── alembic.ini
│   └── requirements.txt
│
├── frontend/
│   ├── app/
│   ├── components/
│   ├── lib/
│   ├── public/
│   ├── .env.example
│   └── package.json
│
├── docker-compose.yml
├── .gitignore
└── README.md
```

---

# Running Nagham AI Locally

## Prerequisites

Install the following before running the project:

- Git
- Python
- Node.js
- npm
- Docker Desktop
- Ollama

The application uses Docker for PostgreSQL and pgvector.

---

## 1. Clone the Repository

```bash
git clone <YOUR_GITHUB_REPOSITORY_URL>
cd nagham-ai
```

---

## 2. Start PostgreSQL

Make sure Docker Desktop is running.

From the project root:

```bash
docker compose up -d
```

The included Docker Compose configuration starts PostgreSQL with pgvector support.

The local database is exposed on port:

```text
5433
```

---

## 3. Backend Setup

Move to the backend:

```bash
cd backend
```

Create a Python virtual environment:

### Windows

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### macOS / Linux

```bash
python3 -m venv venv
source venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

---

## 4. Backend Environment Variables

Create a `.env` file from the provided example.

### Windows

```powershell
Copy-Item .env.example .env
```

### macOS / Linux

```bash
cp .env.example .env
```

Configure the values inside `.env`.

Example:

```env
DATABASE_URL=postgresql://postgres:YOUR_PASSWORD@localhost:5433/nagham_ai

JWT_SECRET_KEY=YOUR_JWT_SECRET_KEY

EMAIL_ADDRESS=your_email@gmail.com
EMAIL_APP_PASSWORD=YOUR_GOOGLE_APP_PASSWORD

OPENAI_API_KEY=

GOOGLE_CLIENT_ID=YOUR_GOOGLE_CLIENT_ID
GOOGLE_CLIENT_SECRET=YOUR_GOOGLE_CLIENT_SECRET

FRONTEND_URL=http://localhost:3000
```

Do not commit the real `.env` file.

The current semantic embedding implementation runs locally and does not require OpenAI API credits.

---

## 5. Database Migrations

With the backend virtual environment active:

```bash
alembic upgrade head
```

This creates/updates the required database schema.

---

## 6. Ollama Setup

Nagham AI uses a local Ollama model for AI query analysis and RAG response generation.

Install Ollama, then pull the model:

```bash
ollama pull qwen2.5:3b
```

Make sure Ollama is running before using the AI Assistant.

You can verify the installed models with:

```bash
ollama list
```

---

## 7. Run the Backend

From the `backend` directory:

```bash
uvicorn app.main:app --reload
```

Backend:

```text
http://127.0.0.1:8000
```

Swagger API documentation:

```text
http://127.0.0.1:8000/docs
```

---

## 8. Frontend Setup

Open another terminal and move to the frontend:

```bash
cd frontend
```

Install dependencies:

```bash
npm install
```

Create the frontend environment file.

### Windows

```powershell
Copy-Item .env.example .env.local
```

### macOS / Linux

```bash
cp .env.example .env.local
```

The default configuration is:

```env
NEXT_PUBLIC_API_URL=http://127.0.0.1:8000
```

---

## 9. Run the Frontend

```bash
npm run dev
```

Open:

```text
http://localhost:3000
```

---

# Running the Full Development Environment

Normally, three services should be available:

```text
PostgreSQL / pgvector
        ↓
FastAPI Backend
        ↓
Next.js Frontend
```

Ollama should also be running when using the AI Assistant.

Typical startup sequence:

### Terminal 1 — Database

```bash
docker compose up -d
```

### Terminal 2 — Backend

```powershell
cd backend
.\venv\Scripts\Activate.ps1
uvicorn app.main:app --reload
```

### Terminal 3 — Frontend

```bash
cd frontend
npm run dev
```

---

# API Documentation

FastAPI automatically provides interactive Swagger documentation.

After starting the backend, visit:

```text
http://127.0.0.1:8000/docs
```

The API includes endpoints related to areas such as:

- Authentication
- Users
- Songs
- Music metadata
- Semantic search
- AI Assistant

---

# AI Search Pipeline

A simplified representation of the current AI pipeline is:

```text
Natural Language Query
        ↓
Intent Extraction
        ↓
Structured Constraints + Semantic Meaning
        ↓
LangGraph Routing
        ↓
┌──────────────┬──────────────┬──────────────┐
│  Structured  │   Semantic   │    Hybrid    │
│    Search    │    Search    │    Search    │
└──────────────┴──────────────┴──────────────┘
        ↓
Metadata-aware Ranking
        ↓
Relevant Songs
        ↓
RAG Context
        ↓
Local LLM
        ↓
Grounded Response
```

---

# Example AI Queries

Try requests such as:

```text
أعطني أغاني لأم كلثوم
```

```text
أريد أغاني على مقام البياتي
```

```text
أريد أغاني من ألحان بليغ حمدي
```

```text
أريد أغنية حزينة عن الفراق
```

```text
أريد أغنية حزينة عن الفراق على مقام الصبا
```

```text
أغاني فيها انتقال إلى مقام الصبا
```

```text
اقترح لي أغنيتين عن الاشتياق للملحن محمد عبد الوهاب أو لفيروز
```

These examples exercise different combinations of structured, semantic, and hybrid retrieval.

---

# Security Notes

The repository intentionally excludes:

- `.env`
- API keys
- JWT secrets
- Email app passwords
- OAuth secrets
- Python virtual environments
- `node_modules`
- Next.js build files

Use the provided `.env.example` files to configure your own environment.

Never commit real credentials.

---

# Current Project Scope

Nagham AI currently focuses on intelligent music discovery and structured Oriental music knowledge.

Possible future extensions include:

- Larger verified Arabic music datasets
- More detailed maqam-transition analysis
- Richer rhythm analysis
- Music notation
- Audio samples
- Source-backed music knowledge
- Lyrics phrase discovery
- More advanced RAG
- Improved local language models
- Personalized recommendations

---

# Author

**Essam H. Abu Shahla**

Computer Systems Engineering / Software Engineering  
Al-Azhar University – Gaza

---

## Academic Project

Nagham AI was developed as an AI/software engineering project exploring how structured musical knowledge, semantic retrieval, vector embeddings, local language models, and AI-agent orchestration can be combined in a practical Arabic music application.
