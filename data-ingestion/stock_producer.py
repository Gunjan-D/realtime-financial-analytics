"""
Real-time Stock Data Producer for Kafka
Fetches live stock data from Alpha Vantage API and publishes to Kafka
"""

import json
import time
import asyncio
import os
from datetime import datetime, timedelta
from typing import List, Dict, Any
import requests
from kafka import KafkaProducer
from loguru import logger
import redis
from pydantic import BaseModel


class StockData(BaseModel):
    """Stock data model"""
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


class StockDataProducer:
    """Producer for real-time stock data"""
    
    def __init__(self):
        self.kafka_servers = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092')
        self.api_key = os.getenv('ALPHA_VANTAGE_API_KEY')
        self.redis_client = redis.from_url(os.getenv('REDIS_URL', 'redis://localhost:6379'))
        
        # Initialize Kafka producer
        self.producer = KafkaProducer(
            bootstrap_servers=[self.kafka_servers],
            value_serializer=lambda x: json.dumps(x, default=str).encode('utf-8'),
            key_serializer=lambda x: x.encode('utf-8') if x else None,
            acks='all',
            retries=3,
            retry_backoff_ms=1000
        )
        
        # Stock symbols to track
        self.symbols = [
            'AAPL', 'GOOGL', 'MSFT', 'AMZN', 'TSLA',
            'NVDA', 'META', 'NFLX', 'AMD', 'INTC',
            'BABA', 'CRM', 'ADBE', 'ORCL', 'PYPL'
        ]
        
        self.topic = 'stock-prices'
        self.rate_limit_delay = 12  # Alpha Vantage allows 5 calls per minute (free tier)
        
        logger.info(f"Initialized StockDataProducer with {len(self.symbols)} symbols")

    def fetch_stock_data(self, symbol: str) -> Dict[str, Any]:
        """Fetch real-time stock data from Alpha Vantage"""
        try:
            url = f"https://www.alphavantage.co/query"
            params = {
                'function': 'GLOBAL_QUOTE',
                'symbol': symbol,
                'apikey': self.api_key
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            # Check for API error
            if 'Error Message' in data:
                logger.error(f"API error for {symbol}: {data['Error Message']}")
                return None
                
            if 'Note' in data:
                logger.warning(f"API rate limit hit: {data['Note']}")
                return None
            
            # Extract quote data
            quote = data.get('Global Quote', {})
            if not quote:
                logger.warning(f"No quote data for {symbol}")
                return None
            
            # Parse the data
            stock_data = {
                'symbol': quote.get('01. symbol', symbol),
                'price': float(quote.get('05. price', 0)),
                'volume': int(quote.get('06. volume', 0)),
                'timestamp': datetime.now().isoformat(),
                'change': float(quote.get('09. change', 0)),
                'change_percent': quote.get('10. change percent', '0%').replace('%', ''),
                'high': float(quote.get('03. high', 0)),
                'low': float(quote.get('04. low', 0)),
                'open': float(quote.get('02. open', 0)),
                'previous_close': float(quote.get('08. previous close', 0))
            }
            
            return stock_data
            
        except Exception as e:
            logger.error(f"Error fetching data for {symbol}: {str(e)}")
            return None

    def generate_mock_data(self, symbol: str) -> Dict[str, Any]:
        """Generate mock stock data for demo purposes"""
        import random
        
        # Get previous price from cache or use a base price
        cache_key = f"last_price:{symbol}"
        last_price = self.redis_client.get(cache_key)
        
        if last_price:
            last_price = float(last_price)
        else:
            # Base prices for different stocks
            base_prices = {
                'AAPL': 150.0, 'GOOGL': 2800.0, 'MSFT': 350.0, 
                'AMZN': 3200.0, 'TSLA': 800.0, 'NVDA': 450.0,
                'META': 300.0, 'NFLX': 400.0, 'AMD': 100.0, 
                'INTC': 50.0, 'BABA': 80.0, 'CRM': 200.0,
                'ADBE': 500.0, 'ORCL': 90.0, 'PYPL': 60.0
            }
            last_price = base_prices.get(symbol, 100.0)
        
        # Generate realistic price movement (-2% to +2%)
        change_percent = random.uniform(-2.0, 2.0)
        new_price = last_price * (1 + change_percent / 100)
        change = new_price - last_price
        
        # Cache the new price
        self.redis_client.setex(cache_key, 300, str(new_price))  # Cache for 5 minutes
        
        stock_data = {
            'symbol': symbol,
            'price': round(new_price, 2),
            'volume': random.randint(100000, 10000000),
            'timestamp': datetime.now().isoformat(),
            'change': round(change, 2),
            'change_percent': round(change_percent, 2),
            'high': round(new_price * random.uniform(1.0, 1.05), 2),
            'low': round(new_price * random.uniform(0.95, 1.0), 2),
            'open': round(last_price * random.uniform(0.99, 1.01), 2),
            'previous_close': round(last_price, 2)
        }
        
        return stock_data

    async def publish_stock_data(self):
        """Continuously fetch and publish stock data"""
        logger.info("Starting stock data publishing...")
        
        while True:
            try:
                for symbol in self.symbols:
                    # Use mock data if no API key is provided
                    if not self.api_key or self.api_key == 'your_alpha_vantage_api_key_here':
                        stock_data = self.generate_mock_data(symbol)
                        logger.info(f"Generated mock data for {symbol}: ${stock_data['price']}")
                    else:
                        stock_data = self.fetch_stock_data(symbol)
                        if not stock_data:
                            continue
                        logger.info(f"Fetched real data for {symbol}: ${stock_data['price']}")
                    
                    # Publish to Kafka
                    self.producer.send(
                        topic=self.topic,
                        key=symbol,
                        value=stock_data
                    )
                    
                    # Small delay between symbols to avoid overwhelming the system
                    await asyncio.sleep(1)
                
                # Flush producer to ensure all messages are sent
                self.producer.flush()
                
                # Wait before next batch (respect API rate limits)
                if self.api_key and self.api_key != 'your_alpha_vantage_api_key_here':
                    await asyncio.sleep(self.rate_limit_delay)
                else:
                    await asyncio.sleep(5)  # 5 seconds for mock data
                    
            except KeyboardInterrupt:
                logger.info("Shutting down producer...")
                break
            except Exception as e:
                logger.error(f"Error in publishing loop: {str(e)}")
                await asyncio.sleep(10)  # Wait before retrying
        
        self.producer.close()

    def publish_historical_data(self, symbol: str, days: int = 30):
        """Publish historical data for backtesting"""
        logger.info(f"Publishing historical data for {symbol} ({days} days)")
        
        try:
            url = f"https://www.alphavantage.co/query"
            params = {
                'function': 'TIME_SERIES_DAILY',
                'symbol': symbol,
                'outputsize': 'full',
                'apikey': self.api_key
            }
            
            response = requests.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            time_series = data.get('Time Series (Daily)', {})
            
            # Get last N days
            dates = sorted(time_series.keys(), reverse=True)[:days]
            
            for date in reversed(dates):  # Publish in chronological order
                day_data = time_series[date]
                
                historical_data = {
                    'symbol': symbol,
                    'price': float(day_data['4. close']),
                    'volume': int(day_data['5. volume']),
                    'timestamp': f"{date} 16:00:00",  # Market close time
                    'high': float(day_data['2. high']),
                    'low': float(day_data['3. low']),
                    'open': float(day_data['1. open']),
                    'is_historical': True
                }
                
                self.producer.send(
                    topic=f'{self.topic}-historical',
                    key=symbol,
                    value=historical_data
                )
                
                time.sleep(0.1)  # Small delay
            
            self.producer.flush()
            logger.info(f"Published {len(dates)} historical records for {symbol}")
            
        except Exception as e:
            logger.error(f"Error publishing historical data for {symbol}: {str(e)}")


async def main():
    """Main function to start the producer"""
    producer = StockDataProducer()
    
    # Optionally publish some historical data first
    # for symbol in producer.symbols[:3]:  # Just first 3 symbols for demo
    #     producer.publish_historical_data(symbol, days=7)
    
    # Start real-time data publishing
    await producer.publish_stock_data()


if __name__ == "__main__":
    asyncio.run(main())