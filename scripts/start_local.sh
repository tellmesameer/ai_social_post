#!/bin/bash

# AI Social Post Generator - Local Development Startup Script

echo "🚀 Starting AI Social Post Generator..."

# Check if Python virtual environment is activated
if [[ "$VIRTUAL_ENV" == "" ]]; then
    echo "❌ Virtual environment not activated. Please activate it first:"
    echo "   source venv/bin/activate  # On Unix/Mac"
    echo "   venv\\Scripts\\activate     # On Windows"
    exit 1
fi

echo "✅ Virtual environment: $VIRTUAL_ENV"

# Install backend dependencies
echo "📦 Installing backend dependencies..."
cd backend
pip install -r requirements.txt
cd ..

# Install frontend dependencies
echo "📦 Installing frontend dependencies..."
cd frontend
pip install -r requirements.txt
cd ..

# Create necessary directories
echo "📁 Creating necessary directories..."
mkdir -p tmp
mkdir -p logs

# Start backend in background
echo "🔧 Starting FastAPI backend..."
cd backend
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000 > ../logs/backend.log 2>&1 &
BACKEND_PID=$!
cd ..

echo "✅ Backend started with PID: $BACKEND_PID"
echo "📋 Backend logs: logs/backend.log"
echo "🌐 Backend URL: http://localhost:8000"
echo "📚 API Docs: http://localhost:8000/docs"

# Wait a moment for backend to start
sleep 3

# Check if backend is running
if curl -s http://localhost:8000/health > /dev/null; then
    echo "✅ Backend is healthy and responding"
else
    echo "❌ Backend is not responding. Check logs/backend.log"
    kill $BACKEND_PID 2>/dev/null
    exit 1
fi

# Start frontend
echo "🎨 Starting Streamlit frontend..."
cd frontend
streamlit run streamlit_app.py --server.port 8501 --server.address 0.0.0.0 > ../logs/frontend.log 2>&1 &
FRONTEND_PID=$!
cd ..

echo "✅ Frontend started with PID: $FRONTEND_PID"
echo "📋 Frontend logs: logs/frontend.log"
echo "🌐 Frontend URL: http://localhost:8501"

# Save PIDs for cleanup
echo $BACKEND_PID > logs/backend.pid
echo $FRONTEND_PID > logs/frontend.pid

echo ""
echo "🎉 AI Social Post Generator is running!"
echo ""
echo "📱 Frontend: http://localhost:8501"
echo "🔧 Backend:  http://localhost:8000"
echo "📚 API Docs: http://localhost:8000/docs"
echo ""
echo "📋 Logs:"
echo "   Backend:  logs/backend.log"
echo "   Frontend: logs/frontend.log"
echo ""
echo "🛑 To stop all services, run: ./scripts/stop_local.sh"
echo ""

# Wait for user to stop
echo "Press Ctrl+C to stop all services..."
wait
