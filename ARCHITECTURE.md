# 🚀 Complete Knowledge Graph RAG System - Neo4j Desktop Edition

## 📁 Project Structure

```
cdkg-system/
├── config/
│   └── settings.py          # Configuration management
├── data/
│   └── cdl_db/             # CSV files (copy your existing cdl_db here)
├── embeddings/             # Generated embeddings storage
├── src/
│   ├── __init__.py
│   ├── data_loader.py      # Step 1: Load CSV → Neo4j
│   ├── embedding_generator.py  # Step 2: Generate embeddings
│   ├── vector_store.py     # Step 3: FAISS index management
│   └── rag_system.py       # Step 4: Complete RAG retrieval
├── .env                    # Environment variables
├── requirements.txt        # Dependencies
├── setup.py               # One-time setup script
└── run_pipeline.py        # Complete pipeline runner
```

## 🎯 Architecture Overview

### Pipeline Flow:
1. **Data Loading** → Load CSVs into Neo4j Desktop
2. **Embedding Generation** → Generate embeddings for all nodes
3. **Vector Store** → Create FAISS index for semantic search
4. **RAG System** → Hybrid retrieval (Graph + Semantic + LLM)

### Components:
- **Neo4j Desktop** (local graph database)
- **Sentence Transformers** (embeddings)
- **FAISS** (vector similarity search)
- **Anthropic Claude** (LLM for generation)

---

## 📋 Prerequisites

### 1. Neo4j Desktop Setup
1. Download Neo4j Desktop: https://neo4j.com/download/
2. Create a new project
3. Create a new database (name: `cdkg`)
4. Start the database
5. Note the connection details:
   - Bolt URL: `bolt://localhost:7687`
   - Username: `neo4j`
   - Password: (set during database creation)

### 2. Python Environment
```bash
# Create virtual environment
python -m venv venv

# Activate
# On macOS/Linux:
source venv/bin/activate
# On Windows:
venv\Scripts\activate
```

---

## ⚙️ Installation

All setup instructions are in the individual files I'll create next.

---

## 🏃 Quick Start

```bash
# 1. Setup (one-time)
python setup.py

# 2. Run complete pipeline
python run_pipeline.py

# 3. Test retrieval
python -c "from src.rag_system import RAGSystem; rag = RAGSystem(); print(rag.query('What are knowledge graphs?'))"
```

---

## 📊 Expected Results

- **Nodes**: ~897 (40 Speakers, 383 Talks, 469 Tags, 2 Events, 3 Categories)
- **Relationships**: ~677
- **Embeddings**: 897 vectors (384-dimensional)
- **FAISS Index**: ~897 vectors indexed

---

Files will be created in the next steps...
