# California Labor Law Compliance Guide

## Overview

This Time & Attendance system is specifically designed to comply with California Labor Code requirements for retail contingent workers. The system implements all mandatory overtime rules, break requirements, and audit trail requirements.

## California Labor Code Compliance

### §510 - Overtime Requirements

The system automatically calculates overtime according to California Labor Code §510:

#### Daily Overtime Rules
- **8+ hours/day**: Time-and-a-half (1.5x base rate)
- **12+ hours/day**: Double time (2.0x base rate)
- **7th consecutive day**: Double time for all hours beyond 8

#### Weekly Overtime Rules
- **40+ hours/week**: Time-and-a-half (1.5x base rate)

#### Special 16+ Hour Rule
- **16+ hours in single shift**: 1.6x base rate (client-specific requirement)

### §554 - Alternative Workweek Schedules

The system supports alternative workweek schedules as permitted under §554:
- 4-day workweek (10 hours/day)
- Automatic overtime calculation for hours beyond alternative schedule
- Proper documentation and approval workflows

### AB 1522 - Healthy Workplaces/Healthy Families Act

Compliance with paid sick leave requirements:
- Automatic accrual tracking
- Usage monitoring
- Reporting for compliance audits

## System Features

### 1. Multi-Modal Time Tracking

#### Web Punch
- Secure web-based time clock
- IP address tracking
- User agent logging
- Session management

#### Mobile App (Geofenced)
- GPS location verification
- Geofence boundary enforcement
- Offline capability with sync
- Biometric authentication support

#### Biometric Terminals
- Fingerprint/face recognition
- Hardware integration
- Fallback to manual entry
- Audit trail preservation

### 2. Grace Period Management

#### 5-Minute Grace Window
- Clock in/out within 5 minutes of scheduled time
- Automatic grace period detection
- Manager notification for violations
- Compliance audit logging

#### Exception Handling
- Manager approval for late punches
- Reason documentation
- Pattern analysis for recurring issues
- Escalation workflows

### 3. Overtime Calculation Engine

#### Automatic Calculation
```python
# Daily overtime calculation
if hours_worked > 8:
    overtime_8h = min(hours_worked - 8, 4)  # Hours 8-12
    overtime_12h = max(0, hours_worked - 12)  # Hours beyond 12

# 7th consecutive day check
if is_seventh_consecutive_day:
    overtime_rate = 2.0  # Double time

# 16+ hour special rule
if hours_worked > 16:
    overtime_16h = hours_worked - 16
    overtime_rate = 1.6  # Special rate
```

#### Rate Hierarchy
1. **16+ hour rule**: 1.6x (highest priority)
2. **12+ hour rule**: 2.0x
3. **7th consecutive day**: 2.0x
4. **8+ hour rule**: 1.5x
5. **40+ hour weekly**: 1.5x

### 4. Paid Holiday Management

#### Automatic Allocation
- 1 paid holiday per week for employees working 4+ shifts
- 8 hours paid at base rate
- Automatic eligibility calculation
- Manager override capability

#### Holiday Configuration
- Flexible holiday calendar
- Location-specific holidays
- Employee-specific exceptions
- Audit trail for all changes

### 5. Compliance Reporting

#### Required Reports
- **Weekly hours summary**: Per employee breakdown
- **Overtime summary**: Rate codes and calculations
- **Holiday eligibility**: Tracking and allocation
- **Pay period audit**: California audit compliance

#### Export Formats
- **CSV**: Standard payroll integration
- **XML**: Compliance filing format
- **PDF**: Audit documentation
- **JSON**: API integration

### 6. Audit Trail Requirements

#### 4-Year Retention
- All time entries preserved
- Change history tracked
- Approval workflows logged
- Compliance violations recorded

#### Data Integrity
- Immutable audit logs
- Digital signatures
- Backup and recovery
- Encryption at rest

## Implementation Details

### Database Schema

#### Core Tables
```sql
-- Employees
employees (id, employee_id, first_name, last_name, hourly_rate, location_id)

-- Time Entries
time_entries (id, employee_id, punch_type, punch_time, location_id, status)

-- Overtime Calculations
overtime_calculations (id, employee_id, date, overtime_type, hours, rate, pay)

-- Paid Holidays
paid_holidays (id, employee_id, date, hours_paid, is_auto_allocated)

-- Compliance Audits
compliance_audits (id, employee_id, violation_type, description, severity)
```

#### Compliance Tracking
```sql
-- Grace period violations
grace_period_violations (time_entry_id, minutes_late, approved_by)

-- Geofence violations
geofence_violations (time_entry_id, distance_meters, location_name)

-- Overtime violations
overtime_violations (employee_id, date, hours_worked, violation_type)
```

### API Endpoints

#### Time Tracking
```http
POST /api/time-attendance/punch
GET /api/time-attendance/time-entries/{employee_id}
PUT /api/time-attendance/time-entries/{time_entry_id}
```

#### Overtime Calculation
```http
POST /api/time-attendance/overtime/calculate/{employee_id}
GET /api/time-attendance/overtime/summary/{employee_id}
```

