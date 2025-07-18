#!/bin/bash
# filepath: /Users/nilatac/Documents/projects/private/aif-tracker/migration-js-python/quick-start.sh

echo "🚀 Starting AIF Tracker Migration..."

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

# Copy environment file
if [ ! -f backend/.env ]; then
    echo "📝 Creating environment file..."
    cp backend/.env.example backend/.env
    echo "⚠️  Please edit backend/.env with your API keys before proceeding"
fi

# Start services with Docker Compose
echo "🐳 Starting services with Docker Compose..."
cd docker

# Stop and remove everything including volumes
echo "🧹 Cleaning up existing containers and database..."
docker-compose down -v --remove-orphans
docker system prune -f
docker volume prune -f

# Start database first
echo "🐘 Starting PostgreSQL with fresh data..."
docker-compose up -d postgres

echo "⏳ Waiting for database to be ready..."
sleep 10

# Test database connection
for i in {1..15}; do
    if docker-compose exec -T postgres psql -U aif_tracker -d aif_tracker -c "SELECT 1;" > /dev/null 2>&1; then
        echo "✅ Database connection successful!"
        break
    fi
    echo "Waiting for database connection... ($i/15)"
    sleep 2
done

# Start backend
echo "🐍 Starting Python backend..."
docker-compose up -d backend celery-worker

echo "⏳ Waiting for backend to be ready..."
for i in {1..30}; do
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        echo "✅ Backend is ready!"
        break
    fi
    echo "Waiting for backend... ($i/30)"
    sleep 2
done

# Check if backend is actually ready
if ! curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "❌ Backend failed to start. Check logs with: docker-compose logs backend"
    echo "Frontend will run in demo mode."
fi

# Start frontend
echo "⚛️  Starting React frontend..."
docker-compose up -d frontend

echo ""
echo "✅ Services started successfully!"
echo ""
echo "🔍 Service Status:"
echo "Backend Health: $(curl -s http://localhost:8000/health 2>/dev/null | grep -o '"status":"[^"]*"' || echo 'Offline')"
echo "Frontend: http://localhost:5173"
echo "Backend API: http://localhost:8000"
echo "API Docs: http://localhost:8000/docs"
echo ""
echo "To stop all services: docker-compose down"
echo "To view logs: docker-compose logs -f [service-name]"