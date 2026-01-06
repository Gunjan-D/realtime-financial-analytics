#!/bin/bash

# Real-time Financial Analytics Platform - Setup Script
# This script sets up the entire project for development or production

set -e

echo "🚀 Setting up Real-time Financial Analytics Platform..."

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

# Check prerequisites
check_prerequisites() {
    print_status "Checking prerequisites..."
    
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi
    
    print_success "Prerequisites check passed"
}

# Setup environment
setup_environment() {
    print_status "Setting up environment..."
    
    if [ ! -f .env ]; then
        cp .env.example .env
        print_success "Environment file created (.env)"
        print_warning "Please edit .env file with your API keys and configuration"
    else
        print_warning ".env file already exists, skipping..."
    fi
}

# Build and start services
start_services() {
    print_status "Building and starting services..."
    
    # Pull base images first
    docker-compose pull
    
    # Build custom images
    docker-compose build
    
    # Start services in detached mode
    docker-compose up -d
    
    print_success "All services started successfully"
}

# Wait for services to be healthy
wait_for_services() {
    print_status "Waiting for services to be ready..."
    
    # Wait for database
    print_status "Waiting for TimescaleDB..."
    until docker-compose exec -T timescaledb pg_isready -U postgres > /dev/null 2>&1; do
        echo -n "."
        sleep 2
    done
    
    # Wait for Kafka
    print_status "Waiting for Kafka..."
    sleep 10
    
    # Wait for backend
    print_status "Waiting for backend API..."
    until curl -f http://localhost:8000/health > /dev/null 2>&1; do
        echo -n "."
        sleep 2
    done
    
    print_success "All services are ready!"
}

# Display service information
show_services_info() {
    print_success "🎉 Setup completed successfully!"
    echo ""
    echo "📊 Access your services:"
    echo "  🌐 Dashboard:      http://localhost:3000"
    echo "  🔧 API Docs:       http://localhost:8000/docs"
    echo "  📈 Grafana:        http://localhost:3001 (admin/admin)"
    echo "  🔍 Prometheus:     http://localhost:9090"
    echo ""
    echo "📝 Useful commands:"
    echo "  🔍 Check logs:     docker-compose logs -f [service-name]"
    echo "  📊 Check status:   docker-compose ps"
    echo "  🛑 Stop services:  docker-compose down"
    echo "  🗑️ Clean up:       docker-compose down -v"
    echo ""
    echo "🚀 Your real-time financial analytics platform is now running!"
}

# Cleanup function
cleanup() {
    print_status "Stopping services..."
    docker-compose down
    print_success "Cleanup completed"
}

# Main setup function
main() {
    echo "================================================"
    echo "🏦 Real-time Financial Analytics Platform"
    echo "================================================"
    echo ""
    
    check_prerequisites
    setup_environment
    start_services
    wait_for_services
    show_services_info
}

# Handle script arguments
case "${1:-setup}" in
    setup)
        main
        ;;
    clean)
        cleanup
        ;;
    restart)
        cleanup
        sleep 5
        main
        ;;
    logs)
        docker-compose logs -f "${2:-}"
        ;;
    status)
        docker-compose ps
        ;;
    *)
        echo "Usage: $0 {setup|clean|restart|logs [service]|status}"
        echo ""
        echo "Commands:"
        echo "  setup     - Setup and start the entire platform (default)"
        echo "  clean     - Stop all services and clean up"
        echo "  restart   - Clean up and restart everything"
        echo "  logs      - Show logs for all services or specific service"
        echo "  status    - Show status of all services"
        exit 1
        ;;
esac