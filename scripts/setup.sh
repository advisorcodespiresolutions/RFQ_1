#!/bin/bash

# Manufacturing RFQ Intelligence Platform Setup Script

set -e

echo "🔧 Setting up Manufacturing RFQ Intelligence Platform..."

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Create environment file if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating environment file..."
    cat > .env << EOF
# Database Configuration
DATABASE_URL=postgresql://rfq_user:rfq_password@localhost:5432/rfq_platform

# Security
SECRET_KEY=$(openssl rand -hex 32)

# Redis
REDIS_URL=redis://localhost:6379

# Development
DEBUG=True
TESTING=False

# AI/ML Settings
AI_MODEL_PATH=ai_models/trained
CONFIDENCE_THRESHOLD=0.85

# File Upload
MAX_FILE_SIZE=104857600
UPLOAD_DIR=uploads

# Email (Optional - configure for production)
MAIL_USERNAME=
MAIL_PASSWORD=
MAIL_FROM=noreply@rfqplatform.com

# External APIs (Optional)
CURRENCY_API_KEY=
EOF
    echo "✅ Environment file created"
fi

# Create necessary directories
echo "📁 Creating project directories..."
mkdir -p backend/uploads
mkdir -p backend/ai_models/trained
mkdir -p backend/logs
mkdir -p docker/nginx
mkdir -p docker/postgres

# Create PostgreSQL init script
cat > docker/postgres/init.sql << EOF
-- Create database if not exists
SELECT 'CREATE DATABASE rfq_platform' WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'rfq_platform')\gexec

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
EOF

# Create Nginx configuration
cat > docker/nginx/nginx.conf << EOF
user nginx;
worker_processes auto;
error_log /var/log/nginx/error.log warn;
pid /var/run/nginx.pid;

events {
    worker_connections 1024;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;
    
    log_format main '\$remote_addr - \$remote_user [\$time_local] "\$request" '
                    '\$status \$body_bytes_sent "\$http_referer" '
                    '"\$http_user_agent" "\$http_x_forwarded_for"';
    
    access_log /var/log/nginx/access.log main;
    
    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    keepalive_timeout 65;
    types_hash_max_size 2048;
    
    include /etc/nginx/conf.d/*.conf;
}
EOF

cat > docker/nginx/default.conf << EOF
upstream backend {
    server backend:8000;
}

upstream frontend {
    server frontend:3000;
}

server {
    listen 80;
    server_name localhost;
    
    # Frontend
    location / {
        proxy_pass http://frontend;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
    
    # Backend API
    location /api/ {
        proxy_pass http://backend;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        client_max_body_size 100M;
    }
    
    # Backend static files
    location /uploads/ {
        proxy_pass http://backend;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
    }
    
    # Health check
    location /health {
        proxy_pass http://backend;
        proxy_set_header Host \$host;
    }
}
EOF

echo "✅ Configuration files created"

# Install backend dependencies
if [ -d "backend" ]; then
    echo "📦 Installing backend dependencies..."
    cd backend
    if [ -f "requirements.txt" ]; then
        python3 -m venv venv 2>/dev/null || echo "Virtual environment already exists"
        source venv/bin/activate 2>/dev/null || true
        pip install -r requirements.txt
    fi
    cd ..
fi

# Install frontend dependencies
if [ -d "frontend" ]; then
    echo "📦 Installing frontend dependencies..."
    cd frontend
    if [ -f "package.json" ]; then
        npm install
    fi
    cd ..
fi

echo "🐳 Building Docker containers..."
docker-compose build

echo "🚀 Starting services..."
docker-compose up -d

echo "⏳ Waiting for services to be ready..."
sleep 10

# Check if services are running
if docker-compose ps | grep -q "Up"; then
    echo "✅ Services are running!"
    echo ""
    echo "🌐 Application URLs:"
    echo "   Frontend: http://localhost:3000"
    echo "   Backend API: http://localhost:8000"
    echo "   API Docs: http://localhost:8000/docs"
    echo "   Database: localhost:5432"
    echo ""
    echo "📋 Default login credentials:"
    echo "   Username: admin"
    echo "   Password: admin123"
    echo ""
    echo "🔧 Management commands:"
    echo "   Stop services: docker-compose down"
    echo "   View logs: docker-compose logs -f"
    echo "   Restart: docker-compose restart"
    echo ""
    echo "✅ Setup complete! The Manufacturing RFQ Intelligence Platform is ready."
else
    echo "❌ Some services failed to start. Check logs with: docker-compose logs"
    exit 1
fi