"""
Test RAG system with transcript retrieval
"""

from rag_system import RAGSystem

print("=" * 70)
print("Testing RAG System - Transcript Content Retrieval")
print("=" * 70)
print()

# Initialize RAG system
print("🚀 Initializing RAG system...")
rag = RAGSystem()

# Test queries that should match transcript content
test_queries = [
    "What did Paco Nathan say about graph thinking?",
    "What is the Cynefin framework mentioned in the talks?",
    "What examples were given about knowledge graphs?",
]

for query in test_queries:
    print("\n" + "=" * 70)
    print(f"📝 Query: {query}")
    print("=" * 70)
    
    # Get full answer
    result = rag.query(query, top_k=5, verbose=True)
    
    print("\n" + "-" * 70)
    print("Answer:")
    print("-" * 70)
    print(result.get('answer', 'No answer generated'))
    print()
    
    # Show transcript results if any
    retrieval = result.get('retrieval_results', {})
    transcript_results = retrieval.get('transcript_results', [])
    
    if transcript_results:
        print("📹 Transcript Sources (with timestamps):")
        for i, tr in enumerate(transcript_results[:2], 1):
            print(f"\n  {i}. {tr.get('title', 'N/A')}")
            if tr.get('timestamp'):
                print(f"     ⏱️  {tr['timestamp']} ({tr.get('timestamp_seconds', 0):.0f}s)")
            print(f"     📝 {tr.get('transcript_snippet', '')[:150]}...")
    
    print("\n" + "=" * 70)

print("\n✅ Test Complete!")
rag.close()

