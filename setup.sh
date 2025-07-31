#!/bin/bash

# California Retail Time & Attendance System - Setup Script
# This script sets up the complete system with database initialization and sample data

set -e  # Exit on any error

echo "🚀 California Retail Time & Attendance System - Setup"
echo "=================================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Python 3.8+ is installed
check_python() {
    print_status "Checking Python version..."
    if command -v python3 &> /dev/null; then
        PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
        PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
        PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)
        
        if [ "$PYTHON_MAJOR" -ge 3 ] && [ "$PYTHON_MINOR" -ge 8 ]; then
            print_success "Python $PYTHON_VERSION found"
            PYTHON_CMD="python3"
        else
            print_error "Python 3.8+ required, found $PYTHON_VERSION"
            exit 1
        fi
    else
        print_error "Python 3 not found. Please install Python 3.8+"
        exit 1
    fi
}

# Check if pip is installed
check_pip() {
    print_status "Checking pip..."
    if command -v pip3 &> /dev/null; then
        print_success "pip3 found"
        PIP_CMD="pip3"
    elif command -v pip &> /dev/null; then
        print_success "pip found"
        PIP_CMD="pip"
    else
        print_error "pip not found. Please install pip"
        exit 1
    fi
}

# Check if PostgreSQL is installed
check_postgresql() {
    print_status "Checking PostgreSQL..."
    if command -v psql &> /dev/null; then
        print_success "PostgreSQL found"
    else
        print_warning "PostgreSQL not found. You'll need to install it manually or use Docker."
        print_status "For Ubuntu/Debian: sudo apt-get install postgresql postgresql-contrib"
        print_status "For macOS: brew install postgresql"
        print_status "For Windows: Download from https://www.postgresql.org/download/windows/"
    fi
}

# Install Python dependencies
install_dependencies() {
    print_status "Installing Python dependencies..."
    cd backend
    
    if [ -f "requirements.txt" ]; then
        $PIP_CMD install -r requirements.txt
        print_success "Dependencies installed"
    else
        print_error "requirements.txt not found in backend directory"
        exit 1
    fi
    
    cd ..
}

# Create environment file
create_env_file() {
    print_status "Creating environment configuration..."
    
    if [ ! -f "backend/.env" ]; then
        cat > backend/.env << EOF
# Database Configuration
DATABASE_URL=postgresql://postgres:password@localhost:5432/time_attendance_db

# Application Configuration
SECRET_KEY=your-secret-key-change-this-in-production
DEBUG=True
API_V1_STR=/api/v1

# CORS Configuration
ALLOWED_ORIGINS=["http://localhost:3000", "http://localhost:3001"]

# Logging Configuration
LOG_LEVEL=INFO
EOF
        print_success "Environment file created at backend/.env"
        print_warning "Please update the database credentials in backend/.env"
    else
        print_status "Environment file already exists"
    fi
}

# Initialize database
init_database() {
    print_status "Initializing database..."
    
    cd backend
    
    # Run database initialization script
    if [ -f "scripts/init_data.py" ]; then
        $PYTHON_CMD scripts/init_data.py
        print_success "Database initialized with sample data"
    else
        print_error "Database initialization script not found"
        exit 1
    fi
    
    cd ..
}

# Run tests
run_tests() {
    print_status "Running system tests..."
    
    cd backend
    
    if [ -f "test_system.py" ]; then
        $PYTHON_CMD test_system.py
        print_success "System tests completed"
    else
        print_error "Test script not found"
        exit 1
    fi
    
    cd ..
}

# Start the application
start_application() {
    print_status "Starting the application..."
    
    cd backend
    
    print_success "Application starting..."
    print_status "API Documentation will be available at: http://localhost:8000/docs"
    print_status "Health check will be available at: http://localhost:8000/health"
    print_status "Press Ctrl+C to stop the application"
    
    $PYTHON_CMD -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
}

# Main setup function
main() {
    echo ""
    print_status "Starting setup process..."
    
    # Check prerequisites
    check_python
    check_pip
    check_postgresql
    
    # Install dependencies
    install_dependencies
    
    # Create environment file
    create_env_file
    
    # Initialize database
    init_database
    
    # Run tests
    run_tests
    
    echo ""
    print_success "Setup completed successfully!"
    echo ""
    print_status "Next steps:"
    echo "1. Update database credentials in backend/.env if needed"
    echo "2. Start the application: ./setup.sh --start"
    echo "3. Access the API documentation at http://localhost:8000/docs"
    echo "4. Test the endpoints with the sample data"
    echo ""
    print_status "Sample employee IDs for testing:"
    echo "  - EMP001 (Sarah Johnson)"
    echo "  - EMP002 (Michael Chen)"
    echo "  - EMP003 (Maria Garcia)"
    echo "  - EMP004 (David Thompson)"
    echo "  - EMP005 (Lisa Wang)"
    echo ""
}

# Handle command line arguments
case "${1:-}" in
    --start)
        start_application
        ;;
    --help|-h)
        echo "Usage: $0 [OPTION]"
        echo ""
        echo "Options:"
        echo "  --start    Start the application after setup"
        echo "  --help     Show this help message"
        echo ""
        echo "Examples:"
        echo "  $0          # Run full setup"
        echo "  $0 --start  # Run setup and start application"
        ;;
    *)
        main
        ;;
esac