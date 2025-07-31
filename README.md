# Time & Attendance System - California Retail

A comprehensive workforce management solution for retail contingent workers in California, featuring automated time tracking, California-compliant overtime calculations, paid holiday management, and full compliance reporting.

## 🎯 Features

- **Multi-Modal Time Tracking**: Web punch, mobile app (geo-fenced), biometric terminals
- **California Overtime Compliance**: Daily overtime (8h/12h rules), 7th consecutive day, 16+ hour shifts
- **Paid Holiday Management**: Automatic allocation with admin override capabilities
- **Compliance Reporting**: California Labor Code §510, §554, AB 1522 compliance
- **Manager Dashboard**: Timesheet approval, exception alerts, overtime monitoring
- **Audit Trail**: 4-year retention with full change tracking

## 🛠 Tech Stack

- **Backend**: FastAPI + PostgreSQL + Redis
- **Frontend**: React + TypeScript + TailwindCSS
- **Mobile**: React Native with geofencing
- **Compliance**: California Labor Code integration
- **Deployment**: Docker + containerized services

## 📁 Project Structure

```
/
├── backend/          # FastAPI backend with compliance engine
├── frontend/         # React web application
├── mobile/           # React Native mobile app
├── compliance/       # California labor law compliance engine
├── docker/          # Docker configurations
└── docs/            # Documentation and compliance guides
```

## 🚀 Getting Started

1. Clone the repository
2. Install dependencies: `./scripts/setup.sh`
3. Run with Docker: `docker-compose up`
4. Access the application at `http://localhost:3000`

## 📊 Key Features

- **Work Schedule**: 4 days/week, 8 hours minimum per shift
- **Grace Period**: 5-minute clock-in/out window
- **Overtime Rules**: California daily overtime + 16+ hour special rule
- **Holiday Allocation**: 1 paid holiday/week for 4+ shifts
- **Compliance**: Full California Labor Code adherence
- **Audit Trail**: 4-year retention with approval workflows