#### Holiday Management
```http
POST /api/time-attendance/holidays/allocate
GET /api/time-attendance/holidays/{employee_id}
POST /api/time-attendance/holidays/manual
```

#### Compliance Reporting
```http
GET /api/time-attendance/compliance/report
GET /api/time-attendance/reports/weekly-summary
GET /api/time-attendance/reports/holiday-eligibility
```

### California Compliance Engine

#### Core Functions
```python
class CaliforniaComplianceEngine:
    def calculate_daily_overtime(self, employee_id, work_date)
    def calculate_sixteen_plus_overtime(self, employee_id, work_date)
    def calculate_weekly_overtime(self, employee_id, week_start)
    def check_grace_period_compliance(self, time_entry, schedule)
    def check_geofence_compliance(self, time_entry, location_id)
    def allocate_paid_holidays(self, week_start)
    def create_compliance_audit(self, employee_id, violation_type, description)
    def generate_compliance_report(self, start_date, end_date)
```

## Configuration

### Environment Variables

#### Database
```bash
DATABASE_URL=postgresql://user:password@localhost:5432/time_attendance
POSTGRES_DB=time_attendance
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres123
```

#### California Settings
```bash
CA_TIMEZONE=US/Pacific
GRACE_PERIOD_MINUTES=5
GEOFENCE_RADIUS_METERS=100
AUDIT_RETENTION_YEARS=4
COMPLIANCE_REPORTING_ENABLED=true
```

#### Payroll Integration
```bash
PAYROLL_SYSTEM=ADP
PAYROLL_API_URL=https://api.adp.com
PAYROLL_API_KEY=your-api-key
```

### Location Configuration

#### Geofence Setup
```json
{
  "location_id": 1,
  "name": "Downtown Store",
  "address": "123 Main St, Los Angeles, CA 90012",
  "latitude": 34.0522,
  "longitude": -118.2437,
  "geofence_radius": 100.0
}
```

#### Schedule Configuration
```json
{
  "employee_id": 1,
  "date": "2024-01-15",
  "start_time": "09:00:00",
  "end_time": "17:00:00",
  "break_duration": 30,
  "is_holiday": false
}
```

## Testing Compliance

### Automated Tests

#### Overtime Calculation Tests
```python
def test_daily_overtime_calculation():
    # Test 8+ hour overtime
    # Test 12+ hour overtime
    # Test 7th consecutive day
    # Test 16+ hour special rule

def test_grace_period_compliance():
    # Test within grace period
    # Test outside grace period
    # Test manager approval workflow

def test_holiday_allocation():
    # Test automatic allocation
    # Test eligibility requirements
    # Test manager override
```

#### Compliance Validation Tests
```python
def test_california_labor_code_compliance():
    # Test §510 compliance
    # Test §554 compliance
    # Test AB 1522 compliance

def test_audit_trail_requirements():
    # Test 4-year retention
    # Test change tracking
    # Test data integrity
```

### Manual Testing Checklist

#### Time Tracking
- [ ] Web punch functionality
- [ ] Mobile app geofencing
- [ ] Biometric terminal integration
- [ ] Grace period validation
- [ ] Exception handling

#### Overtime Calculation
- [ ] Daily overtime rules
- [ ] Weekly overtime rules
- [ ] 7th consecutive day
- [ ] 16+ hour special rule
- [ ] Rate hierarchy enforcement

#### Holiday Management
- [ ] Automatic allocation
- [ ] Eligibility calculation
- [ ] Manager override
- [ ] Audit trail

#### Compliance Reporting
- [ ] Weekly summary reports
- [ ] Overtime breakdown
- [ ] Holiday tracking
- [ ] Export functionality

## Deployment

### Production Checklist

#### Security
- [ ] SSL certificates configured
- [ ] Database encryption enabled
- [ ] API authentication implemented
- [ ] Audit logging enabled
- [ ] Backup procedures established

#### Compliance
- [ ] California timezone configured
- [ ] Grace period settings verified
- [ ] Geofence radius configured
- [ ] Audit retention policy set
- [ ] Payroll integration tested

#### Monitoring
- [ ] Compliance violation alerts
- [ ] Overtime threshold monitoring
- [ ] System health checks
- [ ] Performance monitoring
- [ ] Error tracking

### Integration

#### Payroll Systems
- **ADP**: REST API integration
- **UKG**: XML export format
- **Oracle Cloud**: JSON API integration

#### HRIS Systems
- **Employee data sync**: REST API
- **Schedule import**: CSV/XML
- **Compliance reporting**: Automated exports

## Support

### Documentation
- API documentation: `/docs`
- Compliance guide: This document
- User manual: `/docs/user-manual.md`
- Admin guide: `/docs/admin-guide.md`

### Contact
- Technical support: support@timeattendance.com
- Compliance questions: compliance@timeattendance.com
- Emergency: 1-800-TIME-ATT

### Updates
- Regular compliance updates
- California law changes
- System enhancements
- Security patches