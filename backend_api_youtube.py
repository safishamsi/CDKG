"""
Enhanced Backend API with YouTube Video Integration
"""

import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
os.environ['TRANSFORMERS_NO_TF'] = '1'

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, HttpUrl
from typing import Optional, List, Dict, Any
import uvicorn
from datetime import datetime

from rag_system import RAGSystem
from langgraph_orchestrator import LangGraphOrchestrator
from youtube_processor import YouTubeVideoProcessor

# Initialize FastAPI app
app = FastAPI(
    title="CDKG RAG Chatbot API with YouTube Integration",
    description="Hybrid RAG system with YouTube video ingestion",
    version="2.0.0"
)

# CORS middleware - Allow frontend from any origin (for demo purposes)
# In production, restrict to specific domains
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for demo - restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global instances
rag_system = None
orchestrator = None
youtube_processor = None

# Track processing jobs
processing_jobs = {}

# Track monitoring status
monitoring_status = {
    'enabled': False,
    'channel_id': None,
    'channel_username': None,
    'check_interval_minutes': 60,
    'last_check': None,
    'processed_count': 0,
    'failed_count': 0
}


class Message(BaseModel):
    """Single message in conversation history"""
    role: str  # 'user' or 'assistant'
    content: str

class QueryRequest(BaseModel):
    """Request model for chat queries"""
    query: str
    max_hops: Optional[int] = 2
    use_tools: Optional[bool] = False
    conversation_history: Optional[List[Message]] = []  # Previous messages for context


class QueryResponse(BaseModel):
    """Response model for chat queries"""
    query: str
    answer: str
    query_type: Optional[str] = None
    retrieval_stats: Dict[str, int]
    sources: Optional[List[Dict[str, Any]]] = None
    error: Optional[str] = None


class YouTubeRequest(BaseModel):
    """Request model for YouTube video processing"""
    url: HttpUrl


class YouTubeResponse(BaseModel):
    """Response model for YouTube video processing"""
    status: str
    message: str
    job_id: Optional[str] = None
    video_info: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class JobStatusResponse(BaseModel):
    """Response model for job status"""
    job_id: str
    status: str
    progress: str
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


@app.on_event("startup")
async def startup_event():
    """Initialize systems on startup"""
    global rag_system, orchestrator, youtube_processor
    import threading
    
    def initialize_systems():
        try:
            print("🚀 Initializing systems...")
            print("   This may take a minute (loading ML models)...")
            
            # Initialize RAG system (loads embedding model - can take 30-60 seconds)
            print("   Loading RAG system...")
            global rag_system
            rag_system = RAGSystem()
            
            # Initialize orchestrator
            print("   Initializing orchestrator...")
            global orchestrator
            orchestrator = LangGraphOrchestrator(rag_system)
            
            # Initialize YouTube processor (lightweight, no heavy loading)
            print("   Initializing YouTube processor...")
            global youtube_processor
            youtube_processor = YouTubeVideoProcessor()
            
            print("✅ All systems ready!")
        except Exception as e:
            print(f"❌ Error initializing systems: {e}")
            import traceback
            traceback.print_exc()
            print("⚠️  Server starting with limited functionality")
    
    # Run initialization in background thread (non-blocking)
    init_thread = threading.Thread(target=initialize_systems, daemon=True)
    init_thread.start()
    print("⏳ Server starting, systems initializing in background...")


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
        "service": "CDKG RAG Chatbot API with YouTube",
        "version": "2.0.0",
        "features": [
            "Hybrid RAG (Semantic + Graph + Keyword)",
            "Transcript search",
            "YouTube video ingestion",
            "LangGraph orchestration"
        ]
    }


