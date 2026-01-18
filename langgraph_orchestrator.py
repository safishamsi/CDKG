"""
LangGraph Orchestrator for Hybrid RAG with Multi-hop Reasoning

This module provides intelligent query routing and orchestration using:
- LangGraph for state management and tool calling
- LangChain for tool integration
- Multi-hop reasoning for complex queries
- Semantic similarity via vectors
- Graph traversal for relationship discovery
"""

from typing import TypedDict, Annotated, List, Dict, Any, Optional
from langchain_core.tools import tool
from langchain_anthropic import ChatAnthropic
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
import operator

from rag_system import RAGSystem
from config import config


# Define the state structure
class GraphState(TypedDict):
    """State for the LangGraph workflow"""
    query: str
    query_type: Optional[str]  # 'semantic', 'graph', 'hybrid', 'multi_hop'
    semantic_results: Annotated[List[Dict], operator.add]
    graph_results: Annotated[List[Dict], operator.add]
    transcript_results: Annotated[List[Dict], operator.add]
    multi_hop_paths: Annotated[List[Dict], operator.add]
    context: str
    answer: Optional[str]
    iteration: int
    max_hops: int
    conversation_history: Optional[List[Dict]]  # Previous conversation for context


class LangGraphOrchestrator:
    """Orchestrates hybrid RAG with LangGraph for intelligent routing"""
    
    def __init__(self, rag_system: RAGSystem):
        """
        Initialize orchestrator
        
        Args:
            rag_system: Initialized RAG system instance
        """
        self.rag = rag_system
        # Use Claude 3 Sonnet (stable version)
        self.llm = ChatAnthropic(
            model="claude-3-sonnet-20240229",
            api_key=config.llm.api_key,
            temperature=0.0
        )
        
        # Create tools
        self.tools = self._create_tools()
        self.tool_node = ToolNode(self.tools)
        
        # Build graph
        self.graph = self._build_graph()
        self.app = self.graph.compile()
    
    def _create_tools(self) -> List:
        """Create LangChain tools for RAG operations"""
        rag = self.rag  # Capture for closure
        
        @tool
        def semantic_search(query: str, top_k: int = 5) -> List[Dict]:
            """
            Perform semantic similarity search using vector embeddings.
            
            Use this for queries about:
            - Finding similar concepts, topics, or ideas
            - Semantic understanding of user intent
            - Finding talks/speakers/tags by meaning, not exact keywords
            
            Args:
                query: Search query
                top_k: Number of results to return
                
            Returns:
                List of semantically similar nodes with scores
            """
            results = rag.semantic_search(query, k=top_k)
            return [
                {
                    'node_type': r['node_type'],
                    'title': r['metadata'].get('title') or r['metadata'].get('name') or r['metadata'].get('keyword'),
                    'score': r['similarity_score'],
                    'metadata': r['metadata']
                }
                for r in results
            ]
        
        @tool
        def graph_traversal(entity_names: List[str], max_hops: int = 2) -> List[Dict]:
            """
            Perform graph traversal to find relationships and connections.
            
            Use this for queries about:
            - Finding connections between entities
            - Multi-hop relationships (e.g., speaker -> talks -> tags -> other speakers)
            - Discovering related content through graph structure
            - Complex reasoning about relationships
            
            Args:
                entity_names: List of entity names to start traversal from
                max_hops: Maximum number of hops to traverse (1-3)
                
            Returns:
                List of connected nodes and relationships
            """
            results = rag.graph_traversal(entity_names, max_depth=max_hops)
            return [
                {
                    'source': r['source'],
                    'relationship': r['relationship'],
                    'target': r['neighbor'],
                    'path_length': r.get('path_length', 1)
                }
                for r in results
            ]
        
        @tool
        def transcript_search(query: str, limit: int = 5) -> List[Dict]:
            """
            Search transcript content directly with timestamp support.
            
            Use this for queries about:
            - Specific quotes or statements from talks
            - Finding exact content mentioned in transcripts
            - Questions requiring verbatim answers from talk content
            
            Args:
                query: Search query
                limit: Maximum results to return
                
            Returns:
                List of talks with matching transcript content and timestamps
            """
            results = rag.transcript_search(query, limit=limit)
            return [
                {
                    'title': r.get('title'),
                    'speakers': r.get('speakers', []),
                    'transcript_snippet': r.get('transcript_snippet', '')[:300],
                    'timestamp': r.get('timestamp'),
                    'timestamp_seconds': r.get('timestamp_seconds')
                }
                for r in results
            ]
        
        @tool
        def multi_hop_reasoning(start_entity: str, target_entity: str, max_hops: int = 3) -> Dict:
            """
            Perform multi-hop reasoning to find paths between entities.
            
            Use this for complex queries like:
            - "How is speaker X related to topic Y?"
            - "What connects talk A to speaker B?"
            - Finding indirect relationships through multiple hops
            
            Args:
                start_entity: Starting entity name
                target_entity: Target entity name
                max_hops: Maximum hops to explore
                
            Returns:
                Path information between entities
            """
            paths = self._find_multi_hop_path(start_entity, target_entity, max_hops)
            return {
                'start': start_entity,
                'target': target_entity,
                'paths': paths,
                'found': len(paths) > 0
            }
        
        @tool
        def keyword_search(query: str, limit: int = 10) -> List[Dict]:
            """
            Perform keyword-based search in Neo4j.
            
            Use this for queries with specific keywords or exact matches.
            
            Args:
                query: Search query with keywords
                limit: Maximum results
                
            Returns:
                List of matching nodes
            """
            results = self.rag.cypher_search(query)
            return [
                {
                    'title': r.get('title'),
                    'speaker': r.get('speaker'),
                    'tags': r.get('tags', [])
                }
                for r in results[:limit]
            ]
        
        return [
            semantic_search,
            graph_traversal,
            transcript_search,
            multi_hop_reasoning,
            keyword_search
        ]
    
    def _find_multi_hop_path(self, start: str, target: str, max_hops: int = 3) -> List[Dict]:
        """Find paths between two entities using Cypher"""
        with self.rag.neo4j_driver.session() as session:
            # Try to find paths
            result = session.run(f"""
                MATCH path = shortestPath(
                    (start)-[*1..{max_hops}]-(target)
                )
                WHERE (
                    toLower(start.name) = toLower($start) OR
                    toLower(start.title) = toLower($start) OR
                    toLower(start.keyword) = toLower($start)
                )
                AND (
                    toLower(target.name) = toLower($target) OR
                    toLower(target.title) = toLower($target) OR
                    toLower(target.keyword) = toLower($target)
                )
                RETURN path, length(path) as path_length
                LIMIT 5
            """, start=start, target=target)
            
            paths = []
            for record in result:
                path = record['path']
                path_length = record['path_length']
                
                # Extract path details
                nodes = []
                relationships = []
                for i, node in enumerate(path.nodes):
                    node_type = list(node.labels)[0] if node.labels else 'Unknown'
                    node_name = node.get('name') or node.get('title') or node.get('keyword', 'Unknown')
                    nodes.append({'type': node_type, 'name': node_name})
                
                for rel in path.relationships:
                    relationships.append(rel.type)
                
                paths.append({
                    'nodes': nodes,
                    'relationships': relationships,
                    'length': path_length
                })
            
            return paths
    
    def _classify_query(self, query: str) -> str:
        """Classify query type using heuristics (faster than LLM)"""
        query_lower = query.lower()
        
        # Transcript/quote indicators: "what did", "say about", "mentioned", "said" (check first!)
        transcript_keywords = ['what did', 'say about', 'mentioned', 'said', 'quote']
        if any(kw in query_lower for kw in transcript_keywords):
            return 'hybrid'  # Need transcript + semantic + graph
        
        # Multi-hop indicators: "how is", "related to", "connected to", "path between"
        multi_hop_keywords = ['how is', 'related to', 'connected to', 'path between', 'relationship between', 'are related']
        if any(kw in query_lower for kw in multi_hop_keywords):
            return 'multi_hop'
        
        # Graph traversal indicators: "what talks did", "who gave", "speaker", "by"
        graph_keywords = ['what talks did', 'who gave', 'speaker', ' by ', 'talks by', 'gave']
        if any(kw in query_lower for kw in graph_keywords):
            return 'graph'
        
        # Semantic indicators: "discuss", "about", "topics", "talks about"
        semantic_keywords = ['discuss', 'talks about', 'topics', 'about', 'related topics']
        if any(kw in query_lower for kw in semantic_keywords):
            return 'semantic'
        
        # Default to hybrid for comprehensive answers
        return 'hybrid'
    
    def _route_query_node(self, state: GraphState) -> GraphState:
        """Route query node - classifies query type"""
        if state.get('query_type') is None:
            query_type = self._classify_query(state['query'])
            state['query_type'] = query_type
        return state
    
    def _route_query_decision(self, state: GraphState) -> str:
        """Route query decision function"""
        query_type = state.get('query_type', 'hybrid')
        
        if query_type == 'semantic':
            return 'semantic_search'
        elif query_type == 'graph':
            return 'graph_search'
        elif query_type == 'multi_hop':
            return 'multi_hop_reasoning'
        else:
            return 'hybrid_search'
    
    def _build_graph(self) -> StateGraph:
        """Build the LangGraph workflow"""
        
        def semantic_search_node(state: GraphState) -> GraphState:
            """Perform semantic search"""
            results = self.rag.semantic_search(state['query'], k=5)
            state['semantic_results'] = results
            return state
        
        def graph_search_node(state: GraphState) -> GraphState:
            """Perform graph traversal"""
            # First, try semantic search to find entities
            semantic_results = self.rag.semantic_search(state['query'], k=5)
            state['semantic_results'] = semantic_results
            
            # Extract entity names from semantic results
            entity_names = []
            for r in semantic_results[:5]:
                meta = r['metadata']
                if 'name' in meta and meta['name']:
                    entity_names.append(meta['name'])
                elif 'title' in meta and meta['title']:
                    entity_names.append(meta['title'])
                elif 'keyword' in meta and meta['keyword']:
                    entity_names.append(meta['keyword'])
            
            # Also extract capitalized words from query (likely proper nouns)
            query_words = state['query'].split()
            capitalized_words = [w.strip('.,!?;:') for w in query_words if w[0].isupper() and len(w) > 2]
            entity_names.extend(capitalized_words)
            
            # Remove duplicates while preserving order
            seen = set()
            unique_entities = []
            for e in entity_names:
                e_lower = e.lower()
                if e_lower not in seen:
                    seen.add(e_lower)
                    unique_entities.append(e)
            
            # Limit to top 5 entities
            entity_names = unique_entities[:5]
            
            if entity_names:
                results = self.rag.graph_traversal(entity_names, max_depth=state.get('max_hops', 2))
                state['graph_results'] = results
            else:
                state['graph_results'] = []
            
            return state
        
        def multi_hop_node(state: GraphState) -> GraphState:
            """Perform multi-hop reasoning with transcript support"""
            # Expand query using conversation history for follow-up questions
            expanded_query = state['query']
            conversation_history = state.get('conversation_history', [])
            
            # If this looks like a follow-up, expand it with previous context
            if len(expanded_query.split()) < 5 and conversation_history:
                previous_queries = []
                for msg in conversation_history[-4:]:
                    if msg.get('role') == 'user':
                        previous_queries.append(msg.get('content', ''))
                
                expanded_keywords = []
                for prev_query in previous_queries:
                    words = prev_query.split()
                    for word in words:
                        if word[0].isupper() and len(word) > 2:
                            expanded_keywords.append(word.strip('.,!?;:'))
                
                if expanded_keywords:
                    expanded_query = f"{expanded_query} {' '.join(expanded_keywords[:3])}"
            
            # First do semantic search to find entities (use expanded query)
            semantic_results = self.rag.semantic_search(expanded_query, k=5)
            state['semantic_results'] = semantic_results
            
            # Extract entities from semantic results
            entities = []
            for r in semantic_results[:5]:
                meta = r['metadata']
                if 'name' in meta and meta['name']:
                    entities.append(meta['name'])
                elif 'title' in meta and meta['title']:
                    entities.append(meta['title'])
                elif 'keyword' in meta and meta['keyword']:
                    entities.append(meta['keyword'])
            
            # Also extract capitalized words from query
            query_words = state['query'].split()
            capitalized_words = [w.strip('.,!?;:') for w in query_words if w[0].isupper() and len(w) > 2]
            entities.extend(capitalized_words)
            
            # Remove duplicates
            seen = set()
            unique_entities = []
            for e in entities:
                e_lower = e.lower()
                if e_lower not in seen:
                    seen.add(e_lower)
                    unique_entities.append(e)
            
            # Try to find paths between entities
            if len(unique_entities) >= 2:
                paths = self._find_multi_hop_path(unique_entities[0], unique_entities[1], max_hops=state.get('max_hops', 3))
                state['multi_hop_paths'] = paths
                
                # Also do graph traversal from all entities
                graph_results = self.rag.graph_traversal(unique_entities[:3], max_depth=state.get('max_hops', 2))
                state['graph_results'] = graph_results
            elif len(unique_entities) == 1:
                # Single entity - do graph traversal
                graph_results = self.rag.graph_traversal(unique_entities, max_depth=state.get('max_hops', 2))
                state['graph_results'] = graph_results
                state['multi_hop_paths'] = []
            else:
                state['multi_hop_paths'] = []
                state['graph_results'] = []
            
            # Add transcript search for multi-hop reasoning (get relevant transcript content)
            transcript = self.rag.transcript_search(expanded_query, limit=15)  # Increased from 8 to 15
            state['transcript_results'] = transcript
            
            return state
        
        def hybrid_search_node(state: GraphState) -> GraphState:
            """Perform hybrid search (semantic + graph + transcript)"""
            # Expand query using conversation history for follow-up questions
            expanded_query = state['query']
            conversation_history = state.get('conversation_history', [])
            
            # If this looks like a follow-up (short, vague query, or mentions "he", "they", "it", etc.), expand it
            query_lower = expanded_query.lower()
            is_followup = (len(expanded_query.split()) < 5) or any(pronoun in query_lower for pronoun in ['he ', 'she ', 'they ', 'it ', 'this ', 'that ', 'these ', 'those '])
            
            if (is_followup or len(expanded_query.split()) < 8) and conversation_history:
                # Extract key entities and topics from previous conversation
                previous_queries = []
                previous_answers = []
                for msg in conversation_history[-6:]:  # Last 6 messages for more context
                    if msg.get('role') == 'user':
                        previous_queries.append(msg.get('content', ''))
                    elif msg.get('role') == 'assistant':
                        previous_answers.append(msg.get('content', ''))
                
                # Extract capitalized words (likely proper nouns) from previous queries
                expanded_keywords = []
                for prev_query in previous_queries:
                    words = prev_query.split()
                    for word in words:
                        if word[0].isupper() and len(word) > 2:
                            expanded_keywords.append(word.strip('.,!?;:'))
                
                # Also extract important nouns from previous answers (speaker names, talk titles, topics)
                import re
                for prev_answer in previous_answers:
                    # Find capitalized phrases (2-3 words) - likely names/titles
                    capitalized_phrases = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,2}\b', prev_answer)
                    for phrase in capitalized_phrases:
                        if len(phrase.split()) >= 2:  # Multi-word phrases are likely names/titles
                            expanded_keywords.append(phrase)
                    
                    # Extract quoted text (often talk titles or important terms)
                    quoted_text = re.findall(r'"([^"]+)"', prev_answer)
                    expanded_keywords.extend(quoted_text)
                    
                    # Extract patterns like "by [Name]" or "in [Title]"
                    by_pattern = re.findall(r'\bby\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)', prev_answer, re.IGNORECASE)
                    in_pattern = re.findall(r'\bin\s+["\']?([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)', prev_answer, re.IGNORECASE)
                    expanded_keywords.extend(by_pattern)
                    expanded_keywords.extend(in_pattern)
                
                # Resolve pronouns in the query
                pronoun_resolutions = {}
                if 'he ' in query_lower or ' he' in query_lower:
                    # Find the most recent person mentioned
                    for prev_answer in reversed(previous_answers):
                        person_match = re.search(r'\b([A-Z][a-z]+\s+[A-Z][a-z]+)\b', prev_answer)
                        if person_match:
                            pronoun_resolutions['he'] = person_match.group(1)
                            break
                
                if 'they ' in query_lower or ' they' in query_lower:
                    # Find multiple people or organizations
                    for prev_answer in reversed(previous_answers):
                        people = re.findall(r'\b([A-Z][a-z]+\s+[A-Z][a-z]+)\b', prev_answer)
                        if people:
                            pronoun_resolutions['they'] = ' '.join(people[:2])
                            break
                
                # Replace pronouns with resolved entities
                for pronoun, resolution in pronoun_resolutions.items():
                    expanded_query = expanded_query.replace(pronoun, resolution)
                    expanded_query = expanded_query.replace(pronoun.capitalize(), resolution)
                
                # If we found keywords from history, add them to the query
                if expanded_keywords:
                    # Remove duplicates while preserving order
                    seen = set()
                    unique_keywords = []
                    for kw in expanded_keywords:
                        kw_lower = kw.lower()
                        if kw_lower not in seen and len(kw.strip()) > 1:
                            seen.add(kw_lower)
                            unique_keywords.append(kw)
                    
                    if unique_keywords:
                        expanded_query = f"{expanded_query} {' '.join(unique_keywords[:5])}"  # Up to 5 keywords
                        print(f"📝 Expanded follow-up query: {expanded_query}")
            
            # 1. Semantic search (use expanded query)
            semantic = self.rag.semantic_search(expanded_query, k=5)
            state['semantic_results'] = semantic
            
            # 2. Extract entities for graph traversal
            entity_names = []
            for r in semantic[:5]:
                meta = r['metadata']
                if 'name' in meta and meta['name']:
                    entity_names.append(meta['name'])
                elif 'title' in meta and meta['title']:
                    entity_names.append(meta['title'])
                elif 'keyword' in meta and meta['keyword']:
                    entity_names.append(meta['keyword'])
            
            # Also extract capitalized words from query
            query_words = expanded_query.split()
            capitalized_words = [w.strip('.,!?;:') for w in query_words if w[0].isupper() and len(w) > 2]
            entity_names.extend(capitalized_words)
            
            # Remove duplicates
            seen = set()
            unique_entities = []
            for e in entity_names:
                e_lower = e.lower()
                if e_lower not in seen:
                    seen.add(e_lower)
                    unique_entities.append(e)
            
            entity_names = unique_entities[:5]
            
            # 3. Graph traversal
            if entity_names:
                graph = self.rag.graph_traversal(entity_names, max_depth=state.get('max_hops', 2))
                state['graph_results'] = graph
            else:
                state['graph_results'] = []
            
            # 4. Transcript search (use expanded query and get more results for better coverage)
            transcript = self.rag.transcript_search(expanded_query, limit=15)  # Increased from 10 to 15
            state['transcript_results'] = transcript
            
            return state
        
        def generate_answer_node(state: GraphState) -> GraphState:
            """Generate final answer using all retrieved context with confidence scoring"""
            # Format context (include all expected keys)
            retrieval_results = {
                'semantic_results': state.get('semantic_results', []),
                'keyword_results': [],  # Not used in orchestrator, but required by format_context
                'graph_connections': state.get('graph_results', []),
                'transcript_results': state.get('transcript_results', []),
                'multi_hop_paths': state.get('multi_hop_paths', [])
            }
            
            # Calculate confidence score based on retrieval quality
            confidence = self._calculate_confidence(retrieval_results)
            state['confidence'] = confidence
            
            context = self.rag.format_context(retrieval_results)
            state['context'] = context
            
            # Get conversation history from state
            history = state.get('conversation_history', [])
            
            # Generate answer with conversation history
            answer = self.rag.generate_answer(state['query'], context, conversation_history=history)
            state['answer'] = answer
            
            return state
        
        def _calculate_confidence(self, retrieval_results: Dict) -> float:
            """
            Calculate confidence score based on retrieval quality
            
            Returns:
                Confidence score between 0.0 and 1.0
            """
            confidence = 0.0
            
            # Semantic results contribute to confidence
            semantic_results = retrieval_results.get('semantic_results', [])
            if semantic_results:
                # Average similarity score (normalized to 0-1)
                avg_similarity = sum(r.get('similarity_score', 0) for r in semantic_results) / len(semantic_results)
                confidence += avg_similarity * 0.3  # 30% weight
            
            # Transcript results indicate direct content match
            transcript_results = retrieval_results.get('transcript_results', [])
            if transcript_results:
                # Having transcript results is a strong signal
                confidence += 0.4  # 40% weight
                # Bonus if multiple transcript results
                if len(transcript_results) > 1:
                    confidence += 0.1
            
            # Graph connections show relationship understanding
            graph_results = retrieval_results.get('graph_connections', [])
            if graph_results:
                confidence += 0.2  # 20% weight
            
            # Multi-hop paths indicate complex reasoning capability
            multi_hop = retrieval_results.get('multi_hop_paths', [])
            if multi_hop:
                confidence += 0.1  # 10% weight
            
            # Cap at 1.0
            return min(confidence, 1.0)
        
        # Build graph
        workflow = StateGraph(GraphState)
        
        # Add nodes
        workflow.add_node("route_query", self._route_query_node)
        workflow.add_node("semantic_search", semantic_search_node)
        workflow.add_node("graph_search", graph_search_node)
        workflow.add_node("multi_hop_reasoning", multi_hop_node)
        workflow.add_node("hybrid_search", hybrid_search_node)
        workflow.add_node("generate_answer", generate_answer_node)
        
        # Set entry point
        workflow.set_entry_point("route_query")
        
        # Add conditional routing
        workflow.add_conditional_edges(
            "route_query",
            self._route_query_decision,
            {
                "semantic_search": "semantic_search",
                "graph_search": "graph_search",
                "multi_hop_reasoning": "multi_hop_reasoning",
                "hybrid_search": "hybrid_search"
            }
        )
        
        # All paths lead to answer generation
        workflow.add_edge("semantic_search", "generate_answer")
        workflow.add_edge("graph_search", "generate_answer")
        workflow.add_edge("multi_hop_reasoning", "generate_answer")
        workflow.add_edge("hybrid_search", "generate_answer")
        
        # End
        workflow.add_edge("generate_answer", END)
        
        return workflow
    
    def query(self, query: str, max_hops: int = 2, use_tools: bool = False, conversation_history: Optional[List[Dict]] = None) -> Dict[str, Any]:
        """
        Process query using LangGraph orchestration
        
        Args:
            query: User query
            max_hops: Maximum hops for graph traversal
            use_tools: Whether to use LangChain tools (for agent mode)
            
        Returns:
            Complete result with answer and metadata
        """
        if use_tools:
            # Use LLM with tools (agent mode)
            tools = self.tools
            llm_with_tools = self.llm.bind_tools(tools)
            
            # Create agent
            from langgraph.prebuilt import create_react_agent
            agent = create_react_agent(llm_with_tools, tools)
            
            # Run agent
            result = agent.invoke({"messages": [("user", query)]})
            
            return {
                'query': query,
                'answer': result['messages'][-1].content,
                'tool_calls': [msg.tool_calls for msg in result['messages'] if hasattr(msg, 'tool_calls')]
            }
        else:
            # Use state graph
            initial_state = {
                'query': query,
                'query_type': None,
                'semantic_results': [],
                'graph_results': [],
                'transcript_results': [],
                'multi_hop_paths': [],
                'context': '',
                'answer': None,
                'iteration': 0,
                'max_hops': max_hops,
                'conversation_history': conversation_history or []
            }
            
            result = self.app.invoke(initial_state)
            
            return {
                'query': query,
                'query_type': result.get('query_type'),
                'answer': result.get('answer'),
                'confidence': result.get('confidence'),
                'context': result.get('context'),
                'semantic_results': result.get('semantic_results', []),
                'graph_results': result.get('graph_results', []),
                'transcript_results': result.get('transcript_results', []),
                'multi_hop_paths': result.get('multi_hop_paths', [])
            }
    
    def close(self):
        """Close connections"""
        self.rag.close()

