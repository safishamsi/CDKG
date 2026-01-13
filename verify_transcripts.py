"""Verify transcripts loaded in Neo4j"""

from neo4j import GraphDatabase
import os
import json
from pathlib import Path

# Load env manually
env_file = Path(__file__).parent / ".env"
if env_file.exists():
    with open(env_file, 'r') as f:
        for line in f:
            if line.strip() and not line.startswith('#'):
                if '=' in line:
                    key, value = line.strip().split('=', 1)
                    os.environ[key] = value

uri = os.getenv('NEO4J_URI', 'bolt://127.0.0.1:7687')
user = os.getenv('NEO4J_USER', 'neo4j')
password = os.getenv('NEO4J_PASSWORD', '12345678')

driver = GraphDatabase.driver(uri, auth=(user, password))

with driver.session() as session:
    # Check transcripts loaded
    result = session.run("""
        MATCH (t:Talk)
        WHERE t.transcript IS NOT NULL
        RETURN t.title as title,
               t.transcript_length as length,
               t.transcript_segment_count as segments
        ORDER BY t.title
        LIMIT 10
    """)
    
    print("=" * 70)
    print("Transcripts Loaded in Neo4j")
    print("=" * 70)
    print()
    
    for record in result:
        title = record['title']
        length = record['length']
        segments = record['segments']
        print(f"📝 {title[:60]}...")
        print(f"   Length: {length:,} characters")
        print(f"   Segments: {segments} (with timestamps)")
        print()
    
    # Total count
    result = session.run("""
        MATCH (t:Talk)
        WHERE t.transcript IS NOT NULL
        RETURN count(t) as count,
               sum(t.transcript_length) as total_chars,
               sum(t.transcript_segment_count) as total_segments
    """)
    
    stats = result.single()
    print("=" * 70)
    print("Summary:")
    print(f"   Talks with transcripts: {stats['count']}")
    print(f"   Total characters: {stats['total_chars']:,}")
    print(f"   Total segments (with timestamps): {stats['total_segments']:,}")
    print("=" * 70)
    print()
    
    # Get one example with timestamp segments
    result = session.run("""
        MATCH (t:Talk)
        WHERE t.transcript_segments IS NOT NULL
        RETURN t.title as title,
               t.transcript_segments as segments_json
        LIMIT 1
    """)
    
    record = result.single()
    if record:
        print("Example Transcript with Timestamps:")
        print("=" * 70)
        print(f"Talk: {record['title']}")
        print()
        
        segments = json.loads(record['segments_json'])
        print(f"Total segments: {len(segments)}")
        print()
        print("First 5 segments with timestamps:")
        print("-" * 70)
        
        for seg in segments[:5]:
            print(f"  [{seg['start']} → {seg['end']}] ({seg['duration_seconds']:.1f}s)")
            print(f"    {seg['text'][:80]}...")
            print()

driver.close()

