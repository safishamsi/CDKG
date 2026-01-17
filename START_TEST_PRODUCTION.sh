#!/bin/bash
# Quick script to start backend and run production tests

echo "🚀 Starting Production Test..."
echo ""

# Check if backend is already running
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ Backend is already running!"
else
    echo "📦 Starting backend..."
    cd /Users/safi/Downloads/cdkg-challenge-main
    python3.9 backend_api_youtube.py > backend_test.log 2>&1 &
    BACKEND_PID=$!
    echo "Backend starting (PID: $BACKEND_PID)..."
    
    # Wait for backend to start
    echo "⏳ Waiting for backend to start..."
    for i in {1..30}; do
        if curl -s http://localhost:8000/health > /dev/null 2>&1; then
            echo "✅ Backend is ready!"
            break
        fi
        sleep 1
        echo -n "."
    done
    echo ""
fi

# Check if backend is ready
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo ""
    echo "🧪 Running production tests..."
    echo ""
    python3.9 test_production.py
    
    echo ""
    echo "📋 Next steps:"
    echo "1. Check test results above"
    echo "2. If Tag nodes exist, run: python3.9 migrate_tags_to_properties.py"
    echo "3. Test frontend at: http://localhost:5173 (or your Vercel URL)"
    echo ""
    echo "To stop backend: pkill -f backend_api_youtube.py"
else
    echo ""
    echo "❌ Backend failed to start. Check backend_test.log for errors:"
    echo "   tail -50 backend_test.log"
    echo ""
    echo "Common issues:"
    echo "- Neo4j not running (start Neo4j Desktop)"
    echo "- Missing .env file or credentials"
    echo "- Port 8000 already in use"
fi

