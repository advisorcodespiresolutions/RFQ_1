#!/bin/bash

# Time & Attendance System Setup Script
# California Retail Compliance System

set -e

echo "🚀 Setting up Time & Attendance System for California Retail..."

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

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    print_error "Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    print_error "Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

print_status "Checking Docker and Docker Compose installation..."
print_success "Docker and Docker Compose are available"

# Create necessary directories
print_status "Creating necessary directories..."
mkdir -p logs
mkdir -p data/postgres
mkdir -p data/redis
mkdir -p nginx/ssl

# Set up environment variables
print_status "Setting up environment variables..."
if [ ! -f .env ]; then
    cat > .env << EOF
# Time & Attendance System Environment Variables
# California Retail Compliance System

# Database Configuration
DATABASE_URL=postgresql://postgres:postgres123@localhost:5432/time_attendance
POSTGRES_DB=time_attendance
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres123

# Redis Configuration
REDIS_URL=redis://localhost:6379
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# Security
SECRET_KEY=your-super-secret-key-change-this-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# CORS Settings
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000

# California Compliance Settings
CA_TIMEZONE=US/Pacific
GRACE_PERIOD_MINUTES=5
GEOFENCE_RADIUS_METERS=100

# Email Settings (for notifications)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password

# Payroll Integration
PAYROLL_SYSTEM=ADP
PAYROLL_API_URL=https://api.adp.com
PAYROLL_API_KEY=your-payroll-api-key

# Audit Settings
AUDIT_RETENTION_YEARS=4
COMPLIANCE_REPORTING_ENABLED=true

# Development Settings
DEBUG=true
LOG_LEVEL=INFO
EOF
    print_success "Created .env file"
else
    print_warning ".env file already exists"
fi

# Create database initialization script
print_status "Creating database initialization script..."
mkdir -p scripts
cat > scripts/init.sql << EOF
-- Time & Attendance System Database Initialization
-- California Retail Compliance System

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Create locations table and insert sample data
INSERT INTO locations (name, address, latitude, longitude, geofence_radius, is_active) VALUES
('Downtown Store', '123 Main St, Los Angeles, CA 90012', 34.0522, -118.2437, 100.0, true),
('Westside Store', '456 Sunset Blvd, Los Angeles, CA 90069', 34.0928, -118.3287, 100.0, true),
('Valley Store', '789 Ventura Blvd, Studio City, CA 91604', 34.1528, -118.3969, 100.0, true),
('Beach Store', '321 Ocean Ave, Santa Monica, CA 90401', 34.0195, -118.4912, 100.0, true)
ON CONFLICT DO NOTHING;

-- Create sample employees
INSERT INTO employees (employee_id, first_name, last_name, email, phone, hire_date, hourly_rate, location_id, is_active) VALUES
('EMP001', 'John', 'Doe', 'john.doe@retail.com', '555-0101', '2023-01-15', 18.50, 1, true),
('EMP002', 'Jane', 'Smith', 'jane.smith@retail.com', '555-0102', '2023-02-01', 19.00, 1, true),
('EMP003', 'Mike', 'Johnson', 'mike.johnson@retail.com', '555-0103', '2023-01-20', 17.75, 2, true),
('EMP004', 'Sarah', 'Williams', 'sarah.williams@retail.com', '555-0104', '2023-02-10', 18.25, 2, true),
('EMP005', 'David', 'Brown', 'david.brown@retail.com', '555-0105', '2023-01-25', 19.50, 3, true),
('EMP006', 'Lisa', 'Davis', 'lisa.davis@retail.com', '555-0106', '2023-02-15', 18.00, 3, true),
('EMP007', 'Robert', 'Wilson', 'robert.wilson@retail.com', '555-0107', '2023-01-30', 20.00, 4, true),
('EMP008', 'Maria', 'Garcia', 'maria.garcia@retail.com', '555-0108', '2023-02-20', 18.75, 4, true)
ON CONFLICT DO NOTHING;

-- Create manager relationships
UPDATE employees SET manager_id = 1 WHERE employee_id IN ('EMP002', 'EMP003', 'EMP004');
UPDATE employees SET manager_id = 5 WHERE employee_id IN ('EMP006', 'EMP007', 'EMP008');

-- Create sample schedules for current week
INSERT INTO schedules (employee_id, date, start_time, end_time, break_duration, is_holiday) VALUES
(1, CURRENT_DATE, '09:00:00', '17:00:00', 30, false),
(2, CURRENT_DATE, '10:00:00', '18:00:00', 30, false),
(3, CURRENT_DATE, '08:00:00', '16:00:00', 30, false),
(4, CURRENT_DATE, '11:00:00', '19:00:00', 30, false),
(5, CURRENT_DATE, '09:30:00', '17:30:00', 30, false),
(6, CURRENT_DATE, '10:30:00', '18:30:00', 30, false),
(7, CURRENT_DATE, '08:30:00', '16:30:00', 30, false),
(8, CURRENT_DATE, '11:30:00', '19:30:00', 30, false)
ON CONFLICT DO NOTHING;

