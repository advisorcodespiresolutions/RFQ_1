# California Retail Time & Attendance System

A comprehensive, California-compliant time tracking and attendance management system designed specifically for retail contingent workforce. This system automates time tracking, enforces compliance with California labor laws, calculates overtime according to state regulations, and manages paid holiday allocation.

## 🎯 Key Features

### Time Tracking & Punch Management
- **Multi-device Support**: Web punch, mobile app (with geo-fencing), and biometric terminals
- **Grace Period Management**: 5-minute grace window for clock in/out with automatic tracking
- **Missed Punch Alerts**: Automated alerts for employees and managers
- **Real-time Validation**: Prevents duplicate punches and invalid sequences

### California Labor Law Compliance
- **Daily Overtime**: >8 hours/day = 1.5x pay
- **Extended Daily Overtime**: >12 hours/day = 2.0x pay
- **7th Consecutive Day**: Double time beyond 8 hours
- **Special 16-Hour Rule**: >16 hours in single shift = 1.6x pay
- **Automatic Rule Application**: System applies the highest applicable rate when rules overlap

### Paid Holiday Management
- **Automatic Allocation**: 1 paid holiday/week for employees working 4+ shifts
- **Flexible Configuration**: Configurable holiday calendar and rules
- **Admin Override**: Special case holiday adjustments with approval tracking
- **Eligibility Tracking**: Real-time monitoring of holiday eligibility criteria

### Compliance & Reporting
- **California Labor Code Compliance**: §510, §554, and AB 1522 adherence
- **4-Year Audit Trail**: Complete timesheet audit logs retention
- **Violation Tracking**: Automated detection and reporting of compliance violations
- **Export Capabilities**: CSV, XML formats for payroll system integration

### Manager Functionality
- **Timesheet Approval**: Approve/reject timesheets with notes
- **Exception Reports**: Early/late clock-in alerts and overtime flags
- **Compliance Dashboard**: Real-time violation monitoring
- **Employee Management**: Comprehensive employee data and schedule management

## 🛠 Tech Stack

- **Backend**: FastAPI + PostgreSQL + SQLAlchemy
- **Frontend**: React + TailwindCSS (planned)
- **Authentication**: JWT-based authentication (planned)
- **Deployment**: Docker + containerized services
- **Compliance**: California Labor Code integration

## 📁 Project Structure

```
/
├── backend/                    # FastAPI backend
│   ├── app/
│   │   ├── api/               # API endpoints
│   │   │   └── time_attendance.py
│   │   ├── services/          # Business logic
│   │   │   ├── time_tracking_service.py
│   │   │   ├── overtime_service.py
│   │   │   └── holiday_service.py
│   │   ├── schemas/           # Pydantic models
│   │   │   └── time_attendance.py
│   │   ├── database/          # Database models
│   │   │   └── models.py
│   │   └── main.py
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/                   # React frontend (planned)
├── docker-compose.yml
└── README.md
```

## 🚀 Getting Started

