# LangGraph Orchestrator Integration

## Overview

The system now includes a **LangGraph orchestrator** that provides intelligent query routing and tool orchestration for hybrid RAG (Retrieval Augmented Generation) with multi-hop reasoning capabilities.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    USER QUERY                               │
│         "How is Paco Nathan related to knowledge graphs?"   │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│           LANGGRAPH ORCHESTRATOR                             │
│                                                              │
│  1. Query Classification (LLM-based)                        │
│     - Semantic: Needs similarity search                     │
│     - Graph: Needs relationship traversal                   │
│     - Multi-hop: Needs complex reasoning                    │
│     - Hybrid: Needs both semantic + graph                   │
│                                                              │
│  2. Intelligent Routing                                     │
│     ┌──────────┐  ┌──────────┐  ┌──────────┐                │
│     │Semantic  │  │  Graph   │  │Multi-hop │                │
│     │ Search   │  │Traversal │  │Reasoning │                │
│     └────┬─────┘  └────┬─────┘  └────┬─────┘                │
│          │            │              │                       │
│          └────────────┼──────────────┘                       │
│                       │                                      │
│              Context Fusion                                  │
└───────────────────────┬──────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│              CLAUDE SONNET (Anthropic)                       │
│         Generates final answer with context                  │
└─────────────────────────────────────────────────────────────┘
```

## Features

### 1. **Semantic Similarity Search** (Vector-based)
- Uses FAISS vector index for semantic similarity
- Finds talks, speakers, tags by meaning, not exact keywords
- Powered by sentence-transformers embeddings

### 2. **Graph Traversal** (Knowledge Graph)
- Traverses Neo4j relationships
- Finds connections: Speaker → Talks → Tags → Other Speakers
- Supports configurable depth (1-3 hops)

### 3. **Multi-hop Reasoning**
- Finds paths between entities
- Answers complex relationship questions
- Example: "How is speaker X related to topic Y?"

### 4. **Transcript Search** (Full-text with timestamps)
- Searches actual talk transcripts
- Returns timestamped segments
- Provides video links with time codes

### 5. **Hybrid Retrieval**
- Combines all methods for comprehensive answers
- Semantic similarity + Graph structure + Transcript content

## Usage

### Basic Usage

```python
from rag_system import RAGSystem
from langgraph_orchestrator import LangGraphOrchestrator

# Initialize
rag = RAGSystem()
orchestrator = LangGraphOrchestrator(rag)

# Query
result = orchestrator.query(
    "What did Paco Nathan say about graph thinking?",
    max_hops=2,
    use_tools=False  # Use state graph
)

print(result['answer'])
```

### Agent Mode (with LangChain Tools)

```python
# Use LLM with tools for autonomous tool calling
result = orchestrator.query(
    "How is Paco Nathan related to knowledge graphs?",
    use_tools=True  # Agent mode
)
```

## Query Types

### 1. Semantic Queries
**Example**: "What talks discuss semantic technology?"
- Uses: Vector similarity search
- Best for: Finding content by meaning/topic

### 2. Graph Queries
**Example**: "What talks did Juan Sequeda give?"
- Uses: Graph traversal from speaker node
- Best for: Relationship queries

### 3. Multi-hop Queries
**Example**: "How is Paco Nathan related to knowledge graphs?"
- Uses: Path finding between entities
- Best for: Complex relationship discovery

### 4. Hybrid Queries
**Example**: "What did Paco Nathan say about graph thinking?"
- Uses: Semantic + Graph + Transcript search
- Best for: Comprehensive answers

## LangChain Tools

The orchestrator exposes these tools for agent-based queries:

1. **`semantic_search(query, top_k=5)`**
   - Vector similarity search
   - Returns semantically similar nodes

2. **`graph_traversal(entity_names, max_hops=2)`**
   - Graph relationship traversal
   - Returns connected nodes

3. **`transcript_search(query, limit=5)`**
   - Full-text transcript search
   - Returns timestamped segments

4. **`multi_hop_reasoning(start_entity, target_entity, max_hops=3)`**
   - Path finding between entities
   - Returns relationship paths

5. **`keyword_search(query, limit=10)`**
   - Keyword-based Neo4j search
   - Returns exact matches

## Configuration

The orchestrator uses:
- **Anthropic Claude 3.5 Sonnet** for answer generation
- **FAISS** for vector similarity
- **Neo4j** for graph traversal
- **LangGraph** for workflow orchestration
- **LangChain** for tool integration

## Benefits

1. **Intelligent Routing**: Automatically selects best retrieval method
2. **Multi-hop Reasoning**: Answers complex relationship questions
3. **Hybrid Retrieval**: Combines vectors + graphs + transcripts
4. **Tool-based Agents**: Supports autonomous tool calling
5. **State Management**: LangGraph manages query state and workflow

## Example Output

```python
{
    'query': 'What did Paco Nathan say about graph thinking?',
    'query_type': 'hybrid',
    'answer': 'Based on the transcript...',
    'semantic_results': [...],
    'graph_results': [...],
    'transcript_results': [
        {
            'title': 'Graph Thinking',
            'transcript_snippet': '...',
            'timestamp': '00:05:23',
            'timestamp_seconds': 323
        }
    ],
    'multi_hop_paths': []
}
```

## Next Steps

1. Test the orchestrator with various query types
2. Fine-tune query classification
3. Add more sophisticated multi-hop reasoning
4. Integrate with frontend API

