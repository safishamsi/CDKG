"""
Data Quality Verification Script

This script verifies:
1. Organization nodes exist and have relationships
2. All node types have proper names
3. Transcript content is stored
4. Entity extraction quality
"""

from neo4j import GraphDatabase
from config import config
from typing import Dict, List


def verify_data_quality():
    """Run comprehensive data quality checks"""
    print("🔍 Data Quality Verification\n")
    print("=" * 70)
    
    # Connect to Neo4j
    driver = GraphDatabase.driver(
        config.neo4j.uri,
        auth=(config.neo4j.user, config.neo4j.password)
    )
    
    try:
        driver.verify_connectivity()
        print("✅ Connected to Neo4j\n")
        
        with driver.session() as session:
            # 1. Check Organization nodes
            print("1️⃣  Organization Nodes")
            print("-" * 70)
            org_result = session.run("""
                MATCH (o:Organization)
                OPTIONAL MATCH (o)<-[:MENTIONS]-(t:Talk)
                RETURN o.name as name,
                       count(DISTINCT t) as talk_count,
                       collect(DISTINCT t.title)[0..3] as sample_talks
                ORDER BY talk_count DESC
                LIMIT 10
            """)
            
            orgs = list(org_result)
            if orgs:
                print(f"   ✅ Found {len(orgs)} Organization nodes (showing top 10):")
                for record in orgs:
                    name = record['name'] or 'Unknown'
                    count = record['talk_count']
                    talks = record['sample_talks']
                    print(f"      • {name}: mentioned in {count} talk(s)")
                    if talks:
                        print(f"        Sample talks: {', '.join(talks[:2])}")
            else:
                print("   ⚠️  No Organization nodes found")
                print("      This may indicate NER extraction is not working or no organizations were detected")
            print()
            
            # 2. Check all node types
            print("2️⃣  Node Type Statistics")
            print("-" * 70)
            node_types = ['Speaker', 'Talk', 'Event', 'Category', 'Organization', 
                         'Product', 'Concept', 'Community', 'Tag']
            
            for node_type in node_types:
                result = session.run(f"""
                    MATCH (n:{node_type})
                    RETURN count(n) as count,
                           count(CASE WHEN n.name IS NOT NULL OR n.title IS NOT NULL OR n.keyword IS NOT NULL THEN 1 END) as with_name
                """)
                record = result.single()
                if record:
                    count = record['count']
                    with_name = record['with_name']
                    percentage = (with_name / count * 100) if count > 0 else 0
                    status = "✅" if percentage >= 90 else "⚠️"
                    print(f"   {status} {node_type}: {count} nodes, {with_name} with names ({percentage:.1f}%)")
            print()
            
            # 3. Check transcripts
            print("3️⃣  Transcript Content")
            print("-" * 70)
            transcript_result = session.run("""
                MATCH (t:Talk)
                RETURN count(t) as total_talks,
                       count(t.transcript) as talks_with_transcript,
                       count(t.transcript_segments) as talks_with_segments,
                       avg(size(t.transcript)) as avg_transcript_length
            """)
            record = transcript_result.single()
            if record:
                total = record['total_talks']
                with_transcript = record['talks_with_transcript']
                with_segments = record['talks_with_segments']
                avg_length = record['avg_transcript_length'] or 0
                percentage = (with_transcript / total * 100) if total > 0 else 0
                status = "✅" if percentage > 0 else "⚠️"
                print(f"   {status} Total talks: {total}")
                print(f"      Talks with transcript: {with_transcript} ({percentage:.1f}%)")
                print(f"      Talks with segments: {with_segments}")
                print(f"      Average transcript length: {avg_length:.0f} characters")
            print()
            
            # 4. Check relationships
            print("4️⃣  Relationship Quality")
            print("-" * 70)
            rel_result = session.run("""
                MATCH ()-[r]->()
                RETURN type(r) as rel_type,
                       count(r) as count
                ORDER BY count DESC
                LIMIT 10
            """)
            
            rels = list(rel_result)
            if rels:
                print("   Top relationships:")
                for record in rels:
                    print(f"      • {record['rel_type']}: {record['count']} relationships")
            print()
            
            # 5. Check for nodes with "Unknown" names
            print("5️⃣  Nodes with Missing Names")
            print("-" * 70)
            unknown_result = session.run("""
                MATCH (n)
                WHERE (n.name IS NULL OR n.name = 'Unknown')
                  AND (n.title IS NULL OR n.title = 'Unknown')
                  AND (n.keyword IS NULL OR n.keyword = 'Unknown')
                RETURN labels(n)[0] as node_type,
                       count(n) as count
                ORDER BY count DESC
            """)
            
            unknowns = list(unknown_result)
            if unknowns:
                total_unknown = sum(r['count'] for r in unknowns)
                if total_unknown > 0:
                    print(f"   ⚠️  Found {total_unknown} nodes with missing names:")
                    for record in unknowns:
                        print(f"      • {record['node_type']}: {record['count']} nodes")
                else:
                    print("   ✅ No nodes with missing names")
            else:
                print("   ✅ No nodes with missing names")
            print()
            
            # 6. Check Organization visibility in graph
            print("6️⃣  Organization Visibility in Graph")
            print("-" * 70)
            org_visibility = session.run("""
                MATCH (o:Organization)<-[:MENTIONS]-(t:Talk)
                OPTIONAL MATCH (t)-[:GIVES_TALK]-(s:Speaker)
                RETURN o.name as org_name,
                       count(DISTINCT t) as talk_count,
                       collect(DISTINCT s.name)[0..3] as speakers
                ORDER BY talk_count DESC
                LIMIT 5
            """)
            
            orgs_visible = list(org_visibility)
            if orgs_visible:
                print("   Organizations that should be visible in graph:")
                for record in orgs_visible:
                    org_name = record['org_name'] or 'Unknown'
                    count = record['talk_count']
                    speakers = record['speakers']
                    print(f"      • {org_name}: connected to {count} talk(s)")
                    if speakers:
                        print(f"        Via speakers: {', '.join(speakers[:2])}")
            else:
                print("   ⚠️  No Organization nodes with relationships found")
                print("      They may not appear in graph visualization")
            print()
            
            print("=" * 70)
            print("✅ Data quality verification complete!")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        driver.close()


if __name__ == "__main__":
    verify_data_quality()

