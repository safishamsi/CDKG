#!/usr/bin/env python3
"""
Complete pipeline runner - Run all steps end-to-end

Steps:
1. Load data into Neo4j
2. Generate embeddings
3. Build vector store
4. Test RAG system
"""

import time
import sys

from data_loader import DataLoader
from transcript_processor import process_transcripts
from embedding_generator import EmbeddingGenerator
from vector_store import VectorStore
from rag_system import RAGSystem


def run_step(step_name: str, step_func, *args, **kwargs):
    """Run a pipeline step with timing"""
    print("\n" + "=" * 70)
    print(f"🚀 STEP: {step_name}")
    print("=" * 70)
    
    start_time = time.time()
    
    try:
        result = step_func(*args, **kwargs)
        elapsed = time.time() - start_time
        
        print("\n" + "=" * 70)
        print(f"✅ {step_name} COMPLETE ({elapsed:.2f}s)")
        print("=" * 70)
        
        return result, True
        
    except Exception as e:
        elapsed = time.time() - start_time
        
        print("\n" + "=" * 70)
        print(f"❌ {step_name} FAILED ({elapsed:.2f}s)")
        print(f"Error: {e}")
        print("=" * 70)
        
        import traceback
        traceback.print_exc()
        
        return None, False


def step_1_load_data():
    """Step 1: Load CSV data into Neo4j"""
    loader = DataLoader()
    try:
        loader.load_all()
    finally:
        loader.close()


def step_1_5_process_transcripts():
    """Step 1.5: Process transcript files and load into Neo4j"""
    process_transcripts()


def step_2_generate_embeddings():
    """Step 2: Generate embeddings for all nodes (including transcript content)"""
    generator = EmbeddingGenerator()
    generator.generate_all()


def step_3_build_vector_store():
    """Step 3: Build FAISS index"""
    store = VectorStore()
    store.build_and_save(index_type="flat")


def step_4_test_rag():
    """Step 4: Test RAG system"""
    rag = RAGSystem()
    
    # Test with a sample query
    test_query = "What talks discuss knowledge graphs?"
    
    print("\n" + "=" * 70)
    print("🧪 Testing RAG System")
    print("=" * 70)
    
    result = rag.query(test_query, top_k=5, verbose=True)
    
    rag.close()
    
    return result


def main():
    """Run complete pipeline"""
    print("=" * 70)
    print("🚀 COMPLETE CDKG RAG PIPELINE")
    print("=" * 70)
    print("\nThis will run all steps:")
    print("  1. Load data into Neo4j")
    print("  1.5. Process transcripts and load into Neo4j")
    print("  2. Generate embeddings (including transcript content)")
    print("  3. Build vector store")
    print("  4. Test RAG system")
    print()
    
    # Ask for confirmation
    response = input("Continue? [y/N]: ")
    if response.lower() not in ['y', 'yes']:
        print("Cancelled.")
        sys.exit(0)
    
    pipeline_start = time.time()
    
    # Run steps
    steps = [
        ("Load Data into Neo4j", step_1_load_data),
        ("Process Transcripts", step_1_5_process_transcripts),
        ("Generate Embeddings", step_2_generate_embeddings),
        ("Build Vector Store", step_3_build_vector_store),
        ("Test RAG System", step_4_test_rag),
    ]
    
    results = []
    for step_name, step_func in steps:
        result, success = run_step(step_name, step_func)
        results.append((step_name, success))
        
        if not success:
            print(f"\n❌ Pipeline failed at: {step_name}")
            print("Please fix the error and try again.")
            sys.exit(1)
        
        # Brief pause between steps
        time.sleep(2)
    
    # Print final summary
    pipeline_elapsed = time.time() - pipeline_start
    
    print("\n" + "=" * 70)
    print("📊 PIPELINE SUMMARY")
    print("=" * 70)
    
    for step_name, success in results:
        status = "✅" if success else "❌"
        print(f"{status} {step_name}")
    
    print(f"\n⏱️  Total time: {pipeline_elapsed:.2f}s")
    print("=" * 70)
    
    if all(success for _, success in results):
        print("\n🎉 PIPELINE COMPLETE!")
        print("\n✨ Your RAG system is ready to use!")
        print("\nTry it out:")
        print("   python -c \"from rag_system import RAGSystem; rag = RAGSystem(); rag.query('What are knowledge graphs?')\"")
        print("\nOr in Python:")
        print("   from rag_system import RAGSystem")
        print("   rag = RAGSystem()")
        print("   result = rag.query('Your question here')")
        print()
    else:
        print("\n⚠️  Pipeline had errors. Please check the logs above.")
        sys.exit(1)


if __name__ == "__main__":
    main()
