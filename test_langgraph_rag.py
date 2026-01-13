"""
Test LangGraph Orchestrator with Hybrid RAG
"""

from rag_system import RAGSystem
from langgraph_orchestrator import LangGraphOrchestrator

print("=" * 70)
print("Testing LangGraph Orchestrator with Hybrid RAG")
print("=" * 70)
print()

# Initialize RAG system
print("🚀 Initializing RAG system...")
rag = RAGSystem()

# Initialize LangGraph orchestrator
print("🎯 Initializing LangGraph orchestrator...")
orchestrator = LangGraphOrchestrator(rag)

# Test queries
test_queries = [
    {
        "query": "What did Paco Nathan say about graph thinking?",
        "type": "hybrid",
        "description": "Should use semantic + transcript search"
    },
    {
        "query": "How is Paco Nathan related to knowledge graphs?",
        "type": "multi_hop",
        "description": "Should use multi-hop reasoning"
    },
    {
        "query": "What talks discuss semantic technology?",
        "type": "semantic",
        "description": "Should use semantic similarity"
    },
    {
        "query": "What talks did Juan Sequeda give?",
        "type": "graph",
        "description": "Should use graph traversal"
    }
]

for i, test in enumerate(test_queries, 1):
    print("\n" + "=" * 70)
    print(f"Test {i}: {test['description']}")
    print(f"Query: {test['query']}")
    print("=" * 70)
    
    # Query with orchestrator
    result = orchestrator.query(test['query'], max_hops=2, use_tools=False)
    
    print(f"\n📊 Query Type: {result.get('query_type', 'unknown')}")
    print(f"📝 Answer:\n{result.get('answer', 'No answer')}")
    
    # Show retrieval stats
    print(f"\n📈 Retrieval Stats:")
    print(f"   Semantic results: {len(result.get('semantic_results', []))}")
    print(f"   Graph results: {len(result.get('graph_results', []))}")
    print(f"   Transcript results: {len(result.get('transcript_results', []))}")
    print(f"   Multi-hop paths: {len(result.get('multi_hop_paths', []))}")
    
    if result.get('multi_hop_paths'):
        print(f"\n🔗 Multi-hop Paths Found:")
        for j, path in enumerate(result['multi_hop_paths'][:2], 1):
            print(f"   Path {j}: {path.get('nodes', [])}")

print("\n" + "=" * 70)
print("✅ Testing Complete!")
print("=" * 70)

# Cleanup
orchestrator.close()

