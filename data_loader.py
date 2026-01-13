"""
Step 1: Data Loader - Load CSV data into Neo4j Desktop

This module handles:
- Connecting to Neo4j Desktop
- Loading nodes (Speaker, Talk, Tag, Event, Category)
- Creating relationships (GIVES_TALK, IS_PART_OF, IS_CATEGORIZED_AS, IS_DESCRIBED_BY)
- Batch processing for performance
"""

import time
from pathlib import Path
from typing import List, Dict, Any
import pandas as pd
from neo4j import GraphDatabase
from tqdm import tqdm

from config import config


def safe_str(value: Any) -> str:
    """Safely convert value to string, handling None/null/nan"""
    if value is None:
        return ""
    s = str(value).strip()
    if s.lower() in ["none", "null", "nan", ""]:
        return ""
    return s


class DataLoader:
    """Loads data from CSV files into Neo4j"""
    
    def __init__(self):
        """Initialize connection to Neo4j"""
        self.config = config.neo4j
        self.cdl_db_path = config.paths.cdl_db_path
        self.driver = None
        
    def connect(self):
        """Connect to Neo4j Desktop"""
        print("\n🔌 Connecting to Neo4j Desktop...")
        print(f"   URI: {self.config.uri}")
        print(f"   User: {self.config.user}")
        
        try:
            self.driver = GraphDatabase.driver(
                self.config.uri,
                auth=(self.config.user, self.config.password)
            )
            self.driver.verify_connectivity()
            
            # Test query
            with self.driver.session() as session:
                result = session.run("RETURN 1 as test")
                if result.single()['test'] == 1:
                    print("   ✅ Connected successfully!\n")
                    return True
            
            return False
            
        except Exception as e:
            print(f"   ❌ Connection failed: {e}\n")
            print("📋 Troubleshooting:")
            print("   1. Is Neo4j Desktop running?")
            print("   2. Is your database started?")
            print("   3. Check password in .env file")
            print("   4. Check connection details in Neo4j Desktop")
            raise
    
    def close(self):
        """Close Neo4j connection"""
        if self.driver:
            self.driver.close()
    
    def create_constraints(self):
        """Create unique constraints for all node types"""
        print("🔧 Creating constraints...")
        
        constraints = [
            "CREATE CONSTRAINT speaker_name IF NOT EXISTS FOR (s:Speaker) REQUIRE s.name IS UNIQUE",
            "CREATE CONSTRAINT talk_title IF NOT EXISTS FOR (t:Talk) REQUIRE t.title IS UNIQUE",
            "CREATE CONSTRAINT event_name IF NOT EXISTS FOR (e:Event) REQUIRE e.name IS UNIQUE",
            "CREATE CONSTRAINT category_name IF NOT EXISTS FOR (c:Category) REQUIRE c.name IS UNIQUE",
            "CREATE CONSTRAINT tag_keyword IF NOT EXISTS FOR (tag:Tag) REQUIRE tag.keyword IS UNIQUE",
        ]
        
        with self.driver.session() as session:
            for query in constraints:
                try:
                    session.run(query).consume()
                except Exception:
                    pass  # Constraint may already exist
        
        print("   ✅ Constraints ready\n")
    
    def load_speakers(self, batch_size: int = 100) -> int:
        """Load speakers from CSV"""
        csv_path = self.cdl_db_path / "Speaker.csv"
        if not csv_path.exists():
            print(f"   ⚠️  {csv_path.name} not found")
            return 0
        
        print(f"📊 Loading Speakers...")
        
        df = pd.read_csv(csv_path)
        
        # Extract unique speakers
        speakers_set = set()
        for _, row in df.iterrows():
            name = safe_str(row.get("a.name"))
            if name:
                speakers_set.add(name)
        
        speakers = [{"name": name} for name in sorted(speakers_set)]
        
        # Batch load
        query = "UNWIND $batch AS s MERGE (:Speaker {name: s.name})"
        total = 0
        
        with self.driver.session() as session:
            for i in tqdm(range(0, len(speakers), batch_size), desc="   Speakers"):
                batch = speakers[i:i+batch_size]
                session.run(query, batch=batch).consume()
                total += len(batch)
        
        print(f"   ✅ Loaded {total} speakers\n")
        return total
    
    def load_talks(self, batch_size: int = 100) -> int:
        """Load talks from CSV"""
        csv_path = self.cdl_db_path / "Talk.csv"
        if not csv_path.exists():
            print(f"   ⚠️  {csv_path.name} not found")
            return 0
        
        print(f"📊 Loading Talks...")
        
        df = pd.read_csv(csv_path)
        
        # Extract talks
        talks = []
        for _, row in df.iterrows():
            title = safe_str(row.get("a.title"))
            if title:
                talks.append({
                    "title": title,
                    "category": safe_str(row.get("a.category")),
                    "url": safe_str(row.get("a.url")),
                    "description": safe_str(row.get("a.description")),
                    "type": safe_str(row.get("a.type"))
                })
        
        # Batch load
        query = """
        UNWIND $batch AS t
        MERGE (talk:Talk {title: t.title})
        SET talk.category = t.category,
            talk.url = t.url,
            talk.description = t.description,
            talk.type = t.type
        """
        total = 0
        
        with self.driver.session() as session:
            for i in tqdm(range(0, len(talks), batch_size), desc="   Talks"):
                batch = talks[i:i+batch_size]
                session.run(query, batch=batch).consume()
                total += len(batch)
        
        print(f"   ✅ Loaded {total} talks\n")
        return total
    
    def load_tags(self, batch_size: int = 200) -> int:
        """Load tags from CSV"""
        csv_path = self.cdl_db_path / "Tag.csv"
        if not csv_path.exists():
            print(f"   ⚠️  {csv_path.name} not found")
            return 0
        
        print(f"📊 Loading Tags...")
        
        df = pd.read_csv(csv_path)
        
        # Extract unique tags
        tags_set = set()
        for _, row in df.iterrows():
            keyword = safe_str(row.get("a.keyword"))
            if keyword:
                tags_set.add(keyword)
        
        tags = [{"keyword": kw} for kw in sorted(tags_set)]
        
        # Batch load
        query = "UNWIND $batch AS t MERGE (:Tag {keyword: t.keyword})"
        total = 0
        
        with self.driver.session() as session:
            for i in tqdm(range(0, len(tags), batch_size), desc="   Tags"):
                batch = tags[i:i+batch_size]
                session.run(query, batch=batch).consume()
                total += len(batch)
        
        print(f"   ✅ Loaded {total} tags\n")
        return total
    
    def load_events(self) -> int:
        """Load events from CSV"""
        csv_path = self.cdl_db_path / "Event.csv"
        if not csv_path.exists():
            print(f"   ⚠️  {csv_path.name} not found")
            return 0
        
        print(f"📊 Loading Events...")
        
        df = pd.read_csv(csv_path)
        
        events = []
        for _, row in df.iterrows():
            name = safe_str(row.get("a.name"))
            if name:
                events.append({
                    "name": name,
                    "description": safe_str(row.get("a.description"))
                })
        
        query = """
        UNWIND $batch AS e
        MERGE (event:Event {name: e.name})
        SET event.description = e.description
        """
        
        with self.driver.session() as session:
            session.run(query, batch=events).consume()
        
        print(f"   ✅ Loaded {len(events)} events\n")
        return len(events)
    
    def load_categories(self) -> int:
        """Load categories from CSV"""
        csv_path = self.cdl_db_path / "Category.csv"
        if not csv_path.exists():
            print(f"   ⚠️  {csv_path.name} not found")
            return 0
        
        print(f"📊 Loading Categories...")
        
        df = pd.read_csv(csv_path)
        
        cats_set = set()
        for _, row in df.iterrows():
            name = safe_str(row.get("a.name"))
            if name:
                cats_set.add(name)
        
        categories = [{"name": name} for name in sorted(cats_set)]
        
        query = "UNWIND $batch AS c MERGE (:Category {name: c.name})"
        
        with self.driver.session() as session:
            session.run(query, batch=categories).consume()
        
        print(f"   ✅ Loaded {len(categories)} categories\n")
        return len(categories)
    
    def load_relationships(self, rel_type: str, csv_file: str, batch_size: int = 200) -> int:
        """Load relationships generically"""
        csv_path = self.cdl_db_path / csv_file
        if not csv_path.exists():
            print(f"   ⚠️  {csv_file} not found")
            return 0
        
        print(f"🔗 Loading {rel_type}...")
        
        df = pd.read_csv(csv_path)
        relationships = []
        
        # Extract based on relationship type
        if rel_type == "GIVES_TALK":
            for _, row in df.iterrows():
                speaker = safe_str(row.get("a.name"))
                talk = safe_str(row.get("b.title"))
                date = safe_str(row.get("r.date"))
                if speaker and talk:
                    relationships.append({"from": speaker, "to": talk, "date": date})
            
            query = """
            UNWIND $batch AS r
            MATCH (s:Speaker {name: r.from})
            MATCH (t:Talk {title: r.to})
            MERGE (s)-[rel:GIVES_TALK]->(t)
            SET rel.date = r.date
            """
        
        elif rel_type == "IS_PART_OF":
            for _, row in df.iterrows():
                talk = safe_str(row.get("a.title"))
                event = safe_str(row.get("b.name"))
                if talk and event:
                    relationships.append({"from": talk, "to": event})
            
            query = """
            UNWIND $batch AS r
            MATCH (t:Talk {title: r.from})
            MATCH (e:Event {name: r.to})
            MERGE (t)-[:IS_PART_OF]->(e)
            """
        
        elif rel_type == "IS_CATEGORIZED_AS":
            for _, row in df.iterrows():
                talk = safe_str(row.get("a.title"))
                category = safe_str(row.get("b.name"))
                if talk and category:
                    relationships.append({"from": talk, "to": category})
            
            query = """
            UNWIND $batch AS r
            MATCH (t:Talk {title: r.from})
            MATCH (c:Category {name: r.to})
            MERGE (t)-[:IS_CATEGORIZED_AS]->(c)
            """
        
        elif rel_type == "IS_DESCRIBED_BY":
            for _, row in df.iterrows():
                talk = safe_str(row.get("a.title"))
                tag = safe_str(row.get("b.keyword"))
                if talk and tag:
                    relationships.append({"from": talk, "to": tag})
            
            query = """
            UNWIND $batch AS r
            MATCH (t:Talk {title: r.from})
            MATCH (tag:Tag {keyword: r.to})
            MERGE (t)-[:IS_DESCRIBED_BY]->(tag)
            """
        
        else:
            print(f"   ⚠️  Unknown relationship type: {rel_type}")
            return 0
        
        # Batch load
        total = 0
        with self.driver.session() as session:
            for i in tqdm(range(0, len(relationships), batch_size), desc=f"   {rel_type}"):
                batch = relationships[i:i+batch_size]
                session.run(query, batch=batch).consume()
                total += len(batch)
        
        print(f"   ✅ Loaded {total} relationships\n")
        return total
    
    def get_statistics(self) -> Dict[str, int]:
        """Get database statistics"""
        stats = {}
        
        with self.driver.session() as session:
            # Node counts
            for label in ["Speaker", "Talk", "Tag", "Event", "Category"]:
                result = session.run(f"MATCH (n:{label}) RETURN count(n) as count")
                stats[label] = result.single()['count']
            
            # Relationship count
            result = session.run("MATCH ()-[r]->() RETURN count(r) as count")
            stats['Relationships'] = result.single()['count']
        
        return stats
    
    def print_statistics(self):
        """Print database statistics"""
        print("\n📈 Database Statistics:")
        print("=" * 70)
        
        stats = self.get_statistics()
        
        for label, count in stats.items():
            print(f"   {label:15s}: {count:5d}")
        
        # Sample data
        print("\n📋 Sample Connections:")
        with self.driver.session() as session:
            result = session.run("""
                MATCH (s:Speaker)-[:GIVES_TALK]->(t:Talk)
                RETURN s.name as speaker, t.title as talk
                LIMIT 3
            """)
            for record in result:
                print(f"   • {record['speaker']} → {record['talk'][:60]}...")
    
    def load_all(self):
        """Load all data from CSV files"""
        print("=" * 70)
        print("🚀 LOADING DATA INTO NEO4J DESKTOP")
        print("=" * 70)
        
        start_time = time.time()
        
        # Connect
        self.connect()
        
        # Create constraints
        self.create_constraints()
        
        # Load nodes
        print("=" * 70)
        print("STEP 1: Loading Nodes")
        print("=" * 70 + "\n")
        
        self.load_speakers()
        self.load_talks()
        self.load_tags()
        self.load_events()
        self.load_categories()
        
        # Load relationships
        print("=" * 70)
        print("STEP 2: Loading Relationships")
        print("=" * 70 + "\n")
        
        self.load_relationships("GIVES_TALK", "GIVES_TALK_Speaker_Talk.csv")
        self.load_relationships("IS_PART_OF", "IS_PART_OF_Talk_Event.csv")
        self.load_relationships("IS_CATEGORIZED_AS", "IS_CATEGORIZED_AS_Talk_Category.csv")
        self.load_relationships("IS_DESCRIBED_BY", "IS_DESCRIBED_BY_Talk_Tag.csv")
        
        # Print statistics
        self.print_statistics()
        
        elapsed = time.time() - start_time
        print("\n" + "=" * 70)
        print(f"✅ DATA LOADING COMPLETE in {elapsed:.2f}s!")
        print("=" * 70 + "\n")


def main():
    """Main entry point"""
    loader = DataLoader()
    try:
        loader.load_all()
    finally:
        loader.close()


if __name__ == "__main__":
    main()