@app.get("/health")
async def health():
    """Health check with system status"""
    global rag_system, orchestrator, youtube_processor
    try:
        # Quick check if systems are ready
        rag_ready = rag_system is not None
        orchestrator_ready = orchestrator is not None
        youtube_ready = youtube_processor is not None
        
        # If RAG system exists, test Neo4j connection
        neo4j_connected = False
        if rag_system and rag_system.neo4j_driver:
            try:
                rag_system.neo4j_driver.verify_connectivity()
                neo4j_connected = True
            except:
                pass
        
        return {
            "status": "healthy" if (rag_ready and orchestrator_ready) else "initializing",
            "rag_system": rag_ready,
            "orchestrator": orchestrator_ready,
            "youtube_processor": youtube_ready,
            "neo4j_connected": neo4j_connected,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
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
        # Convert conversation history to list of dicts
        history = []
        if request.conversation_history:
            for msg in request.conversation_history[-6:]:  # Keep last 6 messages (3 exchanges)
                history.append({
                    'role': msg.role,
                    'content': msg.content
                })
        
        # Process query with conversation history
        result = orchestrator.query(
            query=request.query,
            max_hops=request.max_hops,
            use_tools=request.use_tools,
            conversation_history=history
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
        
        # Add transcript results with full timestamp info
        for r in result.get('transcript_results', [])[:3]:
            title = r.get('title', 'Unknown')
            title = title.replace('(DataCatalog)_-[poweredBy]-_(KnowledgeGraph)', 'DataCatalog powered by Knowledge Graph')
            title = title.replace('_-[', ' ')
            title = title.replace(']-_', ' ')
            
            # Format timestamp for display
            timestamp_display = None
            if r.get('timestamp'):
                timestamp_seconds = r.get('timestamp_seconds', 0)
                if timestamp_seconds:
                    minutes = int(timestamp_seconds // 60)
                    seconds = int(timestamp_seconds % 60)
                    timestamp_display = f"{minutes}:{seconds:02d}"
                    if minutes >= 60:
                        hours = minutes // 60
                        mins = minutes % 60
                        timestamp_display = f"{hours}:{mins:02d}:{seconds:02d}"
                else:
                    timestamp_display = r.get('timestamp')
            
            source_entry = {
                'type': 'transcript',
                'title': title,
                'timestamp': r.get('timestamp'),
                'timestamp_seconds': r.get('timestamp_seconds'),
                'timestamp_display': timestamp_display,
                'snippet': r.get('transcript_snippet', '')[:150],
                'video_url': r.get('video_url'),
                'video_link': r.get('video_link'),
                'youtube_id': r.get('youtube_id')
            }
            sources.append(source_entry)
        
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
        
        # Clean up answer
        answer = result.get('answer', 'No answer generated')
        answer = answer.replace('(DataCatalog)_-[poweredBy]-_(KnowledgeGraph)', 'DataCatalog powered by Knowledge Graph')
        answer = answer.replace('_-[', ' ')
        answer = answer.replace(']-_', ' ')
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


def process_youtube_video_background(job_id: str, url: str):
    """Background task to process YouTube video"""
    global youtube_processor, processing_jobs
    
    try:
        processing_jobs[job_id] = {
            'status': 'processing',
            'progress': 'Downloading video info...',
            'started_at': datetime.now().isoformat()
        }
        
        # Process video
        success = youtube_processor.process_youtube_url(url)
        
        if success:
            processing_jobs[job_id] = {
                'status': 'completed',
                'progress': 'Video successfully added to knowledge graph',
                'completed_at': datetime.now().isoformat(),
                'result': {
                    'success': True,
                    'url': url
                }
            }
        else:
            processing_jobs[job_id] = {
                'status': 'failed',
                'progress': 'Failed to process video',
                'error': 'Processing failed - see logs for details',
                'completed_at': datetime.now().isoformat()
            }
    
    except Exception as e:
        processing_jobs[job_id] = {
            'status': 'failed',
            'progress': 'Error processing video',
            'error': str(e),
            'completed_at': datetime.now().isoformat()
        }


@app.post("/api/youtube/add", response_model=YouTubeResponse)
async def add_youtube_video(request: YouTubeRequest, background_tasks: BackgroundTasks):
    """
    Add a YouTube video to the knowledge graph
    
    This endpoint:
    1. Downloads video metadata and transcript
    2. Creates Talk node in Neo4j
    3. Generates and stores embeddings
    4. Makes video searchable in RAG system
    
    Args:
        request: YouTube video URL
        background_tasks: FastAPI background tasks
        
    Returns:
        Response with job_id to track processing
    """
    global youtube_processor
    
    if not youtube_processor:
        raise HTTPException(status_code=503, detail="YouTube processor not initialized")
    
    try:
        url = str(request.url)
        
        # Generate job ID
        import hashlib
        job_id = hashlib.md5(f"{url}{datetime.now().isoformat()}".encode()).hexdigest()[:12]
        
        # Add to background tasks
        background_tasks.add_task(process_youtube_video_background, job_id, url)
        
        return YouTubeResponse(
            status="processing",
            message="Video processing started in background",
            job_id=job_id
        )
    
    except Exception as e:
        return YouTubeResponse(
            status="error",
            message="Failed to start processing",
            error=str(e)
        )


@app.get("/api/youtube/status/{job_id}", response_model=JobStatusResponse)
async def get_job_status(job_id: str):
    """
    Get status of a YouTube video processing job
    
    Args:
        job_id: Job identifier returned from /api/youtube/add
        
    Returns:
        Job status and progress
    """
    global processing_jobs
    
    if job_id not in processing_jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = processing_jobs[job_id]
    
    return JobStatusResponse(
        job_id=job_id,
        status=job['status'],
        progress=job['progress'],
        result=job.get('result'),
        error=job.get('error')
    )


@app.get("/api/youtube/jobs")
async def list_jobs():
    """List all processing jobs"""
    global processing_jobs
    return {
        "total_jobs": len(processing_jobs),
        "jobs": processing_jobs
    }


@app.get("/api/graph")
async def get_graph_data(
    query: Optional[str] = None,
    limit: int = 100,
    depth: int = 2
):
    """
    Get graph data from Neo4j for visualization
    
    Args:
        query: Optional search term to filter nodes
        limit: Maximum number of nodes to return
        depth: Maximum relationship depth to traverse
        
    Returns:
        Graph data in format: {nodes: [], links: []}
    """
    global rag_system
    
    if not rag_system:
        raise HTTPException(status_code=503, detail="RAG system not initialized")
    
    try:
        from neo4j import GraphDatabase
        from config import config
        
        driver = GraphDatabase.driver(
            config.neo4j.uri,
            auth=(config.neo4j.user, config.neo4j.password)
        )
        
        nodes = []
        links = []
        node_map = {}  # Track nodes by ID to avoid duplicates
        
        with driver.session() as session:
            if query:
                # Search-based subgraph: find nodes matching query and their neighbors
                cypher_query = f"""
                MATCH (n)
                WHERE toLower(COALESCE(n.name, '')) CONTAINS toLower($query)
                   OR toLower(COALESCE(n.title, '')) CONTAINS toLower($query)
                   OR toLower(COALESCE(n.keyword, '')) CONTAINS toLower($query)
                WITH n
                MATCH path = (n)-[*1..{depth}]-(connected)
                RETURN DISTINCT
                    n,
                    labels(n)[0] as n_type,
                    connected,
                    labels(connected)[0] as connected_type,
                    relationships(path)[0] as rel
                LIMIT $limit
                """
                result = session.run(cypher_query, query=query, limit=limit)
            else:
                # General graph: get a sample of nodes and relationships
                cypher_query = f"""
                MATCH (n)-[r]->(m)
                RETURN n, labels(n)[0] as n_type, r, m, labels(m)[0] as m_type
                LIMIT $limit
                """
                result = session.run(cypher_query, limit=limit)
            
            for record in result:
                # Process source node
                n = record['n']
                n_type = record['n_type']
                n_id = n.get('name') or n.get('title') or n.get('keyword') or str(n.id)
                n_name = n.get('name') or n.get('title') or n.get('keyword') or 'Unknown'
                
                if n_id not in node_map:
                    # Determine node group for coloring
                    group = 1  # Default
                    if n_type == 'Speaker':
                        group = 2
                    elif n_type == 'Talk':
                        group = 3
                    elif n_type == 'Tag':
                        group = 1
                    elif n_type == 'Event':
                        group = 4
                    elif n_type == 'Category':
                        group = 5
                    
                    node_map[n_id] = {
                        'id': n_id,
                        'name': n_name,
                        'type': n_type,
                        'group': group,
                        'value': 1
                    }
                    nodes.append(node_map[n_id])
                
                # Process target node (if relationship exists)
                if 'm' in record and record['m']:
                    m = record['m']
                    m_type = record.get('m_type', 'Unknown')
                    m_id = m.get('name') or m.get('title') or m.get('keyword') or str(m.id)
                    m_name = m.get('name') or m.get('title') or m.get('keyword') or 'Unknown'
                    
                    if m_id not in node_map:
                        group = 1
                        if m_type == 'Speaker':
                            group = 2
                        elif m_type == 'Talk':
                            group = 3
                        elif m_type == 'Tag':
                            group = 1
                        elif m_type == 'Event':
                            group = 4
                        elif m_type == 'Category':
                            group = 5
                        
                        node_map[m_id] = {
                            'id': m_id,
                            'name': m_name,
                            'type': m_type,
                            'group': group,
                            'value': 1
                        }
                        nodes.append(node_map[m_id])
                    
                    # Add relationship
                    rel = record.get('rel')
                    rel_type = rel.type if rel else 'RELATED_TO'
                    
                    # Avoid duplicate links
                    link_key = f"{n_id}->{m_id}"
                    if not any(l.get('key') == link_key for l in links):
                        links.append({
                            'source': n_id,
                            'target': m_id,
                            'value': 1,
                            'type': rel_type,
                            'key': link_key
                        })
        
        driver.close()
        
        return {
            "nodes": nodes[:limit],
            "links": links[:limit * 2],  # Allow more links than nodes
            "total_nodes": len(nodes),
            "total_links": len(links)
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/graph/around")
async def get_graph_around_node(
    node_id: str,
    depth: int = 2,
    limit: int = 50
):
    """
    Get graph data around a specific node
    
    Args:
        node_id: Name/title/keyword of the node
        depth: Maximum relationship depth
        limit: Maximum nodes to return
        
    Returns:
        Graph data centered around the specified node
    """
    global rag_system
    
    if not rag_system:
        raise HTTPException(status_code=503, detail="RAG system not initialized")
    
    try:
        from neo4j import GraphDatabase
        from config import config
        
        driver = GraphDatabase.driver(
            config.neo4j.uri,
            auth=(config.neo4j.user, config.neo4j.password)
        )
        
        nodes = []
        links = []
        node_map = {}
        
        with driver.session() as session:
            # Find the center node and its neighbors
            cypher_query = f"""
            MATCH (center)
            WHERE toLower(COALESCE(center.name, '')) = toLower($node_id)
               OR toLower(COALESCE(center.title, '')) = toLower($node_id)
               OR toLower(COALESCE(center.keyword, '')) = toLower($node_id)
            WITH center
            MATCH path = (center)-[*1..{depth}]-(neighbor)
            RETURN DISTINCT
                center,
                labels(center)[0] as center_type,
                neighbor,
                labels(neighbor)[0] as neighbor_type,
                relationships(path)[0] as rel
            LIMIT $limit
            """
            result = session.run(cypher_query, node_id=node_id, limit=limit)
            
            for record in result:
                # Center node
                center = record['center']
                center_type = record['center_type']
                center_id = center.get('name') or center.get('title') or center.get('keyword') or str(center.id)
                center_name = center.get('name') or center.get('title') or center.get('keyword') or 'Unknown'
                
                if center_id not in node_map:
                    group = 2 if center_type == 'Speaker' else (3 if center_type == 'Talk' else 1)
                    node_map[center_id] = {
                        'id': center_id,
                        'name': center_name,
                        'type': center_type,
                        'group': group,
                        'value': 2  # Larger for center node
                    }
                    nodes.append(node_map[center_id])
                
                # Neighbor node
                neighbor = record['neighbor']
                neighbor_type = record['neighbor_type']
                neighbor_id = neighbor.get('name') or neighbor.get('title') or neighbor.get('keyword') or str(neighbor.id)
                neighbor_name = neighbor.get('name') or neighbor.get('title') or neighbor.get('keyword') or 'Unknown'
                
                if neighbor_id not in node_map:
                    group = 2 if neighbor_type == 'Speaker' else (3 if neighbor_type == 'Talk' else 1)
                    node_map[neighbor_id] = {
                        'id': neighbor_id,
                        'name': neighbor_name,
                        'type': neighbor_type,
                        'group': group,
                        'value': 1
                    }
                    nodes.append(node_map[neighbor_id])
                
                # Relationship
                rel = record.get('rel')
                rel_type = rel.type if rel else 'RELATED_TO'
                
                link_key = f"{center_id}->{neighbor_id}"
                if not any(l.get('key') == link_key for l in links):
                    links.append({
                        'source': center_id,
                        'target': neighbor_id,
                        'value': 1,
                        'type': rel_type,
                        'key': link_key
                    })
        
        driver.close()
        
        return {
            "nodes": nodes,
            "links": links,
            "center_node": node_id,
            "total_nodes": len(nodes),
            "total_links": len(links)
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/stats")
async def get_stats():
    """Get knowledge graph statistics"""
    global rag_system
    
    if not rag_system:
        raise HTTPException(status_code=503, detail="RAG system not initialized")
    
    try:
        from neo4j import GraphDatabase
        from config import config
        
        driver = GraphDatabase.driver(
            config.neo4j.uri,
            auth=(config.neo4j.user, config.neo4j.password)
        )
        
        with driver.session() as session:
            # Get node counts
            result = session.run("""
                MATCH (n)
                RETURN labels(n)[0] as label, count(n) as count
            """)
            
            node_counts = {record['label']: record['count'] for record in result}
            
            # Get relationship count
            result = session.run("MATCH ()-[r]->() RETURN count(r) as count")
            rel_count = result.single()['count']
            
            # Get talks with transcripts
            result = session.run("""
                MATCH (t:Talk)
                WHERE t.transcript IS NOT NULL
                RETURN count(t) as count
            """)
            transcript_count = result.single()['count']
            
            # Get YouTube videos
            result = session.run("""
                MATCH (t:Talk)
                WHERE t.youtube_id IS NOT NULL
                RETURN count(t) as count
            """)
            youtube_count = result.single()['count']
            
            # Get community count
            result = session.run("""
                MATCH (c:Community)
                RETURN count(c) as count
            """)
            community_count = result.single()['count'] if result.single() else 0
        
        driver.close()
        
        return {
            "nodes": node_counts,
            "relationships": rel_count,
            "talks_with_transcripts": transcript_count,
            "youtube_videos": youtube_count,
            "communities": community_count,
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/communities/detect")
async def detect_communities(
    limit: Optional[int] = None,
    resolution: float = 1.0
):
    """
    Run Leiden community detection on the knowledge graph
    
    Args:
        limit: Optional limit on relationships to process (None = all)
        resolution: Resolution parameter (higher = more communities)
        
    Returns:
        Detection results
    """
    try:
        from community_detection import CommunityDetector
        
        detector = CommunityDetector()
        
        # Run detection in background (this can take time)
        communities = detector.run_detection(limit=limit, resolution=resolution, store=True)
        
        num_communities = len(set(communities.values()))
        
        detector.close()
        
        return {
            "status": "success",
            "communities_detected": num_communities,
            "nodes_assigned": len(communities),
            "resolution": resolution,
            "timestamp": datetime.now().isoformat()
        }
    
    except ImportError as e:
        raise HTTPException(
            status_code=503,
            detail=f"Community detection libraries not installed: {str(e)}. Run: pip install leidenalg python-igraph networkx"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/communities")
async def get_communities(community_id: Optional[int] = None):
    """
    Get information about communities
    
    Args:
        community_id: Optional specific community ID
        
    Returns:
        Community information
    """
    try:
        from community_detection import CommunityDetector
        
        detector = CommunityDetector()
        
        if community_id is not None:
            comm_info = detector.get_community_info(community_id=community_id)
        else:
            comm_info = detector.get_community_info()
        
        detector.close()
        
        return {
            "communities": comm_info,
            "count": len(comm_info),
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/communities/node/{node_id}")
async def get_node_community(node_id: str):
    """
    Get community information for a specific node
    
    Args:
        node_id: Node identifier (name, title, or keyword)
        
    Returns:
        Community information for the node
    """
    try:
        from community_detection import CommunityDetector
        
        detector = CommunityDetector()
        comm_info = detector.get_node_community(node_id)
        detector.close()
        
        if comm_info:
            return {
                "node_id": node_id,
                "community": comm_info,
                "timestamp": datetime.now().isoformat()
            }
        else:
            raise HTTPException(status_code=404, detail=f"Node '{node_id}' not found or not assigned to a community")
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/youtube/monitor/start")
async def start_monitoring(
    channel_id: Optional[str] = None,
    channel_username: Optional[str] = None,
    check_interval_minutes: int = 60
):
    """
    Start automatic YouTube channel monitoring
    
    Args:
        channel_id: YouTube channel ID (optional)
        channel_username: YouTube channel username (e.g., @ConnectedData)
        check_interval_minutes: Minutes between checks (default: 60)
        
    Returns:
        Status response
    """
    global monitoring_status
    
    try:
        if monitoring_status['enabled']:
            return {
                "status": "already_running",
                "message": "Monitoring is already enabled",
                "monitoring_status": monitoring_status
            }
        
        # Default to Connected Data channel if not specified
        if not channel_id and not channel_username:
            channel_username = "@ConnectedData"
        
        monitoring_status.update({
            'enabled': True,
            'channel_id': channel_id,
            'channel_username': channel_username,
            'check_interval_minutes': check_interval_minutes,
            'last_check': None,
            'processed_count': 0,
            'failed_count': 0
        })
        
        # Start background monitoring (non-blocking)
        from youtube_monitor import YouTubeChannelMonitor
        import threading
        
        def run_monitor():
            try:
                monitor = YouTubeChannelMonitor(
                    channel_id=channel_id,
                    channel_username=channel_username
                )
                monitor.run_continuous(
                    check_interval_minutes=check_interval_minutes,
                    lookback_hours=24
                )
            except Exception as e:
                print(f"❌ Monitoring error: {e}")
                monitoring_status['enabled'] = False
        
        monitor_thread = threading.Thread(target=run_monitor, daemon=True)
        monitor_thread.start()
        
        return {
            "status": "started",
            "message": "YouTube monitoring started",
            "monitoring_status": monitoring_status
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/youtube/monitor/stop")
async def stop_monitoring():
    """Stop automatic YouTube channel monitoring"""
    global monitoring_status
    
    monitoring_status['enabled'] = False
    
    return {
        "status": "stopped",
        "message": "YouTube monitoring stopped",
        "monitoring_status": monitoring_status
    }


@app.get("/api/youtube/monitor/status")
async def get_monitoring_status():
    """Get current monitoring status"""
    return {
        "monitoring_status": monitoring_status,
        "timestamp": datetime.now().isoformat()
    }


@app.post("/api/youtube/monitor/check")
async def check_now():
    """
    Manually trigger a check for new videos (one-time)
    
    Returns:
        Results of the check
    """
    try:
        from youtube_monitor import YouTubeChannelMonitor
        
        # Use current monitoring settings or defaults
        monitor = YouTubeChannelMonitor(
            channel_id=monitoring_status.get('channel_id'),
            channel_username=monitoring_status.get('channel_username') or "@ConnectedData"
        )
        
        # Check for new videos
        new_videos = monitor.check_for_new_videos(lookback_hours=24)
        
        if new_videos:
            # Process new videos
            results = monitor.process_new_videos(new_videos)
            
            successful = sum(results.values())
            failed = len(results) - successful
            
            monitoring_status['processed_count'] += successful
            monitoring_status['failed_count'] += failed
            monitoring_status['last_check'] = datetime.now().isoformat()
            
            return {
                "status": "completed",
                "new_videos_found": len(new_videos),
                "successful": successful,
                "failed": failed,
                "videos": [
                    {
                        "video_id": v['video_id'],
                        "title": v['title'],
                        "url": v['url'],
                        "status": "success" if results.get(v['video_id']) else "failed"
                    }
                    for v in new_videos
                ],
                "timestamp": datetime.now().isoformat()
            }
        else:
            monitoring_status['last_check'] = datetime.now().isoformat()
            return {
                "status": "completed",
                "new_videos_found": 0,
                "message": "No new videos found",
                "timestamp": datetime.now().isoformat()
            }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    uvicorn.run(
        "backend_api_youtube:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
