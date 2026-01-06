# Quick Start Guide

## Prerequisites

1. **Docker & Docker Compose** - [Install Docker](https://docs.docker.com/get-docker/)
2. **Git** - [Install Git](https://git-scm.com/downloads)
3. **Alpha Vantage API Key** (Optional, but recommended for real data)
   - Sign up at [Alpha Vantage](https://www.alphavantage.co/support/#api-key)
   - Free tier allows 5 API calls per minute

## 🚀 Getting Started in 5 Minutes

### 1. Clone the Repository
```bash
git clone https://github.com/yourusername/realtime-financial-analytics.git
cd realtime-financial-analytics
```

### 2. Configure Environment
```bash
# Copy the example environment file
cp .env.example .env

# Edit the .env file with your API key (optional)
# For demo purposes, you can use mock data without an API key
```

### 3. Start the Application
```bash
# Start all services
docker-compose up -d

# Check if all services are running
docker-compose ps
```

### 4. Access the Application

**🎯 Main Dashboard**: http://localhost:3000
- Real-time stock price tracking
- Interactive charts and visualizations
- Market sentiment analysis

**📚 API Documentation**: http://localhost:8000/docs
- Complete API documentation
- Interactive API testing

**📊 Monitoring Dashboard**: http://localhost:3001
- Grafana dashboards (admin/admin)
- System performance metrics

## 🔧 Development Mode

### Backend Development
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

### Frontend Development
```bash
cd frontend
npm install
npm start
```

### Stream Processor Development
```bash
cd stream-processor
pip install -r requirements.txt
python main.py
```

## 📊 What You'll See

1. **Real-time Stock Prices**: Live updates every 5 seconds
2. **Interactive Charts**: Click on any stock to view its price history
3. **Market Summary**: Top gainers, losers, and most active stocks
4. **WebSocket Connection**: Live indicator showing real-time connection status

## 🛠️ Troubleshooting

### Common Issues

**Services not starting?**
```bash
# Check Docker is running
docker --version
docker-compose --version

# Check logs for any service
docker-compose logs [service-name]
```

**No data showing?**
- Wait 30-60 seconds for data ingestion to start
- Check the WebSocket connection indicator
- Mock data is used by default if no API key is provided

**Port conflicts?**
- Edit `docker-compose.yml` to change port mappings
- Default ports: 3000 (frontend), 8000 (backend), 3001 (Grafana)

### Stop the Application
```bash
# Stop all services
docker-compose down

# Stop and remove all data
docker-compose down -v
```

## 📈 Next Steps

1. **Customize the Dashboard**: Modify React components in `/frontend/src`
2. **Add New Data Sources**: Extend the data ingestion service
3. **Implement Alerts**: Use the alerts API to set price notifications
4. **Scale the System**: Deploy to Kubernetes for production use

## 🎯 Key Features Demonstrated

- **Real-time Data Pipeline**: Kafka → Spark → TimescaleDB
- **Modern Web Stack**: React + FastAPI + PostgreSQL
- **Containerization**: Full Docker orchestration
- **Monitoring**: Prometheus + Grafana integration
- **WebSocket Communication**: Live data updates
- **Time-series Database**: Optimized for financial data
- **REST API**: Comprehensive API with documentation

---

**Need Help?** Check the full documentation in `/docs` or open an issue on GitHub!