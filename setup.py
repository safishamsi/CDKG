#!/usr/bin/env python3
"""
One-time setup script for the CDKG RAG system

This script:
1. Validates environment and configuration
2. Tests Neo4j connection
3. Checks for required data files
4. Verifies all dependencies
"""

import sys
from pathlib import Path
from config import config


def check_python_version():
    """Check Python version >= 3.8"""
    print("\n🐍 Checking Python version...")
    if sys.version_info < (3, 8):
        print("   ❌ Python 3.8+ required")
        print(f"   Current version: {sys.version}")
        return False
    print(f"   ✅ Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
    return True


def check_dependencies():
    """Check if all required packages are installed"""
    print("\n📦 Checking dependencies...")
    
    required_packages = {
        'neo4j': 'neo4j',
        'polars': 'polars',
        'sentence_transformers': 'sentence-transformers',
        'faiss': 'faiss-cpu',
        'anthropic': 'anthropic',
        'dotenv': 'python-dotenv',
        'tqdm': 'tqdm',
        'pydantic': 'pydantic',
        'numpy': 'numpy',
    }
    
    missing = []
    for module, package in required_packages.items():
        try:
            __import__(module.replace('-', '_'))
            print(f"   ✅ {package}")
        except ImportError:
            print(f"   ❌ {package} (missing)")
            missing.append(package)
    
    if missing:
        print(f"\n⚠️  Missing packages: {', '.join(missing)}")
        print("\nInstall with:")
        print(f"   pip install {' '.join(missing)}")
        return False
    
    return True


def check_env_file():
    """Check if .env file exists and has required variables"""
    print("\n📝 Checking .env file...")
    
    env_path = Path('.env')
    if not env_path.exists():
        print("   ❌ .env file not found")
        print("\n📋 Create .env file with:")
        print("   1. Copy .env.template to .env")
        print("   2. Fill in your Neo4j password")
        print("   3. Fill in your Anthropic API key")
        return False
    
    print("   ✅ .env file exists")
    
    # Check if required variables are set
    required_vars = {
        'NEO4J_PASSWORD': config.neo4j.password,
        'ANTHROPIC_API_KEY': config.llm.api_key
    }
    
    missing_vars = []
    for var_name, var_value in required_vars.items():
        if not var_value or var_value == 'your_password_here' or var_value == 'your_api_key_here':
            print(f"   ❌ {var_name} not set in .env")
            missing_vars.append(var_name)
        else:
            print(f"   ✅ {var_name} set")
    
    if missing_vars:
        print(f"\n⚠️  Please set these variables in .env: {', '.join(missing_vars)}")
        return False
    
    return True


def check_neo4j_connection():
    """Test Neo4j connection"""
    print("\n🔌 Testing Neo4j connection...")
    
    try:
        from neo4j import GraphDatabase
        
        driver = GraphDatabase.driver(
            config.neo4j.uri,
            auth=(config.neo4j.user, config.neo4j.password)
        )
        driver.verify_connectivity()
        
        with driver.session() as session:
            result = session.run("RETURN 1 as test")
            if result.single()['test'] == 1:
                print(f"   ✅ Connected to {config.neo4j.uri}")
                
                # Check if database has data
                result = session.run("MATCH (n) RETURN count(n) as count")
                node_count = result.single()['count']
                
                if node_count > 0:
                    print(f"   ℹ️  Database has {node_count} nodes (already loaded)")
                else:
                    print(f"   ℹ️  Database is empty (needs data loading)")
        
        driver.close()
        return True
        
    except Exception as e:
        print(f"   ❌ Connection failed: {e}")
        print("\n📋 Troubleshooting:")
        print("   1. Is Neo4j Desktop running?")
        print("   2. Is your database started?")
        print("   3. Check password in .env file")
        print("   4. Check URI in .env (should be bolt://localhost:7687)")
        return False


def check_data_files():
    """Check if cdl_db directory and CSV files exist"""
    print("\n📂 Checking data files...")
    
    cdl_db = config.paths.cdl_db_path
    
    if not cdl_db.exists():
        print(f"   ❌ cdl_db directory not found at {cdl_db}")
        print("\n📋 Setup instructions:")
        print(f"   1. Copy your cdl_db directory to: {config.paths.data_dir}/")
        print(f"   2. Ensure these files exist:")
        print(f"      - Speaker.csv")
        print(f"      - Talk.csv")
        print(f"      - Tag.csv")
        print(f"      - Event.csv")
        print(f"      - Category.csv")
        print(f"      - GIVES_TALK_Speaker_Talk.csv")
        print(f"      - IS_PART_OF_Talk_Event.csv")
        print(f"      - IS_CATEGORIZED_AS_Talk_Category.csv")
        print(f"      - IS_DESCRIBED_BY_Talk_Tag.csv")
        return False
    
    print(f"   ✅ cdl_db found at {cdl_db}")
    
    # Check CSV files
    required_files = [
        'Speaker.csv',
        'Talk.csv',
        'Tag.csv',
        'Event.csv',
        'Category.csv',
        'GIVES_TALK_Speaker_Talk.csv',
        'IS_PART_OF_Talk_Event.csv',
        'IS_CATEGORIZED_AS_Talk_Category.csv',
        'IS_DESCRIBED_BY_Talk_Tag.csv'
    ]
    
    missing_files = []
    for filename in required_files:
        filepath = cdl_db / filename
        if filepath.exists():
            print(f"   ✅ {filename}")
        else:
            print(f"   ❌ {filename} (missing)")
            missing_files.append(filename)
    
    if missing_files:
        print(f"\n⚠️  Missing files: {', '.join(missing_files)}")
        return False
    
    return True


def create_directories():
    """Create necessary directories"""
    print("\n📁 Creating directories...")
    
    config.paths.ensure_dirs()
    
    print(f"   ✅ {config.paths.data_dir}")
    print(f"   ✅ {config.paths.embeddings_dir}")


def main():
    """Run all setup checks"""
    print("=" * 70)
    print("🚀 CDKG RAG SYSTEM - SETUP")
    print("=" * 70)
    
    checks = [
        ("Python Version", check_python_version),
        ("Dependencies", check_dependencies),
        ("Environment File", check_env_file),
        ("Neo4j Connection", check_neo4j_connection),
        ("Data Files", check_data_files),
    ]
    
    results = []
    for check_name, check_func in checks:
        try:
            result = check_func()
            results.append((check_name, result))
        except Exception as e:
            print(f"   ❌ Error during {check_name}: {e}")
            results.append((check_name, False))
    
    # Create directories
    create_directories()
    
    # Print summary
    print("\n" + "=" * 70)
    print("📊 SETUP SUMMARY")
    print("=" * 70)
    
    all_passed = True
    for check_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} - {check_name}")
        if not passed:
            all_passed = False
    
    print("=" * 70)
    
    if all_passed:
        print("\n🎉 All checks passed! You're ready to run the pipeline.\n")
        print("Next steps:")
        print("   1. Run: python run_pipeline.py")
        print("   2. Or run steps individually:")
        print("      - python data_loader.py")
        print("      - python embedding_generator.py")
        print("      - python vector_store.py")
        print("      - python rag_system.py")
        print()
    else:
        print("\n⚠️  Some checks failed. Please fix the issues above.\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
