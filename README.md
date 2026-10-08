# DocChat — RAG Chatbot

A full-stack document Q&A chatbot. Upload any document (PDF, DOCX, TXT, CSV, MD) and chat with an AI that answers questions grounded strictly in that document.

## Stack

| Layer | Tech |
|-------|------|
| Frontend | React + Vite |
| Backend | Python + FastAPI |
| AI Framework | LangChain |
| LLM | Mistral-7B-Instruct (HuggingFace free API) |
| Embeddings | `all-MiniLM-L6-v2` (sentence-transformers, free) |
| Vector Store | FAISS (local, free) |

---

## Setup

### 1. Get a Free HuggingFace API Token

1. Go to [https://huggingface.co/settings/tokens](https://huggingface.co/settings/tokens)
2. Create a new token (Read access is enough)
3. Copy the token

### 2. Configure Backend

```bash
cd backend
copy .env.example .env
# Open .env and paste your token:
# HUGGINGFACEHUB_API_TOKEN=hf_xxxxxxxxxxxxxx
```

### 3. Install Backend Dependencies

```bash
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

### 4. Install Frontend Dependencies

```bash
cd frontend
npm install
```

---

## Running the App

### Start Backend (Terminal 1)

```bash
cd backend
venv\Scripts\activate
uvicorn main:app --reload --port 8000
```

### Start Frontend (Terminal 2)

```bash
cd frontend
npm run dev
```

Open [http://localhost:5173](http://localhost:5173) in your browser.

---

## Project Structure

```
Chatbot/
├── backend/
│   ├── main.py              # FastAPI app + LangChain RAG pipeline
│   ├── requirements.txt
│   ├── .env.example         # Copy to .env and add your token
│   └── uploads/             # Uploaded files (auto-created)
└── frontend/
    └── src/
        ├── App.jsx              # Main layout + state management
        ├── api.js               # Axios client
        └── components/
            ├── FileUploadZone.jsx
            ├── ChatMessage.jsx
            └── ChatInput.jsx
```

---

## How It Works

1. **Upload** — File is sent to FastAPI, loaded with LangChain document loaders
2. **Chunk & Embed** — Document is split into chunks and embedded using `all-MiniLM-L6-v2`
3. **FAISS Index** — Embeddings stored in a local FAISS vector store
4. **Chat** — Questions trigger semantic search over the document; top-4 chunks are sent to Mistral-7B as context
5. **Memory** — Conversation history is retained per session
