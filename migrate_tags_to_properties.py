"""
Migration Script: Convert Tag nodes to Talk properties

This script migrates the existing graph structure where Tag is a node
to the new structure where tags are stored as an array property on Talk nodes.

Usage:
    python migrate_tags_to_properties.py
"""

import os
from dotenv import load_dotenv
from neo4j import GraphDatabase

load_dotenv()

def migrate_tags():
    """Convert Tag nodes to Talk.tags property"""
    
    # Connect to Neo4j
    uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    user = os.getenv("NEO4J_USER", "neo4j")
    password = os.getenv("NEO4J_PASSWORD", "")
    
    if not password:
        print("❌ NEO4J_PASSWORD not set in .env file")
        return
    
    driver = GraphDatabase.driver(uri, auth=(user, password))
    
    try:
        with driver.session() as session:
            print("🔄 Starting migration: Tag nodes → Talk.tags property")
            print("=" * 70)
            
            # Step 1: Get all Talk-Tag relationships
            print("\n📊 Step 1: Finding all Talk-Tag relationships...")
            result = session.run("""
                MATCH (t:Talk)-[:IS_DESCRIBED_BY]->(tag:Tag)
                RETURN t.title as talk_title, collect(tag.keyword) as tags
            """)
            
            talks_with_tags = {}
            for record in result:
                talk_title = record['talk_title']
                tags = record['tags']
                if tags:
                    talks_with_tags[talk_title] = tags
            
            print(f"   ✅ Found {len(talks_with_tags)} talks with tags")
            
            # Step 2: Update Talk nodes with tags property
            print("\n💾 Step 2: Updating Talk nodes with tags property...")
            updated_count = 0
            for talk_title, tags in talks_with_tags.items():
                session.run("""
                    MATCH (t:Talk {title: $title})
                    SET t.tags = $tags
                """, title=talk_title, tags=tags)
                updated_count += 1
                if updated_count % 10 == 0:
                    print(f"   ⏳ Updated {updated_count} talks...")
            
            print(f"   ✅ Updated {updated_count} Talk nodes with tags property")
            
            # Step 3: Delete IS_DESCRIBED_BY relationships
            print("\n🗑️  Step 3: Deleting IS_DESCRIBED_BY relationships...")
            result = session.run("""
                MATCH ()-[r:IS_DESCRIBED_BY]->(:Tag)
                DELETE r
                RETURN count(r) as deleted_count
            """)
            deleted = result.single()['deleted_count']
            print(f"   ✅ Deleted {deleted} IS_DESCRIBED_BY relationships")
            
            # Step 4: Delete Tag nodes (optional - comment out if you want to keep them)
            print("\n🗑️  Step 4: Deleting Tag nodes...")
            result = session.run("""
                MATCH (tag:Tag)
                DELETE tag
                RETURN count(tag) as deleted_count
            """)
            deleted = result.single()['deleted_count']
            print(f"   ✅ Deleted {deleted} Tag nodes")
            
            # Step 5: Verify migration
            print("\n✅ Step 5: Verifying migration...")
            result = session.run("""
                MATCH (t:Talk)
                WHERE t.tags IS NOT NULL
                RETURN count(t) as talks_with_tags
            """)
            talks_with_tags_count = result.single()['talks_with_tags']
            print(f"   ✅ {talks_with_tags_count} talks now have tags property")
            
            # Check if any Tag nodes remain
            result = session.run("""
                MATCH (tag:Tag)
                RETURN count(tag) as remaining_tags
            """)
            remaining = result.single()['remaining_tags']
            if remaining == 0:
                print(f"   ✅ No Tag nodes remaining")
            else:
                print(f"   ⚠️  {remaining} Tag nodes still exist")
            
            print("\n" + "=" * 70)
            print("✅ Migration complete!")
            print("=" * 70)
            print("\n📝 Summary:")
            print(f"   • Updated {updated_count} Talk nodes with tags property")
            print(f"   • Deleted {deleted} Tag nodes")
            print(f"   • Tags are now stored as Talk.tags array property")
            print("\n⚠️  Note: This migration is irreversible. Make sure you have a backup!")
            
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        raise
    finally:
        driver.close()


if __name__ == "__main__":
    print("🚀 Tag Migration Script")
    print("=" * 70)
    print("This script converts Tag nodes to Talk.tags property")
    print("=" * 70)
    
    response = input("\n⚠️  This will delete all Tag nodes. Continue? (yes/no): ")
    if response.lower() == 'yes':
        migrate_tags()
    else:
        print("❌ Migration cancelled")

