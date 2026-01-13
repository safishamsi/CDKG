# 🚀 QUICK START GUIDE

## Get Running in 5 Minutes!

### Prerequisites
- ✅ Python 3.8+
- ✅ Neo4j Desktop installed and running
- ✅ Anthropic API key

---

## Setup Steps

### 1️⃣ Setup Environment

```bash
# Create project directory
mkdir cdkg-system
cd cdkg-system

# Copy all the provided files here
# (config.py, data_loader.py, embedding_generator.py, etc.)

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2️⃣ Configure Neo4j Desktop

1. Open Neo4j Desktop
2. Create a new database (if not already done)
3. **Start the database** ⚠️ Important!
4. Note your password

### 3️⃣ Setup Configuration

```bash
# Copy template
cp .env.template .env

# Edit .env with your text editor
# Set these values:
#   NEO4J_PASSWORD=your_neo4j_password
#   ANTHROPIC_API_KEY=sk-ant-your_key_here
```

### 4️⃣ Add Your Data

```bash
# Create data directory
mkdir -p data

# Copy your cdl_db folder
cp -r /path/to/your/cdl_db data/

# Verify files exist
ls data/cdl_db/
# Should show: Speaker.csv, Talk.csv, etc.
```

### 5️⃣ Run Setup Check

```bash
python setup.py
```

**Expected output**: All checks should show ✅

---

## Run the System

### Option A: Complete Pipeline (Recommended)

```bash
python run_pipeline.py
```

This runs everything:
- Loads data into Neo4j
- Generates embeddings
- Builds vector index
- Tests the system

**Time**: 3-5 minutes

### Option B: Step by Step

```bash
# Step 1: Load data
python data_loader.py

# Step 2: Generate embeddings
python embedding_generator.py

# Step 3: Build vector store
python vector_store.py

# Step 4: Test RAG
python rag_system.py
```

---

## Test It!

```python
from rag_system import RAGSystem

rag = RAGSystem()
result = rag.query("What talks discuss knowledge graphs?")
print(result['answer'])
rag.close()
```

---

## Common Issues

### "Connection refused"
→ Start your Neo4j database in Neo4j Desktop

### "Module not found"
→ Run: `pip install -r requirements.txt`

### "API key not set"
→ Add your Anthropic API key to `.env`

### "cdl_db not found"
→ Copy your `cdl_db` folder to `data/cdl_db/`

---

## You're Done! 🎉

Your Knowledge Graph RAG system is ready!

**Next**: Check `README.md` for detailed documentation.
