# 📁 VAULT: EPSTEIN — Public Record Investigation Platform

![Social Preview](https://raw.githubusercontent.com/peromero-creater/VAULT-EPSTEIN/main/frontend/public/epstein.png)

> **"The truth is in the data."**
> An advanced, open-source investigative platform designed to explore 3.5M+ pages of the Jeffrey Epstein document releases.

---

## 🛠 Features

- **🔍 Page-Level Search**: High-speed Postgres Full-Text search to find needles in a haystack of millions of pages.
- **🛡️ Aggressive PII Masking**: Automated sanitization of emails, phone numbers, and addresses.
- **🕵️ Entity Extraction**: High-speed NER (Named Entity Recognition) identifying the people, organizations, and events mentioned.

---

## 🏗 Local Setup (Docker-less)

This project has been streamlined to run directly on your machine using **Postgres** for data and search.

### 1. Requirements
- Python 3.10+
- Node.js 18+
- Postgres Database (Local or Cloud like [Neon.tech](https://neon.tech))

### 2. Backend Setup
```bash
cd backend
python -m venv venv
# Windows: venv\Scripts\activate
# Mac/Linux: source venv/bin/activate
pip install -r requirements.txt
python main.py
```

### 3. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

### 4. Ingest Data
Drop your PDF files into `./data/files` and start the processor:
```bash
python ingestion/main.py
```

---

## 🛡 Safety & Compliance

This platform is for **investigative purposes only**. It automatically masks PII to protect privacy.

- **Emails**: Replaced with `[EMAIL]`
- **Phones**: Replaced with `[PHONE]`
- **Addresses**: Replaced with `[ADDRESS]`

---

## 🔗 Credits
Built for the community. Share the truth.
