# Real-time Financial Analytics Platform - Windows Setup Script
# Run this script in PowerShell to set up the entire project

param(
    [Parameter()]
    [ValidateSet('setup', 'clean', 'restart', 'logs', 'status')]
    [string]$Action = 'setup',
    
    [Parameter()]
    [string]$Service = ""
)

# Colors for output
$colors = @{
    Red = "Red"
    Green = "Green"  
    Yellow = "Yellow"
    Blue = "Blue"
}

function Write-Status {
    param($Message)
    Write-Host "[INFO] $Message" -ForegroundColor $colors.Blue
}

function Write-Success {
    param($Message)
    Write-Host "[SUCCESS] $Message" -ForegroundColor $colors.Green
}

function Write-Warning {
    param($Message)
    Write-Host "[WARNING] $Message" -ForegroundColor $colors.Yellow
}

function Write-Error {
    param($Message)
    Write-Host "[ERROR] $Message" -ForegroundColor $colors.Red
}

function Check-Prerequisites {
    Write-Status "Checking prerequisites..."
    
    # Check Docker
    try {
        $dockerVersion = docker --version
        Write-Success "Docker found: $dockerVersion"
    }
    catch {
        Write-Error "Docker is not installed. Please install Docker Desktop first."
        exit 1
    }
    
    # Check Docker Compose
    try {
        $composeVersion = docker-compose --version
        Write-Success "Docker Compose found: $composeVersion"
    }
    catch {
        Write-Error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    }
    
    Write-Success "Prerequisites check passed"
}

function Setup-Environment {
    Write-Status "Setting up environment..."
    
    if (-not (Test-Path ".env")) {
        Copy-Item ".env.example" ".env"
        Write-Success "Environment file created (.env)"
        Write-Warning "Please edit .env file with your API keys and configuration"
    }
    else {
        Write-Warning ".env file already exists, skipping..."
    }
}

function Start-Services {
    Write-Status "Building and starting services..."
    
    # Pull base images first
    docker-compose pull
    
    # Build custom images
    docker-compose build
    
    # Start services in detached mode
    docker-compose up -d
    
    Write-Success "All services started successfully"
}

function Wait-ForServices {
    Write-Status "Waiting for services to be ready..."
    
    # Wait for database
    Write-Status "Waiting for TimescaleDB..."
    do {
        Start-Sleep -Seconds 2
        Write-Host "." -NoNewline
        $dbReady = docker-compose exec -T timescaledb pg_isready -U postgres 2>$null
    } while ($LASTEXITCODE -ne 0)
    Write-Host ""
    
    # Wait for Kafka
    Write-Status "Waiting for Kafka..."
    Start-Sleep -Seconds 10
    
    # Wait for backend
    Write-Status "Waiting for backend API..."
    do {
        Start-Sleep -Seconds 2
        Write-Host "." -NoNewline
        try {
            $response = Invoke-WebRequest -Uri "http://localhost:8000/health" -UseBasicParsing -ErrorAction SilentlyContinue
            $backendReady = $response.StatusCode -eq 200
        }
        catch {
            $backendReady = $false
        }
    } while (-not $backendReady)
    Write-Host ""
    
    Write-Success "All services are ready!"
}

function Show-ServicesInfo {
    Write-Success "🎉 Setup completed successfully!"
    Write-Host ""
    Write-Host "📊 Access your services:"
    Write-Host "  🌐 Dashboard:      http://localhost:3000" -ForegroundColor Cyan
    Write-Host "  🔧 API Docs:       http://localhost:8000/docs" -ForegroundColor Cyan
    Write-Host "  📈 Grafana:        http://localhost:3001 (admin/admin)" -ForegroundColor Cyan
    Write-Host "  🔍 Prometheus:     http://localhost:9090" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "📝 Useful commands:"
    Write-Host "  🔍 Check logs:     docker-compose logs -f [service-name]"
    Write-Host "  📊 Check status:   docker-compose ps"
    Write-Host "  🛑 Stop services:  docker-compose down"
    Write-Host "  🗑️ Clean up:       docker-compose down -v"
    Write-Host ""
    Write-Host "🚀 Your real-time financial analytics platform is now running!" -ForegroundColor Green
}

function Stop-Services {
    Write-Status "Stopping services..."
    docker-compose down
    Write-Success "Services stopped"
}

function Show-Logs {
    if ($Service) {
        docker-compose logs -f $Service
    }
    else {
        docker-compose logs -f
    }
}

function Show-Status {
    docker-compose ps
}

function Main-Setup {
    Write-Host "===============================================" -ForegroundColor Magenta
    Write-Host "🏦 Real-time Financial Analytics Platform" -ForegroundColor Magenta
    Write-Host "===============================================" -ForegroundColor Magenta
    Write-Host ""
    
    Check-Prerequisites
    Setup-Environment
    Start-Services
    Wait-ForServices
    Show-ServicesInfo
}

# Main script logic
switch ($Action) {
    'setup' {
        Main-Setup
    }
    'clean' {
        Stop-Services
        Write-Success "Cleanup completed"
    }
    'restart' {
        Stop-Services
        Start-Sleep -Seconds 5
        Main-Setup
    }
    'logs' {
        Show-Logs
    }
    'status' {
        Show-Status
    }
    default {
        Write-Host "Usage: .\setup.ps1 [-Action {setup|clean|restart|logs|status}] [-Service service-name]"
        Write-Host ""
        Write-Host "Commands:"
        Write-Host "  setup     - Setup and start the entire platform (default)"
        Write-Host "  clean     - Stop all services and clean up"
        Write-Host "  restart   - Clean up and restart everything"
        Write-Host "  logs      - Show logs for all services or specific service"
        Write-Host "  status    - Show status of all services"
        Write-Host ""
        Write-Host "Examples:"
        Write-Host "  .\setup.ps1                        # Setup the platform"
        Write-Host "  .\setup.ps1 -Action logs           # Show all logs"
        Write-Host "  .\setup.ps1 -Action logs -Service backend  # Show backend logs only"
        Write-Host "  .\setup.ps1 -Action clean          # Stop and cleanup"
    }
}