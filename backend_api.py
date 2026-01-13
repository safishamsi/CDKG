"""
FastAPI Backend for RAG Chatbot
Exposes LangGraph orchestrator via REST API
"""

import os
# Disable tensorflow imports to avoid protobuf issues
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
os.environ['TRANSFORMERS_NO_TF'] = '1'

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import uvicorn

from rag_system import RAGSystem
from langgraph_orchestrator import LangGraphOrchestrator

# Initialize FastAPI app
app = FastAPI(
    title="CDKG RAG Chatbot API",
    description="Hybrid RAG system with LangGraph orchestration",
    version="1.0.0"
)

# CORS middleware for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],  # React dev servers
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global RAG system instance
rag_system = None
orchestrator = None


class QueryRequest(BaseModel):
    """Request model for chat queries"""
    query: str
    max_hops: Optional[int] = 2
    use_tools: Optional[bool] = False


class QueryResponse(BaseModel):
    """Response model for chat queries"""
    query: str
    answer: str
    query_type: Optional[str] = None
    retrieval_stats: Dict[str, int]
    sources: Optional[List[Dict[str, Any]]] = None
    error: Optional[str] = None


@app.on_event("startup")
async def startup_event():
    """Initialize RAG system on startup"""
    global rag_system, orchestrator
    try:
        print("🚀 Initializing RAG system...")
        rag_system = RAGSystem()
        orchestrator = LangGraphOrchestrator(rag_system)
        print("✅ RAG system ready!")
    except Exception as e:
        print(f"❌ Error initializing RAG system: {e}")
        raise


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    global orchestrator
    if orchestrator:
        orchestrator.close()


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "ok",
        "service": "CDKG RAG Chatbot API",
        "version": "1.0.0"
    }


@app.get("/health")
async def health():
    """Health check with system status"""
    global rag_system, orchestrator
    return {
        "status": "healthy",
        "rag_system_initialized": rag_system is not None,
        "orchestrator_initialized": orchestrator is not None
    }


@app.post("/api/query", response_model=QueryResponse)
async def query(request: QueryRequest):
    """
    Process a chat query using LangGraph orchestrator
    
    Args:
        request: Query request with query text and options
        
    Returns:
        Query response with answer and metadata
    """
    global orchestrator
    
    if not orchestrator:
        raise HTTPException(status_code=503, detail="RAG system not initialized")
    
    try:
        # Process query
        result = orchestrator.query(
            query=request.query,
            max_hops=request.max_hops,
            use_tools=request.use_tools
        )
        
        # Extract sources
        sources = []
        
        # Add semantic results
        for r in result.get('semantic_results', [])[:3]:
            meta = r.get('metadata', {})
            title = meta.get('title') or meta.get('name') or meta.get('keyword', 'Unknown')
            # Clean up title
            title = title.replace('(DataCatalog)_-[poweredBy]-_(KnowledgeGraph)', 'DataCatalog powered by Knowledge Graph')
            title = title.replace('_-[', ' ')
            title = title.replace(']-_', ' ')
            sources.append({
                'type': 'semantic',
                'node_type': r.get('node_type'),
                'title': title,
                'score': r.get('similarity_score', 0)
            })
        
        # Add transcript results
        for r in result.get('transcript_results', [])[:3]:
            title = r.get('title', 'Unknown')
            # Clean up title
            title = title.replace('(DataCatalog)_-[poweredBy]-_(KnowledgeGraph)', 'DataCatalog powered by Knowledge Graph')
            title = title.replace('_-[', ' ')
            title = title.replace(']-_', ' ')
            sources.append({
                'type': 'transcript',
                'title': title,
                'timestamp': r.get('timestamp'),
                'snippet': r.get('transcript_snippet', '')[:150]
            })
        
        # Add graph connections
        for r in result.get('graph_results', [])[:3]:
            source = r.get('source', {})
            neighbor = r.get('neighbor', {})
            source_name = source.get('name') or source.get('title') or source.get('keyword', 'Unknown')
            neighbor_name = neighbor.get('name') or neighbor.get('title') or neighbor.get('keyword', 'Unknown')
            sources.append({
                'type': 'graph',
                'relationship': r.get('relationship', 'RELATED_TO'),
                'source': source_name,
                'target': neighbor_name
            })
        
        # Clean up the answer text
        answer = result.get('answer', 'No answer generated')
        # Remove unwanted technical notation
        answer = answer.replace('(DataCatalog)_-[poweredBy]-_(KnowledgeGraph)', 'DataCatalog powered by Knowledge Graph')
        answer = answer.replace('_-[', ' ')
        answer = answer.replace(']-_', ' ')
        # Clean up multiple spaces
        answer = ' '.join(answer.split())
        
        return QueryResponse(
            query=result.get('query', request.query),
            answer=answer,
            query_type=result.get('query_type'),
            retrieval_stats={
                'semantic': len(result.get('semantic_results', [])),
                'graph': len(result.get('graph_results', [])),
                'transcript': len(result.get('transcript_results', [])),
                'multi_hop_paths': len(result.get('multi_hop_paths', []))
            },
            sources=sources
        )
    
    except Exception as e:
        return QueryResponse(
            query=request.query,
            answer="",
            error=str(e),
            retrieval_stats={}
        )


if __name__ == "__main__":
    uvicorn.run(
        "backend_api:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )

