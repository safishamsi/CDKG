# 🚀 Complete Knowledge Graph RAG System

A production-ready Retrieval-Augmented Generation (RAG) system combining Neo4j graph database, semantic search with FAISS, and Claude LLM for intelligent question answering.

## 📋 Table of Contents

- [Features](#features)
- [Architecture](#architecture)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Detailed Usage](#detailed-usage)
- [Project Structure](#project-structure)
- [Configuration](#configuration)
- [Troubleshooting](#troubleshooting)

---

## ✨ Features

- **Hybrid Retrieval**: Combines semantic search (FAISS) + graph traversal (Neo4j) + keyword matching
- **Multi-Modal Search**: Search across Speakers, Talks, Tags, Events, and Categories
- **Graph Intelligence**: Leverages relationship information for better context
- **Production-Ready**: Proper error handling, logging, and configuration management
- **Neo4j Desktop Support**: Works with locally installed Neo4j (no Docker required)
- **Batch Processing**: Efficient loading of large datasets
- **Extensible**: Easy to add new node types or relationship types

---

## 🏗️ Architecture

```
┌─────────────────┐
│   User Query    │
└────────┬────────┘
         │
    ┌────▼────────────────────────────────┐
    │      RAG System (rag_system.py)     │
    └────┬────────────────────────────┬───┘
         │                            │
    ┌────▼─────────┐         ┌────────▼────────┐
    │   Semantic   │         │  Graph Traversal│
    │    Search    │         │   (Neo4j Cypher)│
    │   (FAISS)    │         └─────────────────┘
    └──────────────┘
         │
    ┌────▼──────────────────────────────────┐
    │  Vector Store (vector_store.py)       │
    │  - FAISS Index                        │
    │  - 897 embeddings (384-dim)           │
    └───────────────────────────────────────┘
         │
    ┌────▼──────────────────────────────────┐
    │  Embedding Generator                  │
    │  (embedding_generator.py)             │
    │  - Sentence Transformers              │
    └───────────────────────────────────────┘
         │
    ┌────▼──────────────────────────────────┐
    │  Data Loader (data_loader.py)         │
    │  - CSV → Neo4j                        │
    │  - Batch processing                   │
    └───────────────────────────────────────┘
         │
    ┌────▼──────────────────────────────────┐
    │  Neo4j Desktop                        │
    │  - 897 nodes                          │
    │  - 677 relationships                  │
    └───────────────────────────────────────┘
```

---

## 📋 Prerequisites

### 1. Neo4j Desktop

1. **Download**: [https://neo4j.com/download/](https://neo4j.com/download/)
2. **Install** Neo4j Desktop
3. **Create a new project**
4. **Create a database**:
   - Name: `cdkg` (or any name you prefer)
   - Version: 5.x (recommended)
   - Set a password (you'll need this for `.env`)
5. **Start the database**
6. **Note the connection details**:
   - Bolt URL: Usually `bolt://localhost:7687`
   - Username: `neo4j`
   - Password: (what you set)

### 2. Python Environment

- **Python 3.8+** required
- **Virtual environment** recommended

```bash
# Create virtual environment
python -m venv venv

# Activate
# macOS/Linux:
source venv/bin/activate
# Windows:
venv\Scripts\activate
```

### 3. API Keys

- **Anthropic API Key**: Get from [https://console.anthropic.com/](https://console.anthropic.com/)

---

## 📦 Installation

### Step 1: Clone/Download the Project

```bash
# If you have the files
cd cdkg-system

# Or create a new directory
mkdir cdkg-system
cd cdkg-system
```

### Step 2: Install Dependencies

```bash
pip install -r requirements.txt
```

**Note**: This will install:
- `neo4j` - Neo4j Python driver
- `polars` - Fast dataframe library
- `sentence-transformers` - For embeddings
- `faiss-cpu` - Vector similarity search
- `anthropic` - Claude API client
- `python-dotenv` - Environment variables
- And other dependencies

### Step 3: Setup Environment

```bash
# Copy template
cp .env.template .env

# Edit .env and fill in:
# - NEO4J_PASSWORD (from Neo4j Desktop)
# - ANTHROPIC_API_KEY (from Anthropic Console)
nano .env  # or use any text editor
```

### Step 4: Copy Data Files

```bash
# Create data directory
mkdir -p data

# Copy your cdl_db directory
cp -r /path/to/your/cdl_db data/

# Verify structure
ls data/cdl_db/
# Should show: Speaker.csv, Talk.csv, Tag.csv, etc.
```

### Step 5: Run Setup Check

```bash
python setup.py
```

This will verify:
- ✅ Python version
- ✅ All dependencies installed
- ✅ .env file configured
- ✅ Neo4j connection works
- ✅ Data files present

---

## 🚀 Quick Start

### One-Command Pipeline

```bash
python run_pipeline.py
```

This runs all steps:
1. ✅ Load data into Neo4j (40 speakers, 383 talks, 469 tags, etc.)
2. ✅ Generate embeddings (897 vectors)
3. ✅ Build FAISS index
4. ✅ Test RAG system

**Expected time**: 2-5 minutes (depending on your machine)

### Test RAG System

```python
from rag_system import RAGSystem

rag = RAGSystem()
result = rag.query("What talks discuss knowledge graphs?")
print(result['answer'])

rag.close()
```

---

## 📖 Detailed Usage

### Step-by-Step Execution

If you prefer to run each step individually:

#### 1. Load Data into Neo4j

```bash
python data_loader.py
```

**What it does**:
- Connects to Neo4j Desktop
- Creates constraints for data integrity
- Loads 897 nodes (Speakers, Talks, Tags, Events, Categories)
- Creates 677 relationships
- Uses batch processing for efficiency

**Output**:
```
🚀 LOADING DATA INTO NEO4J DESKTOP
======================================================================
🔌 Connecting to Neo4j Desktop...
   ✅ Connected successfully!

📊 Loading Speakers...
   ✅ Loaded 40 speakers

📊 Loading Talks...
   ✅ Loaded 383 talks

... (continues for all node types)

📈 Database Statistics:
   Speaker        :    40
   Talk           :   383
   Tag            :   469
   Event          :     2
   Category       :     3
   Relationships  :   677
```

#### 2. Generate Embeddings

```bash
python embedding_generator.py
```

**What it does**:
- Loads Sentence Transformer model (BAAI/bge-small-en-v1.5)
- Extracts text from each node
- Generates 384-dimensional embeddings
- Saves embeddings and metadata to `embeddings/`

**Output**:
```
🚀 GENERATING EMBEDDINGS
======================================================================
🤖 Loading embedding model: BAAI/bge-small-en-v1.5
   ✅ Model loaded (dim: 384)

📊 Extracting Speakers...
   ✅ Extracted 40 speakers

🧠 Generating Speaker embeddings...
[Progress bar]

... (continues for all node types)

📈 Embedding Generation Summary:
   Total embeddings: 897
   Embedding dimension: 384
```

#### 3. Build Vector Store

```bash
python vector_store.py
```

**What it does**:
- Loads embeddings from disk
- Creates FAISS index (exact search)
- Saves index for fast loading

**Output**:
```
🚀 BUILDING VECTOR STORE
======================================================================
📂 Loading embeddings...
   ✅ Loaded 897 embeddings (dim=384)

🔨 Creating FAISS index (type: flat)...
   ✅ Index created with 897 vectors

💾 Saved index to faiss_index.bin
```

#### 4. Use RAG System

```python
from rag_system import RAGSystem

# Initialize (loads all components)
rag = RAGSystem()

# Query
result = rag.query(
    "What talks discuss knowledge graphs?",
    top_k=5,
    verbose=True
)

# Access results
print(result['answer'])         # LLM-generated answer
print(result['context'])        # Retrieved context
print(result['retrieval_results'])  # Raw retrieval data

# Close connection
rag.close()
```

**Advanced Usage**:

```python
# Multiple queries
queries = [
    "Who spoke about graph thinking?",
    "What are the main categories of talks?",
    "Tell me about semantic web talks"
]

for query in queries:
    result = rag.query(query, top_k=5)
    print(f"Q: {query}")
    print(f"A: {result['answer']}\n")
```

---

## 📁 Project Structure

```
cdkg-system/
├── config.py                 # Configuration management
├── data_loader.py           # Step 1: CSV → Neo4j
├── embedding_generator.py   # Step 2: Generate embeddings
├── vector_store.py          # Step 3: FAISS index
├── rag_system.py            # Step 4: Complete RAG
├── setup.py                 # Setup verification
├── run_pipeline.py          # Complete pipeline runner
├── requirements.txt         # Dependencies
├── .env.template           # Environment template
├── .env                    # Your configuration (create this)
├── README.md               # This file
├── ARCHITECTURE.md         # Architecture documentation
│
├── data/
│   └── cdl_db/            # CSV files (you copy here)
│       ├── Speaker.csv
│       ├── Talk.csv
│       ├── Tag.csv
│       ├── Event.csv
│       ├── Category.csv
│       ├── GIVES_TALK_Speaker_Talk.csv
│       ├── IS_PART_OF_Talk_Event.csv
│       ├── IS_CATEGORIZED_AS_Talk_Category.csv
│       └── IS_DESCRIBED_BY_Talk_Tag.csv
│
└── embeddings/            # Generated embeddings (auto-created)
    ├── speaker_embeddings.npy
    ├── talk_embeddings.npy
    ├── tag_embeddings.npy
    ├── event_embeddings.npy
    ├── category_embeddings.npy
    ├── all_embeddings.npy
    ├── index_mapping.json
    ├── faiss_index.bin
    └── faiss_index_info.json
```

---

## ⚙️ Configuration

### `.env` File

```bash
# Neo4j Desktop Connection
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_neo4j_password_here

# Anthropic API
ANTHROPIC_API_KEY=sk-ant-...

# Embedding Model (optional, has defaults)
EMBEDDING_MODEL=BAAI/bge-small-en-v1.5

# Paths (optional, has defaults)
EMBEDDINGS_DIR=embeddings
DATA_DIR=data
```

### `config.py`

Modify `config.py` to change:
- Embedding model
- Batch sizes
- LLM parameters (model, temperature, max_tokens)
- Paths

---

## 🔧 Troubleshooting

### "Connection refused" Error

**Problem**: Cannot connect to Neo4j

**Solutions**:
1. Check if Neo4j Desktop is running
2. Check if your database is **started** (not just created)
3. Verify password in `.env` matches Neo4j
4. Verify URI is `bolt://localhost:7687`

### "No module named 'neo4j'" Error

**Problem**: Missing dependencies

**Solution**:
```bash
pip install -r requirements.txt
```

### "cdl_db not found" Error

**Problem**: Data files missing

**Solution**:
```bash
# Copy your cdl_db to the data directory
cp -r /path/to/cdl_db data/

# Verify
ls data/cdl_db/
```

### "ANTHROPIC_API_KEY not set" Error

**Problem**: API key missing from .env

**Solution**:
1. Get API key from https://console.anthropic.com/
2. Add to `.env`: `ANTHROPIC_API_KEY=sk-ant-...`

### Slow Embedding Generation

**Problem**: Embeddings taking too long

**Solutions**:
1. Reduce batch size in `config.py`:
   ```python
   class EmbeddingConfig(BaseModel):
       batch_size: int = 16  # Reduce from 32
   ```
2. Use a smaller model:
   ```bash
   # In .env
   EMBEDDING_MODEL=all-MiniLM-L6-v2
   ```

### Out of Memory Error

**Problem**: Not enough RAM

**Solutions**:
1. Process in smaller batches
2. Use a smaller embedding model
3. Close other applications

---

## 📊 Expected Results

### Database Statistics
- **Nodes**: 897 total
  - 40 Speakers
  - 383 Talks
  - 469 Tags
  - 2 Events
  - 3 Categories
- **Relationships**: 677 total
  - 41 GIVES_TALK
  - 37 IS_PART_OF
  - 37 IS_CATEGORIZED_AS
  - 562 IS_DESCRIBED_BY

### Embeddings
- **Total vectors**: 897
- **Dimensions**: 384 (BAAI/bge-small-en-v1.5)
- **Storage**: ~1.4 MB
- **Index**: FAISS Flat (exact search)

### Performance
- **Data loading**: ~30-60 seconds
- **Embedding generation**: ~1-3 minutes
- **Index building**: ~1-2 seconds
- **Query time**: ~1-3 seconds (including LLM generation)

---

## 🎯 Next Steps

1. **Explore Neo4j Browser**:
   - Open: http://localhost:7474
   - Login with your credentials
   - Try queries:
     ```cypher
     MATCH (s:Speaker)-[:GIVES_TALK]->(t:Talk)
     RETURN s.name, t.title
     LIMIT 10
     ```

2. **Customize the System**:
   - Modify prompts in `rag_system.py`
   - Add new retrieval strategies
   - Experiment with different embedding models

3. **Build an Application**:
   - Create a web interface (Flask/FastAPI)
   - Add conversational memory
   - Implement user feedback loops

---

## 📚 Additional Resources

- **Neo4j Documentation**: https://neo4j.com/docs/
- **Sentence Transformers**: https://www.sbert.net/
- **FAISS**: https://github.com/facebookresearch/faiss
- **Anthropic Claude**: https://docs.anthropic.com/

---

## ✨ Success!

If you've made it this far, congratulations! 🎉

You now have a fully functional Knowledge Graph RAG system!

Try asking it questions about the Connected Data World talks and enjoy exploring the knowledge graph! 🚀
