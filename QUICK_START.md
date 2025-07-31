# Time & Attendance System - Quick Start Guide

## 🚀 Getting Started

This guide will help you set up and run the Time & Attendance system for your California retail client in under 10 minutes.

## Prerequisites

- Docker and Docker Compose installed
- At least 4GB RAM available
- Ports 3000, 8000, 5432, and 6379 available

## Quick Setup

### 1. Clone and Setup

```bash
# Clone the repository (if not already done)
git clone <repository-url>
cd time-attendance-system

# Make setup script executable
chmod +x scripts/setup.sh

# Run the automated setup
./scripts/setup.sh
```

### 2. Access the System

Once setup is complete, access the system at:

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

### 3. Sample Data

The system comes pre-loaded with sample data:

#### Employees
- **John Doe** (EMP001) - Downtown Store
- **Jane Smith** (EMP002) - Downtown Store  
- **Mike Johnson** (EMP003) - Westside Store
- **Sarah Williams** (EMP004) - Westside Store
- **David Brown** (EMP005) - Valley Store
- **Lisa Davis** (EMP006) - Valley Store
- **Robert Wilson** (EMP007) - Beach Store
- **Maria Garcia** (EMP008) - Beach Store

#### Admin User
- **Admin User** (ADMIN001) - System Administrator

## 🕐 Using the Time Clock

### Employee Time Clock

1. Navigate to http://localhost:3000
2. You'll see the time clock interface
3. Click "Clock In" to start your shift
4. Click "Clock Out" to end your shift

**Features:**
- Real-time clock display
- GPS location verification
- 5-minute grace period
- Automatic compliance checking

### Manager Dashboard

1. Navigate to http://localhost:3000/manager
2. View pending approvals
3. Monitor overtime alerts
4. Review compliance violations

**Features:**
- Real-time dashboard
- Approval workflows
- Overtime monitoring
- Compliance reporting

## 📊 California Compliance Features

### Automatic Overtime Calculation

The system automatically calculates overtime according to California Labor Code §510:

- **8+ hours/day**: 1.5x base rate
- **12+ hours/day**: 2.0x base rate  
- **7th consecutive day**: 2.0x base rate
- **16+ hours in single shift**: 1.6x base rate (special rule)

### Grace Period Management

- 5-minute grace window for clock in/out
- Automatic violation detection
- Manager approval workflow
- Compliance audit logging

### Paid Holiday Allocation

- Automatic allocation for employees working 4+ shifts/week
- 8 hours paid at base rate
- Manager override capability
- Audit trail tracking

## 🔧 API Usage

### Time Entry

```bash
# Clock in
curl -X POST http://localhost:8000/api/time-attendance/punch \
  -H "Content-Type: application/json" \
  -d '{
    "employee_id": 1,
    "punch_type": "clock_in",
    "device_type": "web",
    "latitude": 34.0522,
    "longitude": -118.2437
  }'

# Clock out
curl -X POST http://localhost:8000/api/time-attendance/punch \
  -H "Content-Type: application/json" \
  -d '{
    "employee_id": 1,
    "punch_type": "clock_out",
    "device_type": "web"
  }'
```

### Overtime Calculation

```bash
# Calculate overtime for today
curl -X POST http://localhost:8000/api/time-attendance/overtime/calculate/1 \
  -H "Content-Type: application/json" \
  -d '{"work_date": "2024-01-15"}'
```

### Reports

```bash
# Get weekly summary
curl "http://localhost:8000/api/time-attendance/reports/weekly-summary?week_start=2024-01-15"

# Get compliance report
curl "http://localhost:8000/api/time-attendance/compliance/report?start_date=2024-01-01&end_date=2024-01-31"
```

## 📋 Management Commands

### Start Services
```bash
docker-compose up -d
```

### Stop Services
```bash
docker-compose down
```

### View Logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f frontend
```

### Restart Services
```bash
docker-compose restart
```

### Update System
```bash
git pull
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

## 🔍 Monitoring

### Health Checks

- **Frontend**: http://localhost:3000
- **Backend**: http://localhost:8000/health
- **Database**: `docker-compose exec postgres pg_isready`
- **Redis**: `docker-compose exec redis redis-cli ping`

### Key Metrics

- **Pending Approvals**: Check manager dashboard
- **Overtime Alerts**: Monitor compliance tab
- **System Performance**: View Docker logs
- **Database Size**: `docker-compose exec postgres psql -U postgres -d time_attendance -c "SELECT pg_size_pretty(pg_database_size('time_attendance'));"`

## 🛠 Troubleshooting

### Common Issues

#### Services Not Starting
```bash
# Check Docker status
docker --version
docker-compose --version

# Check available ports
netstat -tulpn | grep :3000
netstat -tulpn | grep :8000
```

#### Database Connection Issues
```bash
# Check database status
docker-compose exec postgres pg_isready

# Reset database
docker-compose down -v
docker-compose up -d postgres
sleep 10
docker-compose up -d
```

#### Frontend Not Loading
```bash
# Check frontend logs
docker-compose logs frontend

# Rebuild frontend
docker-compose build --no-cache frontend
docker-compose up -d frontend
```

### Performance Issues

#### High Memory Usage
```bash
# Check container resource usage
docker stats

# Restart services
docker-compose restart
```

#### Slow Response Times
```bash
# Check database performance
docker-compose exec postgres psql -U postgres -d time_attendance -c "SELECT * FROM pg_stat_activity;"

# Check Redis performance
docker-compose exec redis redis-cli info memory
```

## 📞 Support

### Documentation
- **Full Documentation**: `/docs/`
- **API Reference**: http://localhost:8000/docs
- **Compliance Guide**: `/docs/CALIFORNIA_COMPLIANCE.md`

### Getting Help
- **Technical Issues**: Check Docker logs
- **Compliance Questions**: Review compliance documentation
- **Feature Requests**: Create GitHub issue

### Emergency Contacts
- **System Down**: Check Docker status and logs
- **Data Issues**: Review database logs
- **Performance**: Monitor resource usage

## 🎯 Next Steps

### Production Deployment
1. Update environment variables
2. Configure SSL certificates
3. Set up monitoring and alerts
4. Configure backup procedures
5. Test payroll integration

### Customization
1. Modify overtime rules if needed
2. Configure geofence settings
3. Customize holiday allocation rules
4. Set up email notifications
5. Configure payroll system integration

### Training
1. Employee time clock training
2. Manager dashboard training
3. Compliance reporting training
4. API integration training

---

**🎉 Congratulations!** Your Time & Attendance system is now running and ready for use. The system is fully compliant with California Labor Code requirements and ready for your retail contingent workforce.