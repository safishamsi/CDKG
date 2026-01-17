"""
Test Production Deployment with Updated Knowledge Graph

This script tests:
1. Backend health
2. Graph data (should exclude Tag nodes)
3. Talk nodes have tags property
4. API endpoints work correctly
"""

import requests
import json
import os
from dotenv import load_dotenv

load_dotenv()

# Get API URL from environment or use default
API_URL = os.getenv("VITE_API_URL", "http://localhost:8000")
if API_URL.endswith("/"):
    API_URL = API_URL[:-1]

print("=" * 70)
print("🧪 TESTING PRODUCTION DEPLOYMENT")
print("=" * 70)
print(f"API URL: {API_URL}\n")

def test_health():
    """Test backend health endpoint"""
    print("1️⃣  Testing Health Endpoint...")
    try:
        response = requests.get(f"{API_URL}/health", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Health check passed")
            print(f"   Status: {data.get('status')}")
            print(f"   Neo4j Connected: {data.get('neo4j_connected')}")
            return True
        else:
            print(f"   ❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Health check error: {e}")
        return False

def test_graph_data():
    """Test graph data endpoint - should exclude Tag nodes"""
    print("\n2️⃣  Testing Graph Data (should exclude Tag nodes)...")
    try:
        response = requests.get(f"{API_URL}/api/graph?limit=50", timeout=30)
        if response.status_code == 200:
            data = response.json()
            nodes = data.get('nodes', [])
            links = data.get('links', [])
            
            # Check for Tag nodes
            tag_nodes = [n for n in nodes if n.get('type') == 'Tag']
            
            print(f"   ✅ Graph data retrieved")
            print(f"   Total nodes: {len(nodes)}")
            print(f"   Total links: {len(links)}")
            
            if tag_nodes:
                print(f"   ⚠️  WARNING: Found {len(tag_nodes)} Tag nodes (should be 0)")
                print(f"   Tag nodes: {[n.get('name') for n in tag_nodes[:5]]}")
            else:
                print(f"   ✅ No Tag nodes found (correct!)")
            
            # Check node types
            node_types = {}
            for node in nodes:
                node_type = node.get('type', 'Unknown')
                node_types[node_type] = node_types.get(node_type, 0) + 1
            
            print(f"\n   Node types breakdown:")
            for ntype, count in sorted(node_types.items()):
                print(f"      {ntype}: {count}")
            
            # Check if Talk nodes have tags property
            talk_nodes = [n for n in nodes if n.get('type') == 'Talk']
            talks_with_tags = [n for n in talk_nodes if 'tags' in n.get('properties', {})]
            
            print(f"\n   Talk nodes: {len(talk_nodes)}")
            if talks_with_tags:
                print(f"   ✅ {len(talks_with_tags)} Talk nodes have tags property")
                # Show example
                example = talks_with_tags[0]
                tags = example.get('properties', {}).get('tags', [])
                if tags:
                    print(f"   Example tags: {tags[:5]}")
            else:
                print(f"   ⚠️  No Talk nodes have tags property yet")
            
            return True
        else:
            print(f"   ❌ Graph data failed: {response.status_code}")
            print(f"   Response: {response.text[:200]}")
            return False
    except Exception as e:
        print(f"   ❌ Graph data error: {e}")
        return False

def test_query():
    """Test query endpoint"""
    print("\n3️⃣  Testing Query Endpoint...")
    try:
        payload = {
            "query": "What is Connected Data?",
            "max_hops": 2
        }
        response = requests.post(
            f"{API_URL}/api/query",
            json=payload,
            timeout=30,
            headers={"Content-Type": "application/json"}
        )
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Query successful")
            print(f"   Answer: {data.get('answer', '')[:100]}...")
            return True
        else:
            print(f"   ❌ Query failed: {response.status_code}")
            print(f"   Response: {response.text[:200]}")
            return False
    except Exception as e:
        print(f"   ❌ Query error: {e}")
        return False

def test_stats():
    """Test stats endpoint"""
    print("\n4️⃣  Testing Stats Endpoint...")
    try:
        response = requests.get(f"{API_URL}/api/stats", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Stats retrieved")
            print(f"   Node counts: {data.get('node_counts', {})}")
            print(f"   Total relationships: {data.get('relationship_count', 0)}")
            
            # Check for Tag nodes in stats
            tag_count = data.get('node_counts', {}).get('Tag', 0)
            if tag_count > 0:
                print(f"   ⚠️  WARNING: {tag_count} Tag nodes still in database")
                print(f"   Consider running migration script: python migrate_tags_to_properties.py")
            else:
                print(f"   ✅ No Tag nodes in database (correct!)")
            
            return True
        else:
            print(f"   ❌ Stats failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Stats error: {e}")
        return False

def main():
    """Run all tests"""
    results = []
    
    results.append(("Health", test_health()))
    results.append(("Graph Data", test_graph_data()))
    results.append(("Query", test_query()))
    results.append(("Stats", test_stats()))
    
    print("\n" + "=" * 70)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 70)
    
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    all_passed = all(result[1] for result in results)
    
    print("\n" + "=" * 70)
    if all_passed:
        print("✅ ALL TESTS PASSED!")
    else:
        print("⚠️  SOME TESTS FAILED - Check output above")
    print("=" * 70)
    
    # Recommendations
    print("\n💡 RECOMMENDATIONS:")
    print("1. If Tag nodes still exist, run: python migrate_tags_to_properties.py")
    print("2. Process a new YouTube video to test tags as property")
    print("3. Check frontend graph visualization")
    print("4. Verify Talk nodes show tags in properties panel")

if __name__ == "__main__":
    main()

