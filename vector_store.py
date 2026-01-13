"""
Step 3: Vector Store - Create and manage FAISS index for semantic search

This module handles:
- Loading embeddings from disk
- Creating FAISS index
- Performing similarity search
- Managing index persistence
"""

import json
import numpy as np
from pathlib import Path
from typing import List, Dict, Tuple, Optional
import faiss

from config import config


class VectorStore:
    """FAISS-based vector store for semantic search"""
    
    def __init__(self):
        """Initialize vector store"""
        self.config = config
        self.embeddings_dir = config.paths.embeddings_dir
        
        self.index: Optional[faiss.Index] = None
        self.embeddings: Optional[np.ndarray] = None
        self.index_mapping: Optional[List[Dict]] = None
        self.dimension: Optional[int] = None
    
    def load_embeddings(self):
        """Load embeddings and metadata from disk"""
        print("\n📂 Loading embeddings...")
        
        # Load combined embeddings
        emb_path = self.embeddings_dir / "all_embeddings.npy"
        if not emb_path.exists():
            raise FileNotFoundError(
                f"Embeddings not found at {emb_path}. "
                "Please run embedding_generator.py first."
            )
        
        self.embeddings = np.load(emb_path).astype('float32')
        self.dimension = self.embeddings.shape[1]
        
        print(f"   ✅ Loaded {len(self.embeddings)} embeddings (dim={self.dimension})")
        
        # Load index mapping
        mapping_path = self.embeddings_dir / "index_mapping.json"
        with open(mapping_path, 'r') as f:
            self.index_mapping = json.load(f)
        
        print(f"   ✅ Loaded index mapping\n")
    
    def create_index(self, index_type: str = "flat"):
        """
        Create FAISS index
        
        Args:
            index_type: Type of index
                - "flat": Exact search (best quality, slower)
                - "ivf": Inverted file index (faster, approximate)
                - "hnsw": Hierarchical NSW (fastest, approximate)
        """
        print(f"🔨 Creating FAISS index (type: {index_type})...")
        
        if self.embeddings is None:
            self.load_embeddings()
        
        # Create index based on type
        if index_type == "flat":
            # Exact search using L2 distance (for normalized vectors, equivalent to cosine)
            self.index = faiss.IndexFlatIP(self.dimension)  # IP = Inner Product
            
        elif index_type == "ivf":
            # Approximate search with IVF
            nlist = min(100, len(self.embeddings) // 10)  # Number of clusters
            quantizer = faiss.IndexFlatIP(self.dimension)
            self.index = faiss.IndexIVFFlat(quantizer, self.dimension, nlist)
            
            # Train index
            print("   Training IVF index...")
            self.index.train(self.embeddings)
            
        elif index_type == "hnsw":
            # HNSW index for fast approximate search
            M = 32  # Number of connections
            self.index = faiss.IndexHNSWFlat(self.dimension, M)
            
        else:
            raise ValueError(f"Unknown index type: {index_type}")
        
        # Add vectors to index
        print("   Adding vectors to index...")
        self.index.add(self.embeddings)
        
        print(f"   ✅ Index created with {self.index.ntotal} vectors\n")
    
    def save_index(self):
        """Save FAISS index to disk"""
        if self.index is None:
            raise ValueError("No index to save. Create index first.")
        
        index_path = self.embeddings_dir / "faiss_index.bin"
        faiss.write_index(self.index, str(index_path))
        
        # Save index info
        info = {
            'total_vectors': self.index.ntotal,
            'dimension': self.dimension,
            'index_type': type(self.index).__name__
        }
        
        info_path = self.embeddings_dir / "faiss_index_info.json"
        with open(info_path, 'w') as f:
            json.dump(info, f, indent=2)
        
        print(f"💾 Saved index to {index_path}\n")
    
    def load_index(self):
        """Load FAISS index from disk"""
        print("📂 Loading FAISS index...")
        
        index_path = self.embeddings_dir / "faiss_index.bin"
        if not index_path.exists():
            raise FileNotFoundError(
                f"Index not found at {index_path}. "
                "Please create index first."
            )
        
        self.index = faiss.read_index(str(index_path))
        
        # Load index mapping if not already loaded
        if self.index_mapping is None:
            mapping_path = self.embeddings_dir / "index_mapping.json"
            with open(mapping_path, 'r') as f:
                self.index_mapping = json.load(f)
        
        print(f"   ✅ Loaded index with {self.index.ntotal} vectors\n")
    
    def search(self, query_vector: np.ndarray, k: int = 10) -> List[Dict]:
        """
        Search for similar vectors
        
        Args:
            query_vector: Query embedding (1D array)
            k: Number of results to return
            
        Returns:
            List of search results with metadata
        """
        if self.index is None:
            self.load_index()
        
        # Ensure query is 2D
        if query_vector.ndim == 1:
            query_vector = query_vector.reshape(1, -1)
        
        # Ensure float32
        query_vector = query_vector.astype('float32')
        
        # Normalize for cosine similarity
        faiss.normalize_L2(query_vector)
        
        # Search
        distances, indices = self.index.search(query_vector, k)
        
        # Format results
        results = []
        for dist, idx in zip(distances[0], indices[0]):
            if idx < len(self.index_mapping):
                result = self.index_mapping[idx].copy()
                result['similarity_score'] = float(dist)  # Cosine similarity
                results.append(result)
        
        return results
    
    def build_and_save(self, index_type: str = "flat"):
        """Build index from embeddings and save"""
        print("=" * 70)
        print("🚀 BUILDING VECTOR STORE")
        print("=" * 70)
        
        self.load_embeddings()
        self.create_index(index_type)
        self.save_index()
        
        print("=" * 70)
        print("✅ VECTOR STORE READY")
        print("=" * 70 + "\n")


def main():
    """Main entry point - build FAISS index"""
    store = VectorStore()
    store.build_and_save(index_type="flat")  # Use "flat" for exact search
    
    # Test search
    print("🧪 Testing search...")
    test_query = np.random.randn(store.dimension).astype('float32')
    results = store.search(test_query, k=3)
    
    print(f"   Found {len(results)} results")
    for i, result in enumerate(results, 1):
        print(f"   {i}. [{result['node_type']}] Score: {result['similarity_score']:.4f}")
    print()


if __name__ == "__main__":
    main()