### Prerequisites
- Python 3.8+
- PostgreSQL 12+
- Docker (optional)

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd time-attendance-system
   ```

2. **Set up the database**
   ```bash
   # Create PostgreSQL database
   createdb time_attendance_db
   ```

3. **Install dependencies**
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

4. **Configure environment variables**
   ```bash
   # Create .env file
   cp .env.example .env
   # Edit .env with your database credentials
   ```

5. **Run the application**
   ```bash
   # Development
   python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   
   # Or with Docker
   docker-compose up
   ```

6. **Access the API**
   - API Documentation: http://localhost:8000/docs
   - Health Check: http://localhost:8000/health

## 📊 API Endpoints

### Employee Management
- `POST /api/v1/time-attendance/employees/` - Create employee
- `GET /api/v1/time-attendance/employees/` - List employees
- `GET /api/v1/time-attendance/employees/{employee_id}` - Get employee
- `PUT /api/v1/time-attendance/employees/{employee_id}` - Update employee

### Time Tracking
- `POST /api/v1/time-attendance/punch/` - Process time punch
- `GET /api/v1/time-attendance/time-entries/` - Get time entries
- `PUT /api/v1/time-attendance/time-entries/{entry_id}` - Update time entry

### Timesheet Management
- `GET /api/v1/time-attendance/timesheets/{employee_id}` - Get employee timesheet
- `POST /api/v1/time-attendance/timesheets/approve` - Approve/reject timesheet

### Overtime Management
- `GET /api/v1/time-attendance/overtime/report/{employee_id}` - Get overtime report
- `GET /api/v1/time-attendance/overtime/summary` - Get overtime summary
- `POST /api/v1/time-attendance/overtime/config` - Create overtime config

### Holiday Management
- `POST /api/v1/time-attendance/holidays/allocate` - Allocate paid holidays
- `GET /api/v1/time-attendance/holidays/eligibility` - Get eligibility report
- `POST /api/v1/time-attendance/holidays/override` - Create holiday override

### Compliance & Reporting
- `GET /api/v1/time-attendance/compliance/report` - Get compliance report

## 🔧 Configuration

### Overtime Rules Configuration
The system supports configurable overtime rules:

```json
{
  "rule_name": "Daily 8 Hours",
  "rule_type": "daily_8_hours",
  "threshold_hours": 8.0,
  "multiplier": 1.5,
  "is_active": true
}
```

### Holiday Configuration
Configure paid holidays and eligibility rules:

```json
{
  "holiday_name": "New Year's Day",
  "holiday_type": "paid_holiday",
  "date": "2024-01-01",
  "is_active": true
}
```

## 📋 Compliance Features

### California Labor Code Compliance
- **§510**: Daily and weekly overtime requirements
- **§554**: Meal and rest period requirements
- **AB 1522**: Paid sick leave requirements
- **4-year retention**: All records retained for audit purposes

### Automated Compliance Checks
- Grace period violation detection
- Overtime limit monitoring
- Missed punch tracking
- Holiday eligibility validation

### Audit Trail
- Complete change history for all time entries
- Approval workflow tracking
- User action logging
- Export capabilities for regulatory filings

## 🔌 Integration

### Payroll System Integration
- **ADP**: REST API integration (planned)
- **UKG**: XML export format support
- **Oracle Cloud**: CSV export capabilities
- **Custom Formats**: Configurable export templates

### HRIS Integration
- Employee metadata synchronization
- Real-time data updates
- Bi-directional data flow

## 📈 Reporting

### Standard Reports
- Weekly hours summary per employee
- Overtime summary with rate codes
- Holiday eligibility tracking
- Compliance violation reports
- Pay period audit trails

### Custom Reports
- Department-specific summaries
- Date range filtering
- Export to multiple formats
- Real-time dashboard updates

## 🛡️ Security & Privacy

- **Data Encryption**: All sensitive data encrypted at rest
- **Access Control**: Role-based permissions
- **Audit Logging**: Complete user action tracking
- **GDPR Compliance**: Data privacy and retention policies
- **California Privacy Laws**: CCPA compliance

## 🚀 Deployment

### Production Deployment
```bash
# Build Docker image
docker build -t time-attendance-system .

# Run with environment variables
docker run -d \
  -p 8000:8000 \
  -e DATABASE_URL=postgresql://user:pass@host:port/db \
  -e SECRET_KEY=your-secret-key \
  time-attendance-system
```

### Docker Compose
```yaml
version: '3.8'
services:
  app:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/time_attendance
    depends_on:
      - db
  
  db:
    image: postgres:13
    environment:
      - POSTGRES_DB=time_attendance
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=pass
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

For support and questions:
- Email: support@timeattendance.com
- Documentation: [API Docs](http://localhost:8000/docs)
- Issues: [GitHub Issues](https://github.com/your-repo/issues)

## 🔄 Roadmap

### Phase 1 (Current)
- ✅ Core time tracking functionality
- ✅ California overtime calculation
- ✅ Basic reporting
- ✅ API endpoints

### Phase 2 (Next)
- 🔄 React frontend
- 🔄 Mobile app
- 🔄 Biometric integration
- 🔄 Advanced reporting

### Phase 3 (Future)
- 📋 AI-powered anomaly detection
- 📋 Predictive analytics
- 📋 Advanced compliance features
- 📋 Multi-location support