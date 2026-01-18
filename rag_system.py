"""
Step 4: RAG System - Complete hybrid retrieval and generation

This module handles:
- Query understanding
- Hybrid retrieval (Graph + Semantic)
- Context generation
- LLM-based answer generation
"""

import json
import numpy as np
from typing import List, Dict, Optional
from sentence_transformers import SentenceTransformer
from neo4j import GraphDatabase
from anthropic import Anthropic

from config import config
from vector_store import VectorStore


class RAGSystem:
    """Complete RAG system with hybrid retrieval"""
    
    def __init__(self):
        """Initialize RAG system"""
        self.config = config
        
        # Initialize components
        self.embedding_model = None
        self.vector_store = None
        self.neo4j_driver = None
        self.llm_client = None
        
        self._initialize()
    
    def _initialize(self):
        """Initialize all components"""
        print("\n🚀 Initializing RAG System...")
        
        # 1. Load embedding model
        print("   Loading embedding model...")
        self.embedding_model = SentenceTransformer(
            self.config.embedding.model_name,
            device=self.config.embedding.device
        )
        
        # 2. Load vector store
        print("   Loading vector store...")
        self.vector_store = VectorStore()
        self.vector_store.load_index()
        
        # 3. Connect to Neo4j
        print("   Connecting to Neo4j...")
        self.neo4j_driver = GraphDatabase.driver(
            self.config.neo4j.uri,
            auth=(self.config.neo4j.user, self.config.neo4j.password)
        )
        self.neo4j_driver.verify_connectivity()
        
        # 4. Initialize Anthropic client
        print("   Initializing LLM client...")
        self.llm_client = Anthropic(api_key=self.config.llm.api_key)
        
        print("   ✅ RAG System ready!\n")
    
    def embed_query(self, query: str) -> np.ndarray:
        """Generate embedding for query"""
        embedding = self.embedding_model.encode(
            query,
            convert_to_numpy=True,
            normalize_embeddings=True
        )
        return embedding
    
    def semantic_search(self, query: str, k: int = 10) -> List[Dict]:
        """
        Perform semantic search using FAISS
        
        Args:
            query: User query
            k: Number of results
            
        Returns:
            List of search results with metadata
        """
        # Get query embedding
        query_embedding = self.embed_query(query)
        
        # Search in vector store
        results = self.vector_store.search(query_embedding, k=k)
        
        return results
    
    def get_community_members(self, node_id: str) -> List[Dict]:
        """
        Get all members of the same community as a given node
        
        Args:
            node_id: Node identifier (name, title, or keyword)
            
        Returns:
            List of community member information
        """
        with self.neo4j_driver.session() as session:
            query = """
            MATCH (n)-[:BELONGS_TO]->(c:Community)
            WHERE (n.name = $node_id OR n.title = $node_id OR n.keyword = $node_id)
            MATCH (member)-[:BELONGS_TO]->(c)
            WHERE member <> n
            RETURN DISTINCT
                labels(member)[0] as type,
                member.name as name,
                member.title as title,
                member.keyword as keyword,
                c.id as community_id
            LIMIT 20
            """
            result = session.run(query, node_id=node_id)
            
            members = []
            for record in result:
                name = record['name'] or record['title'] or record['keyword'] or 'Unknown'
                members.append({
                    'type': record['type'],
                    'name': name,
                    'community_id': record['community_id']
                })
            
            return members
    
    def graph_traversal(self, entity_names: List[str], max_depth: int = 2) -> List[Dict]:
        """
        Perform graph traversal from entities with improved matching
        
        Args:
            entity_names: List of entity names (talks, speakers, tags)
            max_depth: Maximum traversal depth
            
        Returns:
            List of connected nodes
        """
        if not entity_names:
            return []
        
        # Build query to find neighbors with case-insensitive matching
        query = """
        UNWIND $names as name
        MATCH (n)
        WHERE toLower(COALESCE(n.name, '')) = toLower(name)
           OR toLower(COALESCE(n.title, '')) = toLower(name)
           OR toLower(COALESCE(n.keyword, '')) = toLower(name)
           OR toLower(COALESCE(n.name, '')) CONTAINS toLower(name)
           OR toLower(COALESCE(n.title, '')) CONTAINS toLower(name)
        WITH n, name
        MATCH path = (n)-[*1..%d]-(neighbor)
        WHERE neighbor IS NOT NULL
        WITH n, neighbor, relationships(path) as rels, length(path) as path_len
        RETURN DISTINCT
            labels(n)[0] as source_type,
            n.name as source_name,
            n.title as source_title,
            n.keyword as source_keyword,
            type(rels[0]) as rel_type,
            labels(neighbor)[0] as neighbor_type,
            neighbor.name as neighbor_name,
            neighbor.title as neighbor_title,
            neighbor.keyword as neighbor_keyword,
            path_len
        ORDER BY path_len
        LIMIT 50
        """ % max_depth
        
        with self.neo4j_driver.session() as session:
            result = session.run(query, names=entity_names)
            
            connections = []
            for record in result:
                if record['neighbor_type']:
                    # Build source info
                    source_name = record['source_name'] or record['source_title'] or record['source_keyword'] or 'Unknown'
                    neighbor_name = record['neighbor_name'] or record['neighbor_title'] or record['neighbor_keyword'] or 'Unknown'
                    
                    connections.append({
                        'source_type': record['source_type'],
                        'source': {
                            'name': record['source_name'],
                            'title': record['source_title'],
                            'keyword': record['source_keyword']
                        },
                        'relationship': record['rel_type'],
                        'neighbor_type': record['neighbor_type'],
                        'neighbor': {
                            'name': record['neighbor_name'],
                            'title': record['neighbor_title'],
                            'keyword': record['neighbor_keyword']
                        },
                        'path_length': record['path_len']
                    })
        
        return connections
    
    def transcript_search(self, query: str, limit: int = 5) -> List[Dict]:
        """
        Search transcript content directly in Neo4j with timestamp support
        
        Args:
            query: Search query
            limit: Maximum results
            
        Returns:
            List of talks with matching transcript content and timestamps
        """
        import json
        
        # Extract keywords from query (words longer than 2 chars, excluding common words)
        import string
        common_words = {'what', 'did', 'say', 'about', 'the', 'and', 'are', 'was', 'were', 'for', 'with', 'that', 'this', 'from'}
        words = query.split()
        # Strip punctuation and filter
        keywords = [word.lower().strip(string.punctuation) for word in words 
                   if len(word.strip(string.punctuation)) > 2 and word.lower().strip(string.punctuation) not in common_words]
        
        # Extract speaker names - look for consecutive capitalized words (likely names)
        speaker_candidates = []
        i = 0
        while i < len(words):
            if words[i][0].isupper() and len(words[i]) > 2 and words[i].lower() not in common_words:
                # Check if next word is also capitalized (multi-word name)
                if i + 1 < len(words) and words[i + 1][0].isupper() and len(words[i + 1]) > 2:
                    # Multi-word name like "Paco Nathan"
                    full_name = f"{words[i]} {words[i + 1]}"
                    speaker_candidates.append(full_name)
                    # Remove speaker name parts from keywords to avoid false matches
                    if words[i].lower() in keywords:
                        keywords.remove(words[i].lower())
                    if words[i + 1].lower() in keywords:
                        keywords.remove(words[i + 1].lower())
                    i += 2
                    continue
                else:
                    # Single word name
                    speaker_candidates.append(words[i])
                    if words[i].lower() in keywords:
                        keywords.remove(words[i].lower())
            i += 1
        
        with self.neo4j_driver.session() as session:
            # Build a more comprehensive search query
            if keywords:
                # Search in transcript content
                transcript_conditions = " OR ".join([f"toLower(t.transcript) CONTAINS '{kw}'" for kw in keywords])
                
                # Also search for talk titles matching keywords
                title_conditions = " OR ".join([f"toLower(t.title) CONTAINS '{kw}'" for kw in keywords])
                
                # If we have speaker candidates, require BOTH speaker AND keyword match
                if speaker_candidates:
                    # Build speaker match conditions - try exact match first, then contains
                    speaker_conditions = []
                    for name in speaker_candidates:
                        speaker_conditions.append(f"toLower(s.name) = toLower('{name}')")
                        speaker_conditions.append(f"toLower(s.name) CONTAINS toLower('{name}')")
                    speaker_names_condition = " OR ".join(speaker_conditions)
                    
                    # Require talks by the speaker AND matching keywords
                    where_clause = f"t.transcript IS NOT NULL AND EXISTS {{ MATCH (s:Speaker)-[:GIVES_TALK]->(t) WHERE {speaker_names_condition} }} AND ({transcript_conditions} OR {title_conditions})"
                else:
                    where_clause = f"""
                        t.transcript IS NOT NULL 
                        AND ({transcript_conditions} OR {title_conditions})
                    """
            else:
                # If no keywords, just filter by speaker if provided
                speaker_filter = ""
                if speaker_candidates:
                    speaker_names_condition = " OR ".join([f"toLower(s.name) CONTAINS toLower('{name}')" for name in speaker_candidates])
                    speaker_filter = f"""
                    AND EXISTS {{
                        MATCH (s:Speaker)-[:GIVES_TALK]->(t)
                        WHERE {speaker_names_condition}
                    }}
                    """
                where_clause = f"t.transcript IS NOT NULL {speaker_filter}"
            
            # Debug: print query for troubleshooting
            # Debug: Check if we're building the query correctly
            # For "What did Paco Nathan say about graph thinking?"
            # We should have: speaker_candidates = ['Paco Nathan'], keywords = ['graph', 'thinking']
            
            # Move WHERE clause filtering before OPTIONAL MATCH to ensure correct filtering
            cypher_query = f"""
                MATCH (t:Talk)
                WHERE {where_clause}
                OPTIONAL MATCH (s:Speaker)-[:GIVES_TALK]->(t)
                OPTIONAL MATCH (t)-[:IS_DESCRIBED_BY]->(tag:Tag)
                RETURN t.title as title,
                       t.description as description,
                       t.transcript as transcript,
                       t.transcript_segments as segments_json,
                       t.youtube_id as youtube_id,
                       t.url as url,
                       collect(DISTINCT s.name)[0..3] as speakers,
                       collect(DISTINCT tag.keyword)[0..5] as tags,
                       size(t.transcript) as transcript_length,
                       CASE 
                         WHEN toLower(t.title) = toLower($search_query) THEN 1
                         WHEN toLower(t.title) CONTAINS toLower($search_query) THEN 2
                         WHEN toLower(t.transcript) CONTAINS toLower($search_query) THEN 3
                         ELSE 4
                       END as match_priority
                ORDER BY match_priority ASC, transcript_length DESC
                LIMIT $limit
            """
            result = session.run(cypher_query, search_query=query, limit=limit)
            
            results = []
            for record in result:
                transcript = record['transcript'] or ''
                segments_json = record['segments_json']
                segments = json.loads(segments_json) if segments_json else []
                
                # Use keywords instead of full query for better matching
                import string
                common_words = {'what', 'did', 'say', 'about', 'the', 'and', 'are', 'was', 'were', 'for', 'with', 'that', 'this', 'from'}
                words = query.split()
                search_keywords = [word.lower().strip(string.punctuation) for word in words 
                                 if len(word.strip(string.punctuation)) > 2 and word.lower().strip(string.punctuation) not in common_words]
                
                query_lower = query.lower()
                transcript_lower = transcript.lower()
                
                # Find position of query in transcript, or search for keywords
                pos = transcript_lower.find(query_lower)
                if pos < 0 and search_keywords:
                    # Try finding any keyword
                    for kw in search_keywords:
                        pos = transcript_lower.find(kw)
                        if pos >= 0:
                            break
                
                # Find matching segment with timestamp
                matching_segment = None
                if segments and pos >= 0:
                    # Find which segment contains this position
                    char_pos = 0
                    for segment in segments:
                        segment_text = segment.get('text', '')
                        segment_start = char_pos
                        segment_end = char_pos + len(segment_text)
                        
                        if segment_start <= pos < segment_end:
                            matching_segment = segment
                            break
                        
                        char_pos = segment_end + 1  # +1 for space between segments
                
                # Extract multiple relevant snippets from transcript
                # For follow-up questions or queries about specific aspects, we want multiple snippets
                snippets = []
                
                # Find all positions where keywords appear
                keyword_positions = []
                for kw in search_keywords:
                    start_pos = 0
                    while True:
                        pos_found = transcript_lower.find(kw, start_pos)
                        if pos_found < 0:
                            break
                        keyword_positions.append(pos_found)
                        start_pos = pos_found + 1
                
                # Also search for related terms if query is about "tools", "discusses", "mentions", etc.
                related_terms = []
                query_lower_for_terms = query.lower()
                if any(term in query_lower_for_terms for term in ['tool', 'discuss', 'mention', 'talk about', 'say about', 'cover']):
                    # Add technical terms that might be mentioned
                    technical_terms = ['apache', 'arrow', 'parquet', 'cairo', 'cynefin', 'graphistry', 'framework', 'library', 'tool', 'technology', 'system']
                    for term in technical_terms:
                        start_pos = 0
                        while True:
                            pos_found = transcript_lower.find(term, start_pos)
                            if pos_found < 0:
                                break
                            keyword_positions.append(pos_found)
                            start_pos = pos_found + 1
                
                # If we found keyword positions, extract snippets around each
                if keyword_positions:
                    # Sort and deduplicate positions
                    keyword_positions = sorted(set(keyword_positions))
                    
                    # Extract snippets around each position (up to 5 different positions)
                    for pos in keyword_positions[:5]:
                        # Extract more context around match (800 chars before and after for comprehensive quotes)
                        start = max(0, pos - 800)
                        end = min(len(transcript), pos + 800)
                        
                        # Try to start at sentence boundary
                        if start > 0:
                            sentence_start = transcript.rfind('.', max(0, start - 150), start)
                            sentence_start = max(sentence_start, transcript.rfind('!', max(0, start - 150), start))
                            sentence_start = max(sentence_start, transcript.rfind('?', max(0, start - 150), start))
                            if sentence_start > 0:
                                start = sentence_start + 1
                        
                        # Try to end at sentence boundary
                        if end < len(transcript):
                            sentence_end = transcript.find('.', end, min(len(transcript), end + 150))
                            sentence_end = min(sentence_end, transcript.find('!', end, min(len(transcript), end + 150))) if sentence_end > 0 else sentence_end
                            sentence_end = min(sentence_end, transcript.find('?', end, min(len(transcript), end + 150))) if sentence_end > 0 else sentence_end
                            if sentence_end > 0:
                                end = sentence_end + 1
                        
                        snippet = transcript[start:end].strip()
                        if start > 0:
                            snippet = "..." + snippet
                        if end < len(transcript):
                            snippet = snippet + "..."
                        
                        # Only add if not too similar to existing snippets
                        if not snippets or not any(self._snippets_overlap(snippet, existing) for existing in snippets):
                            snippets.append(snippet)
                
                # If we have snippets, use them; otherwise fall back to original logic
                if snippets:
                    # Combine snippets, but limit total length
                    combined_snippet = " | ".join(snippets[:3])  # Max 3 snippets
                    if len(combined_snippet) > 2000:
                        # Truncate but try to keep complete sentences
                        combined_snippet = combined_snippet[:2000]
                        last_period = combined_snippet.rfind('.')
                        if last_period > 1500:
                            combined_snippet = combined_snippet[:last_period + 1] + "..."
                    snippet = combined_snippet
                elif pos >= 0:
                    # Original single-snippet logic
                    start = max(0, pos - 800)  # Increased from 500 to 800
                    end = min(len(transcript), pos + len(query) + 800)
                    
                    # Try to start at sentence boundary
                    if start > 0:
                        sentence_start = transcript.rfind('.', max(0, start - 150), start)
                        sentence_start = max(sentence_start, transcript.rfind('!', max(0, start - 150), start))
                        sentence_start = max(sentence_start, transcript.rfind('?', max(0, start - 150), start))
                        if sentence_start > 0:
                            start = sentence_start + 1
                    
                    # Try to end at sentence boundary
                    if end < len(transcript):
                        sentence_end = transcript.find('.', end, min(len(transcript), end + 150))
                        sentence_end = min(sentence_end, transcript.find('!', end, min(len(transcript), end + 150))) if sentence_end > 0 else sentence_end
                        sentence_end = min(sentence_end, transcript.find('?', end, min(len(transcript), end + 150))) if sentence_end > 0 else sentence_end
                        if sentence_end > 0:
                            end = sentence_end + 1
                    
                    snippet = transcript[start:end].strip()
                    if start > 0:
                        snippet = "..." + snippet
                    if end < len(transcript):
                        snippet = snippet + "..."
                else:
                    # If exact match not found, search for keywords and use relevant section
                    keywords = [w.lower() for w in query.split() if len(w) > 3]
                    best_pos = -1
                    for kw in keywords:
                        kw_pos = transcript_lower.find(kw)
                        if kw_pos >= 0 and (best_pos < 0 or kw_pos < best_pos):
                            best_pos = kw_pos
                    
                    if best_pos >= 0:
                        start = max(0, best_pos - 500)
                        end = min(len(transcript), best_pos + 500)
                        
                        # Try to start at sentence boundary
                        if start > 0:
                            sentence_start = transcript.rfind('.', max(0, start - 100), start)
                            sentence_start = max(sentence_start, transcript.rfind('!', max(0, start - 100), start))
                            sentence_start = max(sentence_start, transcript.rfind('?', max(0, start - 100), start))
                            if sentence_start > 0:
                                start = sentence_start + 1
                        
                        # Try to end at sentence boundary
                        if end < len(transcript):
                            sentence_end = transcript.find('.', end, min(len(transcript), end + 100))
                            sentence_end = min(sentence_end, transcript.find('!', end, min(len(transcript), end + 100))) if sentence_end > 0 else sentence_end
                            sentence_end = min(sentence_end, transcript.find('?', end, min(len(transcript), end + 100))) if sentence_end > 0 else sentence_end
                            if sentence_end > 0:
                                end = sentence_end + 1
                        
                        snippet = transcript[start:end].strip()
                        if start > 0:
                            snippet = "..." + snippet
                        if end < len(transcript):
                            snippet = snippet + "..."
                    else:
                        # Fallback: use first 1000 chars with sentence boundary
                        fallback_end = min(1000, len(transcript))
                        sentence_end = transcript.find('.', fallback_end - 200, fallback_end + 100)
                        if sentence_end > 0:
                            fallback_end = sentence_end + 1
                        snippet = transcript[:fallback_end] + ("..." if len(transcript) > fallback_end else "")
                
                result_dict = {
                    'node_type': 'Talk',
                    'title': record['title'],
                    'description': record['description'],
                    'transcript_snippet': snippet,
                    'speakers': record['speakers'],
                    'tags': record['tags'],
                    'transcript_length': record['transcript_length'],
                    'source': 'transcript_search'
                }
                
                # Add YouTube URL if available
                youtube_id = record.get('youtube_id')
                url = record.get('url')
                if youtube_id:
                    result_dict['youtube_id'] = youtube_id
                    result_dict['video_url'] = f"https://www.youtube.com/watch?v={youtube_id}"
                elif url and 'youtube.com' in url.lower():
                    result_dict['video_url'] = url
                
                # Add timestamp information if available
                if matching_segment:
                    result_dict['timestamp'] = matching_segment.get('start')
                    result_dict['timestamp_seconds'] = matching_segment.get('start_seconds')
                    result_dict['timestamp_end'] = matching_segment.get('end')
                    
                    # Generate proper video link with timestamp
                    if youtube_id:
                        timestamp_sec = int(matching_segment.get('start_seconds', 0))
                        result_dict['video_link'] = f"https://www.youtube.com/watch?v={youtube_id}&t={timestamp_sec}s"
                    elif url and 'youtube.com' in url.lower():
                        timestamp_sec = int(matching_segment.get('start_seconds', 0))
                        # Extract video ID from URL if needed
                        import re
                        video_id_match = re.search(r'(?:v=|/)([0-9A-Za-z_-]{11}).*', url)
                        if video_id_match:
                            vid_id = video_id_match.group(1)
                            result_dict['video_link'] = f"https://www.youtube.com/watch?v={vid_id}&t={timestamp_sec}s"
                        else:
                            result_dict['video_link'] = f"{url}&t={timestamp_sec}s"
                    else:
                        result_dict['video_link'] = f"#t={int(matching_segment.get('start_seconds', 0))}"
                
                results.append(result_dict)
        
        return results
    
    def _snippets_overlap(self, snippet1: str, snippet2: str, threshold: float = 0.5) -> bool:
        """Check if two snippets overlap significantly"""
        words1 = set(snippet1.lower().split())
        words2 = set(snippet2.lower().split())
        if not words1 or not words2:
            return False
        overlap = len(words1 & words2) / max(len(words1), len(words2))
        return overlap > threshold
    
    def cypher_search(self, query: str) -> List[Dict]:
        """
        Perform keyword-based Cypher search
        
        Args:
            query: User query
            
        Returns:
            List of matching talks and speakers
        """
        # Extract keywords (simple tokenization)
        keywords = [word.lower() for word in query.split() if len(word) > 3]
        
        if not keywords:
            return []
        
        # Search in talks and speakers
        cypher_query = """
        UNWIND $keywords as keyword
        MATCH (t:Talk)
        WHERE toLower(t.title) CONTAINS keyword 
           OR toLower(t.description) CONTAINS keyword
           OR toLower(t.category) CONTAINS keyword
        OPTIONAL MATCH (s:Speaker)-[:GIVES_TALK]->(t)
        OPTIONAL MATCH (t)-[:IS_DESCRIBED_BY]->(tag:Tag)
        RETURN DISTINCT
            t.title as title,
            t.description as description,
            t.category as category,
            s.name as speaker,
            collect(DISTINCT tag.keyword)[0..5] as tags
        LIMIT 10
        """
        
        with self.neo4j_driver.session() as session:
            result = session.run(cypher_query, keywords=keywords)
            
            results = []
            for record in result:
                results.append({
                    'type': 'Talk',
                    'title': record['title'],
                    'description': record['description'],
                    'category': record['category'],
                    'speaker': record['speaker'],
                    'tags': record['tags']
                })
        
        return results
    
    def hybrid_retrieve(self, query: str, top_k: int = 5) -> Dict[str, any]:
        """
        Hybrid retrieval combining semantic search and graph traversal
        
        Args:
            query: User query
            top_k: Number of top results to retrieve
            
        Returns:
            Dictionary with all retrieved context
        """
        print(f"\n🔍 Retrieving context for: '{query}'")
        
        # 1. Semantic search
        print("   Running semantic search...")
        semantic_results = self.semantic_search(query, k=top_k)
        
        # 2. Cypher keyword search
        print("   Running keyword search...")
        keyword_results = self.cypher_search(query)
        
        # 2.5. Transcript content search (increase limit for better coverage)
        print("   Searching transcript content...")
        transcript_results = self.transcript_search(query, limit=top_k * 2)  # Get more transcript results
        
        # 3. Graph traversal from top semantic results
        print("   Performing graph traversal...")
        entity_names = []
        for result in semantic_results[:3]:  # Top 3 for traversal
            metadata = result['metadata']
            if 'name' in metadata:
                entity_names.append(metadata['name'])
            elif 'title' in metadata:
                entity_names.append(metadata['title'])
            elif 'keyword' in metadata:
                entity_names.append(metadata['keyword'])
        
        graph_connections = self.graph_traversal(entity_names)
        
        print(f"   ✅ Retrieved {len(semantic_results)} semantic + {len(keyword_results)} keyword + {len(transcript_results)} transcript + {len(graph_connections)} graph results\n")
        
        return {
            'semantic_results': semantic_results,
            'keyword_results': keyword_results,
            'transcript_results': transcript_results,
            'graph_connections': graph_connections,
            'query': query
        }
    
    def format_context(self, retrieval_results: Dict) -> str:
        """Format retrieval results into context string for LLM"""
        """
        Format retrieval results into context for LLM
        
        Args:
            retrieval_results: Results from hybrid_retrieve
            
        Returns:
            Formatted context string
        """
        context_parts = []
        
        # Add semantic results
        if retrieval_results['semantic_results']:
            context_parts.append("=== Relevant Content (Semantic Search) ===\n")
            for i, result in enumerate(retrieval_results['semantic_results'][:5], 1):
                meta = result['metadata']
                score = result['similarity_score']
                
                if result['node_type'] == 'Talk':
                    # Clean up talk title
                    title = meta.get('title', 'N/A')
                    title = title.replace('(DataCatalog)_-[poweredBy]-_(KnowledgeGraph)', 'DataCatalog powered by Knowledge Graph')
                    title = title.replace('_-[', ' ')
                    title = title.replace(']-_', ' ')
                    
                    context_parts.append(
                        f"{i}. Talk: {title}\n"
                        f"   Speaker: {meta.get('speaker', 'Unknown')}\n"
                        f"   Category: {meta.get('category', 'N/A')}\n"
                        f"   Description: {meta.get('description', 'N/A')[:200]}...\n"
                        f"   Relevance: {score:.3f}\n"
                    )
                elif result['node_type'] == 'Speaker':
                    context_parts.append(
                        f"{i}. Speaker: {meta.get('name', 'N/A')}\n"
                        f"   Talks: {', '.join(meta.get('talks', [])[:3])}\n"
                        f"   Relevance: {score:.3f}\n"
                    )
                elif result['node_type'] == 'Tag':
                    context_parts.append(
                        f"{i}. Tag: {meta.get('keyword', 'N/A')}\n"
                        f"   Relevance: {score:.3f}\n"
                    )
        
        # Add keyword results
        if retrieval_results['keyword_results']:
            context_parts.append("\n=== Keyword Matches ===\n")
            for i, result in enumerate(retrieval_results['keyword_results'][:3], 1):
                context_parts.append(
                    f"{i}. {result.get('title', 'N/A')}\n"
                    f"   By: {result.get('speaker', 'Unknown')}\n"
                    f"   Tags: {', '.join(result.get('tags', []))}\n"
                )
        
        # Add transcript results (full content search with timestamps)
        if retrieval_results.get('transcript_results'):
            context_parts.append("\n=== Transcript Content (Direct Quotes Available) ===\n")
            # Show more transcript results (up to 8) to get more complete context
            for i, result in enumerate(retrieval_results['transcript_results'][:8], 1):
                # Clean up title
                title = result.get('title', 'N/A')
                title = title.replace('(DataCatalog)_-[poweredBy]-_(KnowledgeGraph)', 'DataCatalog powered by Knowledge Graph')
                title = title.replace('_-[', ' ')
                title = title.replace(']-_', ' ')
                
                timestamp_info = ""
                if result.get('timestamp'):
                    timestamp_str = result.get('timestamp')
                    timestamp_seconds = result.get('timestamp_seconds', 0)
                    
                    # Format timestamp in multiple ways for clarity
                    if timestamp_seconds:
                        minutes = int(timestamp_seconds // 60)
                        seconds = int(timestamp_seconds % 60)
                        formatted_time = f"{minutes}:{seconds:02d}"
                        if minutes >= 60:
                            hours = minutes // 60
                            mins = minutes % 60
                            formatted_time = f"{hours}:{mins:02d}:{seconds:02d}"
                        
                        timestamp_info = f"   Timestamp: {timestamp_str} (or {formatted_time} or {int(timestamp_seconds)}s)\n"
                    else:
                        timestamp_info = f"   Timestamp: {timestamp_str}\n"
                
                # Add video link if available
                video_link_info = ""
                if result.get('video_link'):
                    video_link_info = f"   Video Link: {result.get('video_link')}\n"
                elif result.get('video_url'):
                    video_link_info = f"   Video URL: {result.get('video_url')}\n"
                
                transcript_snippet = result.get('transcript_snippet', '')
                # Include more context from transcript (1200 chars for better, more complete quotes)
                # Try to preserve sentence boundaries
                if transcript_snippet and len(transcript_snippet) > 1200:
                    # Find last sentence boundary before 1200 chars
                    truncate_pos = 1200
                    sentence_end = transcript_snippet.rfind('.', 1000, truncate_pos)
                    sentence_end = max(sentence_end, transcript_snippet.rfind('!', 1000, truncate_pos))
                    sentence_end = max(sentence_end, transcript_snippet.rfind('?', 1000, truncate_pos))
                    if sentence_end > 1000:
                        transcript_snippet = transcript_snippet[:sentence_end + 1] + "..."
                    else:
                        transcript_snippet = transcript_snippet[:1200] + "..."
                
                context_parts.append(
                    f"{i}. Talk: {title}\n"
                    f"   Speakers: {', '.join(result.get('speakers', []))}\n"
                    f"{timestamp_info}"
                    f"{video_link_info}"
                    f"   Transcript excerpt: {transcript_snippet}\n"
                    f"   Tags: {', '.join(result.get('tags', [])[:5])}\n"
                )
        
        # Add graph connections
        if retrieval_results['graph_connections']:
            context_parts.append("\n=== Related Connections ===\n")
            for i, conn in enumerate(retrieval_results['graph_connections'][:5], 1):
                source = conn['source']
                neighbor = conn['neighbor']
                rel = conn['relationship']
                
                source_name = source.get('name') or source.get('title') or source.get('keyword', 'Unknown')
                neighbor_name = neighbor.get('name') or neighbor.get('title') or neighbor.get('keyword', 'Unknown')
                
                context_parts.append(
                    f"{i}. {source_name} --[{rel}]--> {neighbor_name}\n"
                )
        
        # Add community information if available
        # Check if any semantic results have community assignments
        community_info_added = set()
        for result in retrieval_results.get('semantic_results', [])[:3]:
            meta = result.get('metadata', {})
            node_name = meta.get('name') or meta.get('title') or meta.get('keyword')
            if node_name:
                try:
                    members = self.get_community_members(node_name)
                    if members and len(members) > 0:
                        comm_id = members[0].get('community_id')
                        if comm_id and comm_id not in community_info_added:
                            community_info_added.add(comm_id)
                            member_names = [m['name'] for m in members[:5]]
                            context_parts.append(
                                f"\n=== Community Context ===\n"
                                f"Related entities in the same community: {', '.join(member_names)}\n"
                            )
                except:
                    pass  # Skip if community detection not available
        
        return "\n".join(context_parts)
    
    def generate_answer(self, query: str, context: str, conversation_history: Optional[List[Dict]] = None) -> str:
        """
        Generate answer using Claude with conversation memory
        
        Args:
            query: User query
            context: Retrieved context
            conversation_history: Previous conversation messages for context
            
        Returns:
            Generated answer
        """
        print("🤖 Generating answer with Claude...")
        
        # Build conversation history section
        history_section = ""
        if conversation_history and len(conversation_history) > 0:
            history_section = "\n\n=== Previous Conversation ===\n"
            for msg in conversation_history:
                role = msg.get('role', 'user')
                content = msg.get('content', '')
                if role == 'user':
                    history_section += f"User: {content}\n"
                elif role == 'assistant':
                    history_section += f"Assistant: {content}\n"
            history_section += "\nThe user may be asking a follow-up question. Use the conversation history to understand context and provide a coherent answer.\n"
        
        prompt = f"""You are a helpful assistant answering questions about talks, speakers, and topics from Connected Data World conferences.
{history_section}

Using the provided context, answer the user's question directly and concisely. Be specific and cite relevant talks or speakers when possible.

IMPORTANT FORMATTING RULES:
- Clean up any technical notation like "(DataCatalog)_-[poweredBy]-_(KnowledgeGraph)" to readable format like "DataCatalog powered by Knowledge Graph"
- Remove unnecessary parentheses and technical symbols from talk titles
- Use clear, natural language - be direct and avoid repetition
- Format lists with proper bullet points using "- " or "* "
- DO NOT use markdown formatting like **bold** or __italic__
- Instead, write naturally and let important terms stand out through context
- Use section headers only when organizing multiple distinct topics
- Be concise - avoid saying the same thing multiple times
- Write in a confident, informative tone
- If you don't have enough information, say so briefly at the end

CRITICAL: TRANSCRIPT CONTENT USAGE:
- When transcript excerpts are provided in the context, USE THEM DIRECTLY AND EXTENSIVELY
- Quote the actual transcript text - do NOT say "the transcript cuts off" or "presumably" or "I don't have additional content"
- Do NOT make assumptions about what might be in missing parts
- If a transcript snippet ends with "...", that's fine - just use what's there
- NEVER write phrases like "the transcript cuts off but presumably", "appears to be", "presumably describes", or "I don't have additional transcript content"
- Use the transcript content as-is, even if it seems incomplete
- If transcript content is available, quote it directly and confidently
- You MUST SUMMARIZE and SYNTHESIZE transcript content in your own words - use the transcripts as rich context to provide comprehensive answers
- Combine information from MULTIPLE transcript excerpts to give complete, comprehensive answers
- If there are multiple transcript snippets from the same talk, use ALL of them to provide a fuller picture
- Use transcript content to add depth, examples, and specific details to your answers
- Provide COMPLETE answers - don't stop mid-thought. Use all available transcript content to answer fully
- For follow-up questions like "tell me more", you MUST search through ALL provided transcript excerpts and extract additional relevant information
- If the user asks for more details, look through ALL transcript snippets in the context - there is likely more content available
- NEVER say "I don't have additional content" if transcript excerpts are present in the context - instead, extract and synthesize information from ALL available excerpts

CRITICAL: TIMESTAMP USAGE:
- Only include timestamps when:
  1. The user explicitly asks for them (e.g., "where can I find", "what timestamp", "at what time", "where in the video", "when did they say")
  2. The query context clearly suggests location/timing is important (e.g., "find that part", "when was that mentioned", "jump to that section")
  3. It's a follow-up question about finding specific information that was previously discussed
- Do NOT include timestamps in general answers unless requested
- When timestamps ARE needed, format them in a user-friendly way: "at 5:23", "around 2:15", "starting at 10:45"
- When quoting transcript content, only include timestamp if the user asked for location/timing
- If multiple timestamps are relevant, include all of them
- Make timestamps easy to understand - convert seconds to MM:SS or HH:MM:SS format when helpful
- Example (when asked): "You can find this explanation at 3:45 in the video" or "This is discussed around the 10-minute mark (10:00)"
- Example (when NOT asked): Just provide the content without mentioning timestamps

ANSWER STYLE:
- Start with a direct answer to the question
- Provide specific details from the context
- Use bullet points for lists of items
- Include direct quotes from transcripts when available - quote the actual text
- You can also summarize transcript content in your own words when it provides better context
- Synthesize information from multiple sources (transcripts, graph connections, semantic matches) to provide comprehensive answers
- Keep paragraphs short (2-3 sentences max)
- Write confidently about what IS in the transcript, not what might be
- ALWAYS cite sources: When mentioning information from a talk, include the talk title and speaker name (e.g., "As mentioned in [Talk Title] by [Speaker Name]...")
- For transcript quotes, cite the source: "In [Talk Title], [Speaker Name] said: '[quote]'"

Context:
{context}

Question: {query}

Answer the question directly and concisely. If transcript excerpts are in the context, quote them directly without making assumptions about missing content."""
        
        # Build messages with conversation history
        messages = []
        if conversation_history:
            # Add conversation history (last 6 messages max to avoid token limits)
            for msg in conversation_history[-6:]:
                messages.append({
                    "role": msg.get('role', 'user'),
                    "content": msg.get('content', '')
                })
        
        # Add current query
        messages.append({"role": "user", "content": prompt})
        
        response = self.llm_client.messages.create(
            model=self.config.llm.model,
            max_tokens=self.config.llm.max_tokens,
            temperature=self.config.llm.temperature,
            messages=messages
        )
        
        answer = response.content[0].text
        return answer
    
    def query(self, query: str, top_k: int = 5, verbose: bool = True) -> Dict[str, any]:
        """
        Complete RAG pipeline
        
        Args:
            query: User query
            top_k: Number of results to retrieve
            verbose: Print intermediate results
            
        Returns:
            Dictionary with answer and metadata
        """
        print("\n" + "=" * 70)
        print(f"💬 Query: {query}")
        print("=" * 70)
        
        # 1. Retrieve
        retrieval_results = self.hybrid_retrieve(query, top_k=top_k)
        
        # 2. Format context
        context = self.format_context(retrieval_results)
        
        if verbose:
            print("\n📄 Context Preview:")
            print(context[:500] + "...\n")
        
        # 3. Generate answer
        answer = self.generate_answer(query, context)
        
        print("\n" + "=" * 70)
        print("💡 Answer:")
        print("=" * 70)
        print(answer)
        print("=" * 70 + "\n")
        
        return {
            'query': query,
            'answer': answer,
            'context': context,
            'retrieval_results': retrieval_results
        }
    
    def close(self):
        """Close connections"""
        if self.neo4j_driver:
            self.neo4j_driver.close()


def main():
    """Test the RAG system"""
    rag = RAGSystem()
    
    # Test queries
    test_queries = [
        "What talks discuss knowledge graphs?",
        "Who spoke about graph thinking?",
        "Tell me about semantic technology talks",
    ]
    
    for query in test_queries:
        result = rag.query(query, top_k=5)
        print("\n" + "="*70 + "\n")
    
    rag.close()


if __name__ == "__main__":
    main()
