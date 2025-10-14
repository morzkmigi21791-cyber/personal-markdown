# Site of Sites

A platform for hosting static websites with project management and file handling capabilities.

## 🚀 Quick Start

### Using Docker (Recommended)
```bash
# Start all services
start.bat
# Choose option [1] for Docker Full Stack

# Stop all services
stop.bat
```

### Using Development Mode
```bash
# Start services
start.bat
# Choose option [2] for Development Mode
```

## 🔧 Troubleshooting

### Fix Common Issues
```bash
# Fix all common issues (proxy errors, database, etc.)
fix.bat
```

### View Logs
```bash
# View service logs
logs.bat
```

## 📁 Project Structure

- `start.bat` - Universal startup script
- `stop.bat` - Universal stop script
- `fix.bat` - Fix common issues
- `logs.bat` - View service logs
- `docker-compose.full.yml` - Full Docker stack
- `docker-compose.yml` - Basic infrastructure
- `backend/` - FastAPI backend
- `frontend/` - React frontend
- `nginx/` - Nginx configuration

## 🌐 Services

- **Main Site**: http://localhost
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **MinIO Console**: http://localhost:9001

## 🔑 Default Credentials

- **MinIO**: Qwerty / 19216811!
- **PostgreSQL**: postgres / Sctorlorn25565

## 🛠️ Features

✅ **User Authentication** - Registration and login with JWT tokens  
✅ **Project Management** - Create and manage static website projects  
✅ **File Hosting** - Upload and manage files with MinIO S3 storage  
✅ **Site Hosting** - Host static websites with custom subdomains  
✅ **User Profiles** - User profiles with search functionality  
✅ **Responsive Design** - Modern UI with React components  

## 🔧 Development

### Backend (FastAPI)
- Python 3.11+
- PostgreSQL database
- MinIO S3 storage
- JWT authentication
- SQLAlchemy ORM

### Frontend (React)
- React 18
- Axios for API calls
- CSS styling
- Modal components
- Router navigation

### Infrastructure
- Docker & Docker Compose
- Nginx reverse proxy
- PostgreSQL database
- MinIO S3 storage