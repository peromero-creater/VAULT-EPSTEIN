# 🚀 Quick Start Guide - Vault Epstein

## 1. Configure Grok AI (Already Done!)

Your Grok API key is configured in `.env` file. Grok has specialized knowledge of Epstein case files and connections.

```bash
AI_PROVIDER=grok  ✅ 
GROK_API_KEY=your_grok_api_key_here  ✅
```

## 2. Ingest Real Documents

### DocumentCloud (Recommended First)
```powershell
cd ingestion
python ingest_all.py --source documentcloud --limit 50
```

### Justice.gov
```powershell
python ingest_all.py --source justice --limit 20
```

### jmail.world (Drive, Photos, Flights)
```powershell
python ingest_all.py --source jmail --limit 30
```

### All Sources at Once
```powershell
python ingest_all.py --source all --limit 100
```

## 3. Test Dry Run First (Recommended)
```powershell
# See what documents are available without ingesting
python ingest_all.py --source documentcloud --limit 10 --dry-run
```

## 4. Start the Application

### Backend
```powershell
cd backend
uvicorn main:app --reload
```

### Frontend  
```powershell
cd frontend
npm run dev
```

## 5. Access the Application

- **Search:** http://localhost:3000/search
- **Countries:** http://localhost:3000/countries (47+ countries with search!)
- **Connections:** http://localhost:3000/connections

## 6. Test Grok AI

Once documents are ingested, search for names and you'll see Grok-powered narratives:

- Search "Trump" → Grok generates connections
- Search "Clinton" → Grok analyzes flight logs  
- Search "Maxwell" → Grok finds relationships

## Available Document Sources

✅ **DocumentCloud** - Public Epstein documents
✅ **Justice.gov** - Official DOJ files
✅ **jmail.world** - Drive, Photos, Flights
✅ **Google Pinpoint** - Requires manual export

## Grok API Features

- **Specialized Epstein Knowledge**
- **Connection Discovery**
- **Flight Log Analysis**
- **Entity Relationship Mapping**
- **Country Intelligence Summaries**

Grok is specifically trained on Epstein case files and has deep knowledge of the connections!
