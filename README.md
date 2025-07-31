# Bayer IT Partner Ecosystem Portal

A comprehensive, secure platform for managing IT vendor partnerships, feedback, and analytics for Bayer's IT organization. This application enables Bayer IT buying managers to view, assess, and collaborate with staffing/SOW/nearshore/offshore vendors in a centralized and structured way.

## 🎯 Features

### Core Functionality
- **Partner Directory & Tiering**: Categorized partner management with advanced filtering
- **Vendor Profile Management**: Self-service profile updates and capability management
- **Feedback System**: Structured rating and feedback collection with analytics
- **Dashboard & Analytics**: Real-time KPIs and performance metrics
- **Role-Based Access Control**: Secure access for different user types
- **Document Management**: File upload and management for vendors

### User Roles
- **Super Admin**: System-level configuration and oversight
- **Admin (Bayer IT)**: Portal management and user access control
- **IT Manager/Buyer**: Partner evaluation and feedback submission
- **Vendor/Partner**: Profile management and document uploads

### Advanced Features
- **Partner Performance Tracker**: Automated scorecards and risk indicators
- **Recommendation Engine**: Smart vendor suggestions based on requirements
- **Engagement Tracking**: Project history and outcome monitoring
- **Quarterly Review Prep**: Automated report generation for QBRs
- **Audit & Compliance**: Complete audit trail and exportable logs

## 🛠 Tech Stack

### Backend
- **Framework**: FastAPI + Python 3.11+
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Authentication**: JWT tokens with role-based access control
- **File Storage**: Local file system with secure upload handling
- **API Documentation**: Auto-generated OpenAPI/Swagger docs

### Frontend
- **Framework**: React 18 + TypeScript
- **Styling**: Tailwind CSS with custom components
- **State Management**: React Query for server state
- **Routing**: React Router v6 with protected routes
- **UI Components**: Heroicons + custom design system

### Infrastructure
- **Containerization**: Docker + Docker Compose
- **Development**: Hot reload for both frontend and backend
- **Production Ready**: Scalable architecture for enterprise deployment

## 📁 Project Structure

```
/
├── backend/                 # FastAPI backend
│   ├── app/
│   │   ├── api/            # API routes
│   │   ├── core/           # Configuration and auth
│   │   ├── database/       # Database models and connection
│   │   └── schemas/        # Pydantic schemas
│   ├── requirements.txt    # Python dependencies
│   └── Dockerfile         # Backend container
├── frontend/               # React frontend
│   ├── src/
│   │   ├── components/     # Reusable UI components
│   │   ├── pages/          # Page components
│   │   ├── contexts/       # React contexts
│   │   ├── services/       # API services
│   │   └── types/          # TypeScript types
│   ├── package.json        # Node.js dependencies
│   └── Dockerfile         # Frontend container
├── docker-compose.yml      # Development environment
└── README.md              # This file
```

## 🚀 Getting Started

### Prerequisites
- Docker and Docker Compose
- Node.js 18+ (for development)
- Python 3.11+ (for development)

### Quick Start
1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd bayer-partner-ecosystem
   ```

2. **Start the application**
   ```bash
   docker-compose up -d
   ```

3. **Access the application**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs

4. **Default credentials**
   - Email: `admin@bayer.com`
   - Password: `admin123`

### Development Setup

#### Backend Development
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### Frontend Development
```bash
cd frontend
npm install
npm start
```

## 📊 Key Metrics & Capabilities

### Partner Management
- **Tier Classification**: Strategic, Preferred, Niche partners
- **Service Types**: Staffing, SOW, Nearshore, Offshore, Specialized
- **Geographic Coverage**: Multi-region support with filtering
- **Capability Tracking**: Technology domains, tools, and platforms

### Feedback & Analytics
- **Rating System**: 1-10 scale across 5 key dimensions
- **Trend Analysis**: Performance tracking over time
- **Risk Alerts**: Automated identification of underperforming partners
- **Export Capabilities**: PDF and Excel report generation

### Security & Compliance
- **Role-Based Access**: Granular permissions per user type
- **Audit Logging**: Complete activity tracking
- **Data Encryption**: Secure storage and transmission
- **Compliance Ready**: SOC2, ISO, and other certification support

## 🔧 Configuration

### Environment Variables
Create a `.env` file in the backend directory:

```env
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/bayer_partner_ecosystem

# Security
SECRET_KEY=your-secret-key-change-in-production
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Azure AD (for production)
AZURE_CLIENT_ID=your-azure-client-id
AZURE_CLIENT_SECRET=your-azure-client-secret
AZURE_TENANT_ID=your-azure-tenant-id

# File Upload
MAX_FILE_SIZE=10485760  # 10MB
UPLOAD_DIR=uploads
```

### Database Setup
The application automatically creates tables and initial data on first run. For production:

```bash
# Run database migrations
alembic upgrade head

# Create initial admin user
python -c "from app.database.database import init_db; import asyncio; asyncio.run(init_db())"
```

## 🚀 Deployment

### Production Deployment
1. **Update environment variables** for production settings
2. **Configure database** with production PostgreSQL instance
3. **Set up reverse proxy** (nginx) for SSL termination
4. **Configure Azure AD** for enterprise SSO
5. **Deploy with Docker** or your preferred container orchestration

### Azure Deployment
The application is designed for Azure deployment with:
- Azure App Service for hosting
- Azure Database for PostgreSQL
- Azure AD for authentication
- Azure Blob Storage for file uploads (optional)

## 📈 Monitoring & Analytics

### Built-in Analytics
- Partner performance trends
- Feedback submission rates
- Profile completion metrics
- User engagement tracking

### Integration Capabilities
- Power BI for advanced analytics
- ServiceNow for project integration
- JIRA for development tracking
- Email notifications for alerts

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is proprietary software developed for Bayer AG. All rights reserved.

## 🆘 Support

For technical support or questions:
- Create an issue in the repository
- Contact the development team
- Check the API documentation at `/docs`

---

**Bayer IT Partner Ecosystem Portal** - Empowering strategic vendor partnerships through data-driven insights and collaborative management.