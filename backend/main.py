"""
FastAPI Backend for Real-time Financial Analytics Platform
"""

import json
import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, HTTPException, Depends, WebSocket, WebSocketDisconnect, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import redis
from sqlalchemy import create_engine, text
import pandas as pd
from loguru import logger
import os
from pydantic import BaseModel


# Pydantic models
class StockData(BaseModel):
    symbol: str
    price: float
    volume: int
    timestamp: datetime
    change: float
    change_percent: float
    high: float
    low: float
    open: float
    previous_close: float


class MarketSummary(BaseModel):
    total_symbols: int
    avg_change_percent: float
    gainers: List[Dict[str, Any]]
    losers: List[Dict[str, Any]]
    most_active: List[Dict[str, Any]]
    market_cap_change: float


class Portfolio(BaseModel):
    user_id: str
    symbols: List[str]
    positions: Dict[str, Dict[str, Any]]


# FastAPI app
app = FastAPI(
    title="Real-time Financial Analytics API",
    description="API for real-time stock market data and analytics",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global variables
redis_client = None
db_engine = None


@app.on_event("startup")
async def startup_event():
    """Initialize connections on startup"""
    global redis_client, db_engine
    
    # Redis connection
    redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')
    redis_client = redis.from_url(redis_url)
    
    # Database connection
    database_url = os.getenv('DATABASE_URL')
    if database_url:
        db_engine = create_engine(database_url)
    
    logger.info("Backend services initialized")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    if redis_client:
        redis_client.close()
    logger.info("Backend services shut down")


# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except:
                # Remove broken connections
                self.disconnect(connection)


manager = ConnectionManager()


# API Endpoints
@app.get("/")
async def root():
    return {"message": "Real-time Financial Analytics API", "status": "running"}


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    health_status = {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "services": {
            "redis": "connected" if redis_client and redis_client.ping() else "disconnected",
            "database": "connected" if db_engine else "not configured"
        }
    }
    return health_status


@app.get("/api/v1/stocks/{symbol}")
async def get_stock_data(symbol: str):
    """Get latest data for a specific stock"""
    try:
        cache_key = f"latest:{symbol.upper()}"
        cached_data = redis_client.get(cache_key)
        
        if cached_data:
            data = json.loads(cached_data)
            return {
                "symbol": symbol.upper(),
                **data
            }
        else:
            raise HTTPException(status_code=404, detail=f"No data found for {symbol}")
            
    except Exception as e:
        logger.error(f"Error fetching stock data for {symbol}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/api/v1/stocks")
async def get_all_stocks():
    """Get latest data for all tracked stocks"""
    try:
        stocks_data = []
        
        # Get all keys matching the pattern
        keys = redis_client.keys("latest:*")
        
        for key in keys:
            try:
                symbol = key.decode().replace("latest:", "")
                cached_data = redis_client.get(key)
                
                if cached_data:
                    data = json.loads(cached_data)
                    stocks_data.append({
                        "symbol": symbol,
                        **data
                    })
            except Exception as e:
                logger.error(f"Error processing key {key}: {str(e)}")
                continue
        
        # Sort by change percent (descending)
        stocks_data.sort(key=lambda x: x.get('change_percent', 0), reverse=True)
        
        return {
            "stocks": stocks_data,
            "total": len(stocks_data),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error fetching all stocks data: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/api/v1/market/summary")
async def get_market_summary():
    """Get market summary statistics"""
    try:
        # Get all stocks data
        stocks_response = await get_all_stocks()
        stocks = stocks_response["stocks"]
        
        if not stocks:
            raise HTTPException(status_code=404, detail="No market data available")
        
        # Calculate market statistics
        total_symbols = len(stocks)
        avg_change = sum(stock.get('change_percent', 0) for stock in stocks) / total_symbols
        
        # Top gainers and losers
        gainers = sorted(stocks, key=lambda x: x.get('change_percent', 0), reverse=True)[:5]
        losers = sorted(stocks, key=lambda x: x.get('change_percent', 0))[:5]
        
        # Most active by volume
        most_active = sorted(stocks, key=lambda x: x.get('volume', 0), reverse=True)[:5]
        
        summary = {
            "total_symbols": total_symbols,
            "avg_change_percent": round(avg_change, 2),
            "gainers": gainers,
            "losers": losers,
            "most_active": most_active,
            "market_sentiment": "bullish" if avg_change > 0 else "bearish",
            "timestamp": datetime.now().isoformat()
        }
        
        return summary
        
    except Exception as e:
        logger.error(f"Error generating market summary: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/api/v1/stocks/{symbol}/history")
async def get_stock_history(symbol: str, days: int = 7):
    """Get historical data for a stock"""
    try:
        if not db_engine:
            raise HTTPException(status_code=503, detail="Database not configured")
        
        query = text("""
            SELECT symbol, price, volume, timestamp, change, change_percent,
                   high, low, open, previous_close
            FROM stock_data_processed 
            WHERE symbol = :symbol 
            AND timestamp >= NOW() - INTERVAL ':days days'
            ORDER BY timestamp DESC
            LIMIT 1000
        """)
        
        with db_engine.connect() as conn:
            result = conn.execute(query, {"symbol": symbol.upper(), "days": days})
            history = [dict(row._mapping) for row in result]
        
        return {
            "symbol": symbol.upper(),
            "history": history,
            "total_records": len(history)
        }
        
    except Exception as e:
        logger.error(f"Error fetching history for {symbol}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.post("/api/v1/alerts")
async def create_alert(alert_data: Dict[str, Any]):
    """Create a price alert"""
    try:
        # Store alert in Redis with expiration
        alert_key = f"alert:{alert_data['symbol']}:{alert_data['user_id']}"
        redis_client.setex(alert_key, 86400, json.dumps(alert_data))  # 24 hours
        
        return {"message": "Alert created successfully", "alert_id": alert_key}
        
    except Exception as e:
        logger.error(f"Error creating alert: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


# WebSocket endpoint for real-time updates
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    
    try:
        while True:
            # Send periodic updates to connected clients
            await asyncio.sleep(5)  # Update every 5 seconds
            
            try:
                # Get latest market data
                stocks_response = await get_all_stocks()
                message = json.dumps({
                    "type": "market_update",
                    "data": stocks_response,
                    "timestamp": datetime.now().isoformat()
                })
                
                await manager.send_personal_message(message, websocket)
                
            except Exception as e:
                logger.error(f"Error sending WebSocket update: {str(e)}")
                break
                
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        logger.info("WebSocket client disconnected")


# Background task for monitoring alerts
async def monitor_alerts():
    """Background task to monitor price alerts"""
    while True:
        try:
            # Get all alert keys
            alert_keys = redis_client.keys("alert:*")
            
            for key in alert_keys:
                try:
                    alert_data = json.loads(redis_client.get(key))
                    symbol = alert_data['symbol']
                    target_price = alert_data['target_price']
                    condition = alert_data['condition']  # 'above' or 'below'
                    
                    # Get current price
                    current_data = redis_client.get(f"latest:{symbol}")
                    if current_data:
                        current_price = json.loads(current_data)['price']
                        
                        # Check alert condition
                        triggered = False
                        if condition == 'above' and current_price >= target_price:
                            triggered = True
                        elif condition == 'below' and current_price <= target_price:
                            triggered = True
                        
                        if triggered:
                            # Send alert notification
                            alert_message = {
                                "type": "alert",
                                "symbol": symbol,
                                "current_price": current_price,
                                "target_price": target_price,
                                "condition": condition,
                                "timestamp": datetime.now().isoformat()
                            }
                            
                            await manager.broadcast(json.dumps(alert_message))
                            
                            # Remove the triggered alert
                            redis_client.delete(key)
                            logger.info(f"Alert triggered for {symbol} at ${current_price}")
                
                except Exception as e:
                    logger.error(f"Error processing alert {key}: {str(e)}")
            
            await asyncio.sleep(10)  # Check every 10 seconds
            
        except Exception as e:
            logger.error(f"Error in alert monitoring: {str(e)}")
            await asyncio.sleep(30)


# Start background tasks
@app.on_event("startup")
async def start_background_tasks():
    asyncio.create_task(monitor_alerts())


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)