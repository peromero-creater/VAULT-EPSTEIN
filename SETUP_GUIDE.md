# Quick Setup Guide

## Prerequisites
- Python 3.11+
- Node.js 18+
- API Keys (optional but recommended):
  - OpenAI API Key
  - Google AI API Key

## Backend Setup

1. **Install Python Dependencies**
```powershell
cd backend
pip install -r requirements.txt
```

2. **Configure Environment (Optional)**
```powershell
# Copy the example env file
cp ../.env.example .env

# Edit .env and add your API keys
# OPENAI_API_KEY=sk-...
# GOOGLE_AI_API_KEY=...
```

3. **Initialize Database**
```powershell
# The database will be created automatically on first run
python main.py
```

4. **Ingest Real Documents**
```powershell
cd ../ingestion

# Dry run first to test (doesn't modify database)
python ingest_all.py --source documentcloud --limit 10 --dry-run

# Real ingestion (start with small batch)
python ingest_all.py --source documentcloud --limit 50

# Ingest from Justice.gov
python ingest_all.py --source justice --limit 20

# Ingest from all sources
python ingest_all.py --source all --limit 100
```

## Frontend Setup

1. **Install Dependencies**
```powershell
cd frontend
npm install
```

2. **Run Development Server**
```powershell
npm run dev
```

## Features Now Available

### ✅ Real Document Integration
- DocumentCloud API integration
- Justice.gov scraper
- Automatic text extraction
- External source linking

### ✅ AI-Powered Analysis
- OpenAI GPT-4 integration
- Google Gemini fallback
- Entity extraction
- Relationship discovery
- Narrative generation

**AI Endpoints:**
- `POST /api/analyze-document/{doc_id}` - Extract entities from document
- `GET /api/document-narrative/{doc_id}` - Get AI summary
- `POST /api/discover-connections/{entity_name}` - Find hidden relationships
- `GET /api/country-summary/{country_code}` - Country intelligence summary

### ✅ Enhanced UI
- Search with pagination (10 results per page)
- 47+ countries on interactive 3D globe
- Country search bar
- AI-generated narratives
- External source links

## Testing

1. **Start Backend** (in backend folder):
```powershell
uvicorn main:app --reload
```

2. **Start Frontend** (in frontend folder):
```powershell
npm run dev
```

3. **Visit Pages:**
- http://localhost:3000/search - Search documents
- http://localhost:3000/countries - 3D globe
- http://localhost:3000/connections - Entity connections

## Next Steps

- [ ] Add more document sources (Google Pinpoint, jmail.world)
- [ ] Implement AI analysis buttons in UI
- [ ] Add document viewer component
- [ ] Set up background ingestion service
