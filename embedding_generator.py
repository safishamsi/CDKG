"""
Step 2: Embedding Generator - Generate embeddings for all nodes

This module handles:
- Extracting text from Neo4j nodes
- Generating embeddings using Sentence Transformers
- Storing embeddings and metadata
"""

import json
import numpy as np
from pathlib import Path
from typing import List, Dict, Tuple
from neo4j import GraphDatabase
from sentence_transformers import SentenceTransformer
from tqdm import tqdm

from config import config


class EmbeddingGenerator:
    """Generates embeddings for Neo4j nodes"""
    
    def __init__(self):
        """Initialize embedding model and Neo4j connection"""
        self.config = config
        self.driver = None
        self.model = None
        
        # Storage paths
        self.embeddings_dir = config.paths.embeddings_dir
        self.embeddings_dir.mkdir(parents=True, exist_ok=True)
    
    def connect_neo4j(self):
        """Connect to Neo4j"""
        print("\n🔌 Connecting to Neo4j...")
        self.driver = GraphDatabase.driver(
            self.config.neo4j.uri,
            auth=(self.config.neo4j.user, self.config.neo4j.password)
        )
        self.driver.verify_connectivity()
        print("   ✅ Connected\n")
    
    def load_embedding_model(self):
        """Load sentence transformer model"""
        print(f"🤖 Loading embedding model: {self.config.embedding.model_name}")
        self.model = SentenceTransformer(
            self.config.embedding.model_name,
            device=self.config.embedding.device
        )
        print(f"   ✅ Model loaded (dim: {self.model.get_sentence_embedding_dimension()})\n")
    
    def extract_speakers(self) -> Tuple[List[Dict], List[str]]:
        """Extract speakers and create text representations"""
        print("📊 Extracting Speakers...")
        
        with self.driver.session() as session:
            result = session.run("""
                MATCH (s:Speaker)
                OPTIONAL MATCH (s)-[:GIVES_TALK]->(t:Talk)
                RETURN s.name as name, 
                       collect(DISTINCT t.title) as talks,
                       count(t) as talk_count
                ORDER BY s.name
            """)
            
            speakers = []
            texts = []
            
            for record in result:
                name = record['name']
                talks = record['talks'][:5]  # Top 5 talks
                
                # Create rich text representation
                text = f"Speaker: {name}"
                if talks:
                    text += f". Talks: {', '.join(talks)}"
                
                speakers.append({
                    'name': name,
                    'talks': talks,
                    'talk_count': record['talk_count']
                })
                texts.append(text)
        
        print(f"   ✅ Extracted {len(speakers)} speakers\n")
        return speakers, texts
    
    def extract_talks(self) -> Tuple[List[Dict], List[str]]:
        """Extract talks and create text representations"""
        print("📊 Extracting Talks...")
        
        with self.driver.session() as session:
            result = session.run("""
                MATCH (t:Talk)
                OPTIONAL MATCH (s:Speaker)-[:GIVES_TALK]->(t)
                OPTIONAL MATCH (t)-[:IS_DESCRIBED_BY]->(tag:Tag)
                RETURN t.title as title,
                       t.description as description,
                       t.category as category,
                       COALESCE(t.transcript, '') as transcript,
                       s.name as speaker,
                       collect(DISTINCT tag.keyword)[0..10] as tags
                ORDER BY t.title
            """)
            
            talks = []
            texts = []
            
            for record in result:
                title = record['title']
                desc = record['description'] or ""
                category = record['category'] or ""
                transcript = record['transcript'] or ""
                speaker = record['speaker'] or ""
                tags = record['tags']
                
                # Create rich text representation
                text = f"Talk: {title}"
                if speaker:
                    text += f" by {speaker}"
                if category:
                    text += f". Category: {category}"
                if desc:
                    # Truncate description to 500 chars
                    text += f". {desc[:500]}"
                if tags:
                    text += f". Tags: {', '.join(tags)}"
                
                # Include transcript content (first 2000 chars for embedding)
                # Full transcript is still searchable via Neo4j transcript_search
                if transcript:
                    transcript_snippet = transcript[:2000] + ("..." if len(transcript) > 2000 else "")
                    text += f". Transcript: {transcript_snippet}"
                
                talks.append({
                    'title': title,
                    'description': desc,
                    'category': category,
                    'transcript': transcript,
                    'transcript_length': len(transcript),
                    'speaker': speaker,
                    'tags': tags
                })
                texts.append(text)
            
            # Count talks with transcripts
            talks_with_transcripts = sum(1 for t in talks if t.get('transcript'))
            if talks_with_transcripts > 0:
                print(f"   📝 {talks_with_transcripts} talks have transcript content included in embeddings")
        
        print(f"   ✅ Extracted {len(talks)} talks\n")
        return talks, texts
    
    def extract_tags(self) -> Tuple[List[Dict], List[str]]:
        """Extract tags and create text representations"""
        print("📊 Extracting Tags...")
        
        with self.driver.session() as session:
            result = session.run("""
                MATCH (tag:Tag)
                OPTIONAL MATCH (t:Talk)-[:IS_DESCRIBED_BY]->(tag)
                RETURN tag.keyword as keyword,
                       count(t) as usage_count
                ORDER BY tag.keyword
            """)
            
            tags = []
            texts = []
            
            for record in result:
                keyword = record['keyword']
                
                # Create text representation
                text = f"Tag: {keyword}"
                
                tags.append({
                    'keyword': keyword,
                    'usage_count': record['usage_count']
                })
                texts.append(text)
        
        print(f"   ✅ Extracted {len(tags)} tags\n")
        return tags, texts
    
    def extract_events(self) -> Tuple[List[Dict], List[str]]:
        """Extract events and create text representations"""
        print("📊 Extracting Events...")
        
        with self.driver.session() as session:
            result = session.run("""
                MATCH (e:Event)
                OPTIONAL MATCH (t:Talk)-[:IS_PART_OF]->(e)
                RETURN e.name as name,
                       e.description as description,
                       count(t) as talk_count
                ORDER BY e.name
            """)
            
            events = []
            texts = []
            
            for record in result:
                name = record['name']
                desc = record['description'] or ""
                
                # Create text representation
                text = f"Event: {name}"
                if desc:
                    text += f". {desc[:500]}"
                
                events.append({
                    'name': name,
                    'description': desc,
                    'talk_count': record['talk_count']
                })
                texts.append(text)
        
        print(f"   ✅ Extracted {len(events)} events\n")
        return events, texts
    
    def extract_categories(self) -> Tuple[List[Dict], List[str]]:
        """Extract categories and create text representations"""
        print("📊 Extracting Categories...")
        
        with self.driver.session() as session:
            result = session.run("""
                MATCH (c:Category)
                OPTIONAL MATCH (t:Talk)-[:IS_CATEGORIZED_AS]->(c)
                RETURN c.name as name,
                       count(t) as talk_count
                ORDER BY c.name
            """)
            
            categories = []
            texts = []
            
            for record in result:
                name = record['name']
                
                # Create text representation
                text = f"Category: {name}"
                
                categories.append({
                    'name': name,
                    'talk_count': record['talk_count']
                })
                texts.append(text)
        
        print(f"   ✅ Extracted {len(categories)} categories\n")
        return categories, texts
    
    def generate_embeddings(self, texts: List[str]) -> np.ndarray:
        """Generate embeddings for texts"""
        embeddings = self.model.encode(
            texts,
            batch_size=self.config.embedding.batch_size,
            show_progress_bar=True,
            convert_to_numpy=True,
            normalize_embeddings=True  # L2 normalization for cosine similarity
        )
        return embeddings
    
    def save_embeddings(self, node_type: str, metadata: List[Dict], embeddings: np.ndarray):
        """Save embeddings and metadata to disk"""
        # Save embeddings
        emb_path = self.embeddings_dir / f"{node_type.lower()}_embeddings.npy"
        np.save(emb_path, embeddings)
        
        # Save metadata
        meta_path = self.embeddings_dir / f"{node_type.lower()}_metadata.json"
        with open(meta_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        print(f"   💾 Saved {len(embeddings)} embeddings to {emb_path.name}")
    
    def generate_all(self):
        """Generate embeddings for all node types"""
        print("=" * 70)
        print("🚀 GENERATING EMBEDDINGS")
        print("=" * 70)
        
        # Connect and load model
        self.connect_neo4j()
        self.load_embedding_model()
        
        # Process each node type
        print("=" * 70)
        print("Extracting and Embedding Nodes")
        print("=" * 70 + "\n")
        
        all_embeddings = []
        index_mapping = []
        
        for node_type, extract_func in [
            ('Speaker', self.extract_speakers),
            ('Talk', self.extract_talks),
            ('Tag', self.extract_tags),
            ('Event', self.extract_events),
            ('Category', self.extract_categories)
        ]:
            # Extract
            metadata, texts = extract_func()
            
            if not texts:
                print(f"   ⚠️  No {node_type} nodes found, skipping...\n")
                continue
            
            # Generate embeddings
            print(f"🧠 Generating {node_type} embeddings...")
            embeddings = self.generate_embeddings(texts)
            
            # Save
            self.save_embeddings(node_type, metadata, embeddings)
            
            # Track for combined index
            start_idx = len(all_embeddings)
            all_embeddings.extend(embeddings)
            
            for i, meta in enumerate(metadata):
                index_mapping.append({
                    'index': start_idx + i,
                    'node_type': node_type,
                    'metadata': meta
                })
            
            print()
        
        # Save combined embeddings
        if all_embeddings:
            all_embeddings_array = np.vstack(all_embeddings)
            
            combined_path = self.embeddings_dir / "all_embeddings.npy"
            np.save(combined_path, all_embeddings_array)
            print(f"💾 Saved {len(all_embeddings_array)} combined embeddings\n")
            
            # Save index mapping
            mapping_path = self.embeddings_dir / "index_mapping.json"
            with open(mapping_path, 'w') as f:
                json.dump(index_mapping, f, indent=2)
            print(f"💾 Saved index mapping\n")
        
        # Print summary
        print("=" * 70)
        print("📈 Embedding Generation Summary:")
        print("=" * 70)
        print(f"   Total embeddings: {len(all_embeddings)}")
        print(f"   Embedding dimension: {self.model.get_sentence_embedding_dimension()}")
        print(f"   Saved to: {self.embeddings_dir}")
        print("=" * 70 + "\n")
        
        self.driver.close()


def main():
    """Main entry point"""
    generator = EmbeddingGenerator()
    generator.generate_all()


if __name__ == "__main__":
    main()
