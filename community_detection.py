"""
Community Detection using Leiden Algorithm

This module:
1. Extracts graph data from Neo4j
2. Runs Leiden algorithm for community detection
3. Stores community assignments back in Neo4j
4. Provides query interface for community information
"""

import networkx as nx
from typing import Dict, List, Optional
from neo4j import GraphDatabase
from config import config
from tqdm import tqdm


class CommunityDetector:
    """Detect communities in Neo4j graph using Leiden algorithm"""
    
    def __init__(self, neo4j_driver=None):
        """
        Initialize community detector
        
        Args:
            neo4j_driver: Optional Neo4j driver (creates new if None)
        """
        if neo4j_driver:
            self.driver = neo4j_driver
        else:
            self.driver = GraphDatabase.driver(
                config.neo4j.uri,
                auth=(config.neo4j.user, config.neo4j.password)
            )
    
    def extract_graph(self, limit: Optional[int] = None) -> nx.Graph:
        """
        Extract graph from Neo4j into NetworkX format
        
        Args:
            limit: Optional limit on number of relationships to extract
            
        Returns:
            NetworkX graph
        """
        print("📊 Extracting graph from Neo4j...")
        G = nx.Graph()
        
        with self.driver.session() as session:
            # Get all relationships
            if limit:
                query = """
                MATCH (n)-[r]->(m)
                RETURN n, labels(n)[0] as n_type, r, m, labels(m)[0] as m_type
                LIMIT $limit
                """
                result = session.run(query, limit=limit)
            else:
                query = """
                MATCH (n)-[r]->(m)
                RETURN n, labels(n)[0] as n_type, r, m, labels(m)[0] as m_type
                """
                result = session.run(query)
            
            nodes_added = set()
            
            for record in tqdm(result, desc="Building graph"):
                # Source node
                n = record['n']
                n_type = record['n_type']
                n_id = n.get('name') or n.get('title') or n.get('keyword') or str(n.id)
                n_name = n.get('name') or n.get('title') or n.get('keyword') or 'Unknown'
                
                if n_id not in nodes_added:
                    G.add_node(n_id, 
                              name=n_name,
                              type=n_type,
                              neo4j_id=n.id)
                    nodes_added.add(n_id)
                
                # Target node
                m = record['m']
                m_type = record.get('m_type', 'Unknown')
                m_id = m.get('name') or m.get('title') or m.get('keyword') or str(m.id)
                m_name = m.get('name') or m.get('title') or m.get('keyword') or 'Unknown'
                
                if m_id not in nodes_added:
                    G.add_node(m_id,
                              name=m_name,
                              type=m_type,
                              neo4j_id=m.id)
                    nodes_added.add(m_id)
                
                # Edge
                rel = record['r']
                rel_type = rel.type if rel else 'RELATED_TO'
                
                if not G.has_edge(n_id, m_id):
                    G.add_edge(n_id, m_id, type=rel_type)
        
        print(f"   ✅ Extracted graph: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")
        return G
    
    def detect_communities(self, G: nx.Graph, resolution: float = 1.0) -> Dict[str, int]:
        """
        Detect communities using Leiden algorithm
        
        Args:
            G: NetworkX graph
            resolution: Resolution parameter (higher = more communities)
            
        Returns:
            Dictionary mapping node_id -> community_id
        """
        try:
            import leidenalg
            import igraph as ig
        except ImportError:
            print("⚠️  leidenalg or igraph not installed. Installing...")
            print("   Run: pip install leidenalg python-igraph")
            raise ImportError("leidenalg and python-igraph required for community detection")
        
        print(f"🔍 Detecting communities with Leiden algorithm (resolution={resolution})...")
        
        # Convert NetworkX to igraph
        # Create mapping from NetworkX node IDs to igraph indices
        node_list = list(G.nodes())
        node_to_idx = {node: idx for idx, node in enumerate(node_list)}
        
        # Create igraph graph
        edges = [(node_to_idx[u], node_to_idx[v]) for u, v in G.edges()]
        g_ig = ig.Graph(edges, directed=False)
        
        # Add node attributes
        for attr in ['name', 'type']:
            if attr in G.nodes[node_list[0]]:
                g_ig.vs[attr] = [G.nodes[node][attr] for node in node_list]
        
        # Run Leiden algorithm
        # Use CPMVertexPartition which supports resolution_parameter
        # (ModularityVertexPartition doesn't support resolution_parameter in this version)
        partition = leidenalg.find_partition(
            g_ig,
            leidenalg.CPMVertexPartition,
            resolution_parameter=resolution
        )
        
        # Map back to node IDs
        communities = {}
        for idx, community_id in enumerate(partition.membership):
            node_id = node_list[idx]
            communities[node_id] = community_id
        
        num_communities = len(set(communities.values()))
        print(f"   ✅ Detected {num_communities} communities")
        
        return communities
    
    def store_communities(self, communities: Dict[str, int], community_metadata: Optional[Dict[int, Dict]] = None):
        """
        Store community assignments back in Neo4j
        
        Args:
            communities: Dictionary mapping node_id -> community_id
            community_metadata: Optional metadata for each community (size, topics, etc.)
        """
        print("💾 Storing community assignments in Neo4j...")
        
        with self.driver.session() as session:
            # First, remove old community property
            session.run("""
                MATCH (n)
                WHERE n.community_id IS NOT NULL
                REMOVE n.community_id
            """)
            
            # Store new community assignments
            for node_id, community_id in tqdm(communities.items(), desc="Storing communities"):
                # Try to find node by name, title, or keyword
                session.run("""
                    MATCH (n)
                    WHERE (n.name = $node_id OR n.title = $node_id OR n.keyword = $node_id)
                    SET n.community_id = $community_id
                """, node_id=node_id, community_id=community_id)
            
            # Create Community nodes and relationships
            # First, remove old Community nodes
            session.run("MATCH (c:Community) DETACH DELETE c")
            
            # Get unique communities
            unique_communities = set(communities.values())
            
            # Create Community nodes with metadata
            for comm_id in unique_communities:
                metadata = community_metadata.get(comm_id, {}) if community_metadata else {}
                size = metadata.get('size', sum(1 for v in communities.values() if v == comm_id))
                topics = metadata.get('topics', [])
                
                session.run("""
                    MERGE (c:Community {id: $comm_id})
                    SET c.size = $size,
                        c.topics = $topics
                """, comm_id=comm_id, size=size, topics=topics)
            
            # Create BELONGS_TO relationships
            for node_id, community_id in tqdm(communities.items(), desc="Creating relationships"):
                session.run("""
                    MATCH (n)
                    WHERE (n.name = $node_id OR n.title = $node_id OR n.keyword = $node_id)
                    MATCH (c:Community {id: $community_id})
                    MERGE (n)-[:BELONGS_TO]->(c)
                """, node_id=node_id, community_id=community_id)
        
        print("   ✅ Community assignments stored")
    
    def get_community_info(self, community_id: Optional[int] = None) -> List[Dict]:
        """
        Get information about communities
        
        Args:
            community_id: Optional specific community ID
            
        Returns:
            List of community information dictionaries
        """
        with self.driver.session() as session:
            if community_id is not None:
                query = """
                MATCH (c:Community {id: $comm_id})
                OPTIONAL MATCH (n)-[:BELONGS_TO]->(c)
                WITH c, collect(DISTINCT n) as members
                RETURN c.id as id,
                       c.size as size,
                       c.topics as topics,
                       [m IN members | 
                        CASE 
                          WHEN 'Speaker' IN labels(m) THEN m.name
                          WHEN 'Talk' IN labels(m) THEN m.title
                          WHEN 'Tag' IN labels(m) THEN m.keyword
                          ELSE null
                        END
                       ][0..20] as member_names,
                       size(members) as actual_size
                """
                result = session.run(query, comm_id=community_id)
            else:
                query = """
                MATCH (c:Community)
                OPTIONAL MATCH (n)-[:BELONGS_TO]->(c)
                WITH c, collect(DISTINCT n) as members
                RETURN c.id as id,
                       c.size as size,
                       c.topics as topics,
                       [m IN members | 
                        CASE 
                          WHEN 'Speaker' IN labels(m) THEN m.name
                          WHEN 'Talk' IN labels(m) THEN m.title
                          WHEN 'Tag' IN labels(m) THEN m.keyword
                          ELSE null
                        END
                       ][0..20] as member_names,
                       size(members) as actual_size
                ORDER BY actual_size DESC
                """
                result = session.run(query)
            
            communities = []
            for record in result:
                communities.append({
                    'id': record['id'],
                    'size': record['actual_size'] or record['size'],
                    'topics': record['topics'] or [],
                    'members': [m for m in record['member_names'] if m][:20]
                })
            
            return communities
    
    def get_node_community(self, node_id: str) -> Optional[Dict]:
        """
        Get community information for a specific node
        
        Args:
            node_id: Node identifier (name, title, or keyword)
            
        Returns:
            Community information or None
        """
        with self.driver.session() as session:
            query = """
            MATCH (n)-[:BELONGS_TO]->(c:Community)
            WHERE (n.name = $node_id OR n.title = $node_id OR n.keyword = $node_id)
            OPTIONAL MATCH (other)-[:BELONGS_TO]->(c)
            WITH c, collect(DISTINCT other) as members
            RETURN c.id as id,
                   c.size as size,
                   c.topics as topics,
                   [m IN members | 
                    CASE 
                      WHEN 'Speaker' IN labels(m) THEN m.name
                      WHEN 'Talk' IN labels(m) THEN m.title
                      WHEN 'Tag' IN labels(m) THEN m.keyword
                      ELSE null
                    END
                   ][0..20] as member_names,
                   size(members) as actual_size
            LIMIT 1
            """
            result = session.run(query, node_id=node_id)
            record = result.single()
            
            if record:
                return {
                    'id': record['id'],
                    'size': record['actual_size'] or record['size'],
                    'topics': record['topics'] or [],
                    'members': [m for m in record['member_names'] if m][:20]
                }
            return None
    
    def run_detection(self, limit: Optional[int] = None, resolution: float = 1.0, store: bool = True):
        """
        Run complete community detection pipeline
        
        Args:
            limit: Optional limit on relationships to extract
            resolution: Resolution parameter for Leiden algorithm
            store: Whether to store results in Neo4j
            
        Returns:
            Dictionary mapping node_id -> community_id
        """
        # Extract graph
        G = self.extract_graph(limit=limit)
        
        # Detect communities
        communities = self.detect_communities(G, resolution=resolution)
        
        # Calculate community metadata
        community_metadata = {}
        for comm_id in set(communities.values()):
            comm_nodes = [node_id for node_id, cid in communities.items() if cid == comm_id]
            community_metadata[comm_id] = {
                'size': len(comm_nodes)
            }
        
        # Store in Neo4j
        if store:
            self.store_communities(communities, community_metadata)
        
        return communities
    
    def close(self):
        """Close Neo4j driver"""
        if self.driver:
            self.driver.close()


def main():
    """Run community detection"""
    detector = CommunityDetector()
    
    try:
        # Run detection (limit to 5000 relationships for faster processing)
        # Use lower resolution (0.1-0.5) for CPMVertexPartition to get meaningful communities
        communities = detector.run_detection(limit=5000, resolution=0.1, store=True)
        
        print(f"\n✅ Community detection complete!")
        print(f"   Found {len(set(communities.values()))} communities")
        
        # Show community info
        print("\n📊 Community Information:")
        comm_info = detector.get_community_info()
        for comm in comm_info[:10]:  # Show top 10
            print(f"\n   Community {comm['id']}: {comm['size']} members")
            if comm['members']:
                print(f"      Sample members: {', '.join(comm['members'][:5])}")
    
    finally:
        detector.close()


if __name__ == "__main__":
    main()

