#!/bin/bash
# Start script for development

echo "🚀 Starting CDKG RAG Chatbot..."
echo ""

# Check if backend is running
if ! curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "📦 Starting backend server..."
    python backend_api.py &
    BACKEND_PID=$!
    echo "   Backend PID: $BACKEND_PID"
    sleep 3
else
    echo "✅ Backend already running on port 8000"
fi

# Check if frontend dependencies are installed
if [ ! -d "frontend/node_modules" ]; then
    echo "📦 Installing frontend dependencies..."
    cd frontend
    npm install
    cd ..
fi

echo ""
echo "✅ Ready! Open http://localhost:3000 in your browser"
echo ""
echo "Press Ctrl+C to stop all servers"
echo ""

# Start frontend
cd frontend
npm run dev
