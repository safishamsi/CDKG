"""
Test transcript retrieval in RAG system
"""

from rag_system import RAGSystem

print("=" * 70)
print("Testing Transcript Retrieval in RAG System")
print("=" * 70)
print()

# Initialize RAG system
print("Initializing RAG system...")
rag = RAGSystem()

# Test query that should match transcript content
test_queries = [
    "What did Paco Nathan say about graph thinking?",
    "What is the Cynefin framework?",
    "What examples were given about knowledge graphs?",
]

for query in test_queries:
    print("\n" + "=" * 70)
    print(f"Query: {query}")
    print("=" * 70)
    
    # Get retrieval results
    retrieval = rag.hybrid_retrieve(query, top_k=3)
    
    # Check transcript results
    transcript_results = retrieval.get('transcript_results', [])
    
    if transcript_results:
        print(f"\n✅ Found {len(transcript_results)} transcript matches:")
        for i, result in enumerate(transcript_results[:2], 1):
            print(f"\n{i}. Talk: {result.get('title', 'N/A')}")
            if result.get('timestamp'):
                print(f"   ⏱️  Timestamp: {result['timestamp']} ({result.get('timestamp_seconds', 0):.0f}s)")
            print(f"   📝 Excerpt: {result.get('transcript_snippet', '')[:200]}...")
    else:
        print("\n⚠️  No transcript matches found")
    
    # Check if transcript content is in semantic results
    semantic_results = retrieval.get('semantic_results', [])
    transcript_in_semantic = False
    for result in semantic_results:
        metadata = result.get('metadata', {})
        if metadata.get('transcript') or metadata.get('transcript_length'):
            transcript_in_semantic = True
            break
    
    if transcript_in_semantic:
        print("\n✅ Transcript content also found in semantic search results")
    
    print("\n" + "-" * 70)

print("\n" + "=" * 70)
print("✅ Transcript Retrieval Test Complete")
print("=" * 70)

rag.close()