-- Create sample time entries for today
INSERT INTO time_entries (employee_id, punch_type, punch_time, location_id, device_type, is_within_grace_period, status) VALUES
(1, 'clock_in', CURRENT_TIMESTAMP - INTERVAL '2 hours', 1, 'web', true, 'approved'),
(2, 'clock_in', CURRENT_TIMESTAMP - INTERVAL '1 hour 55 minutes', 1, 'mobile', true, 'approved'),
(3, 'clock_in', CURRENT_TIMESTAMP - INTERVAL '3 hours', 2, 'web', true, 'approved'),
(4, 'clock_in', CURRENT_TIMESTAMP - INTERVAL '2 hours 30 minutes', 2, 'mobile', true, 'pending'),
(5, 'clock_in', CURRENT_TIMESTAMP - INTERVAL '2 hours 15 minutes', 3, 'web', true, 'approved'),
(6, 'clock_in', CURRENT_TIMESTAMP - INTERVAL '1 hour 45 minutes', 3, 'mobile', true, 'approved'),
(7, 'clock_in', CURRENT_TIMESTAMP - INTERVAL '3 hours 30 minutes', 4, 'web', true, 'approved'),
(8, 'clock_in', CURRENT_TIMESTAMP - INTERVAL '2 hours 45 minutes', 4, 'mobile', true, 'pending')
ON CONFLICT DO NOTHING;

-- Create sample compliance audits
INSERT INTO compliance_audits (employee_id, audit_date, violation_type, description, severity, resolved) VALUES
(4, CURRENT_DATE, 'grace_period_violation', 'Clock in 7 minutes late', 'low', false),
(8, CURRENT_DATE, 'grace_period_violation', 'Clock in 6 minutes late', 'low', false),
(2, CURRENT_DATE - INTERVAL '1 day', 'geofence_violation', 'Punch outside geofence boundary', 'medium', true)
ON CONFLICT DO NOTHING;

print_success "Created database initialization script"

# Build and start services
print_status "Building and starting Docker services..."
docker-compose down -v 2>/dev/null || true
docker-compose build --no-cache
docker-compose up -d

# Wait for services to be ready
print_status "Waiting for services to be ready..."
sleep 30

# Check if services are running
print_status "Checking service health..."
if docker-compose ps | grep -q "Up"; then
    print_success "All services are running"
else
    print_error "Some services failed to start"
    docker-compose logs
    exit 1
fi

# Run database migrations
print_status "Running database migrations..."
docker-compose exec backend alembic upgrade head

# Create admin user
print_status "Creating admin user..."
docker-compose exec backend python -c "
from app.models.time_attendance import Employee
from app.database import SessionLocal
from datetime import datetime

db = SessionLocal()
try:
    admin = Employee(
        employee_id='ADMIN001',
        first_name='Admin',
        last_name='User',
        email='admin@retail.com',
        phone='555-0000',
        hire_date=datetime.now(),
        hourly_rate=25.00,
        location_id=1,
        is_active=True
    )
    db.add(admin)
    db.commit()
    print('Admin user created successfully')
except Exception as e:
    print(f'Error creating admin user: {e}')
finally:
    db.close()
"

# Run initial compliance calculations
print_status "Running initial compliance calculations..."
docker-compose exec backend python -c "
from app.services.california_compliance import CaliforniaComplianceEngine
from app.database import SessionLocal
from datetime import date

db = SessionLocal()
try:
    engine = CaliforniaComplianceEngine(db)
    
    # Calculate overtime for all employees for today
    employees = db.query(Employee).filter(Employee.is_active == True).all()
    for employee in employees:
        engine.calculate_daily_overtime(employee.id, date.today())
        engine.calculate_sixteen_plus_overtime(employee.id, date.today())
    
    # Allocate paid holidays for current week
    from datetime import datetime, timedelta
    week_start = date.today() - timedelta(days=date.today().weekday())
    engine.allocate_paid_holidays(week_start)
    
    print('Initial compliance calculations completed')
except Exception as e:
    print(f'Error running compliance calculations: {e}')
finally:
    db.close()
"

# Display system information
print_success "🎉 Time & Attendance System setup completed!"
echo ""
echo "📋 System Information:"
echo "  • Frontend: http://localhost:3000"
echo "  • Backend API: http://localhost:8000"
echo "  • API Documentation: http://localhost:8000/docs"
echo "  • Database: PostgreSQL on localhost:5432"
echo "  • Redis: localhost:6379"
echo ""
echo "👥 Sample Users:"
echo "  • Employee: john.doe@retail.com (EMP001)"
echo "  • Manager: Admin User (ADMIN001)"
echo ""
echo "🔧 California Compliance Features:"
echo "  • Daily overtime calculation (>8h = 1.5x, >12h = 2.0x)"
echo "  • 7th consecutive day double time"
echo "  • 16+ hour shift special rule (1.6x)"
echo "  • 5-minute grace period validation"
echo "  • Geofencing for location verification"
echo "  • Automatic paid holiday allocation"
echo "  • 4-year audit trail retention"
echo ""
echo "📊 Available Reports:"
echo "  • Weekly hours summary"
echo "  • Overtime breakdown by type"
echo "  • Holiday eligibility tracking"
echo "  • Compliance violation reports"
echo ""
echo "🚀 Next Steps:"
echo "  1. Access the frontend at http://localhost:3000"
echo "  2. Use the time clock to punch in/out"
echo "  3. Access manager dashboard at http://localhost:3000/manager"
echo "  4. Review compliance reports and overtime calculations"
echo ""
echo "⚠️  Important Notes:"
echo "  • Change default passwords in production"
echo "  • Update SECRET_KEY in .env file"
echo "  • Configure email settings for notifications"
echo "  • Set up SSL certificates for production"
echo "  • Configure payroll system integration"
echo ""
print_success "Setup completed successfully! 🎉"