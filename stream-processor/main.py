"""
Real-time stream processing using PySpark
Processes stock data from Kafka and performs real-time analytics
"""

import json
import os
from datetime import datetime
from typing import Dict, Any, List
import pandas as pd
import numpy as np
from pyspark.sql import SparkSession
from pyspark.sql.functions import *
from pyspark.sql.types import *
from pyspark.sql.streaming import *
import redis
from loguru import logger
from sqlalchemy import create_engine, text
import ta


class StockStreamProcessor:
    """Real-time stream processor for stock data"""
    
    def __init__(self):
        self.kafka_servers = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092')
        self.database_url = os.getenv('DATABASE_URL')
        self.redis_client = redis.from_url(os.getenv('REDIS_URL', 'redis://localhost:6379'))
        
        # Initialize Spark Session
        self.spark = SparkSession.builder \
            .appName("FinancialStreamProcessor") \
            .config("spark.sql.streaming.checkpointLocation", "/tmp/checkpoint") \
            .config("spark.sql.streaming.stateStore.providerClass", 
                   "org.apache.spark.sql.execution.streaming.state.HDFSBackedStateStoreProvider") \
            .getOrCreate()
        
        self.spark.sparkContext.setLogLevel("WARN")
        
        # Database connection for writing processed data
        self.db_engine = create_engine(self.database_url) if self.database_url else None
        
        logger.info("Initialized StockStreamProcessor")

    def create_stock_schema(self) -> StructType:
        """Define the schema for stock data"""
        return StructType([
            StructField("symbol", StringType(), True),
            StructField("price", DoubleType(), True),
            StructField("volume", LongType(), True),
            StructField("timestamp", StringType(), True),
            StructField("change", DoubleType(), True),
            StructField("change_percent", DoubleType(), True),
            StructField("high", DoubleType(), True),
            StructField("low", DoubleType(), True),
            StructField("open", DoubleType(), True),
            StructField("previous_close", DoubleType(), True)
        ])

    def read_kafka_stream(self):
        """Read streaming data from Kafka"""
        kafka_df = self.spark \
            .readStream \
            .format("kafka") \
            .option("kafka.bootstrap.servers", self.kafka_servers) \
            .option("subscribe", "stock-prices") \
            .option("startingOffsets", "latest") \
            .option("failOnDataLoss", "false") \
            .load()
        
        # Parse JSON data
        stock_schema = self.create_stock_schema()
        
        parsed_df = kafka_df.select(
            col("key").cast("string").alias("symbol_key"),
            from_json(col("value").cast("string"), stock_schema).alias("data"),
            col("timestamp").alias("kafka_timestamp")
        ).select("symbol_key", "data.*", "kafka_timestamp")
        
        return parsed_df

    def calculate_technical_indicators(self, df):
        """Calculate technical indicators using windowing"""
        
        # Define window specification for each symbol
        window_spec = Window.partitionBy("symbol").orderBy("timestamp_dt")
        
        # Add technical indicators
        enhanced_df = df.withColumn(
            # Simple Moving Averages
            "sma_5", avg("price").over(window_spec.rowsBetween(-4, 0))
        ).withColumn(
            "sma_20", avg("price").over(window_spec.rowsBetween(-19, 0))
        ).withColumn(
            # Price volatility
            "volatility", stddev("price").over(window_spec.rowsBetween(-19, 0))
        ).withColumn(
            # Price momentum
            "momentum", col("price") - lag("price", 5).over(window_spec)
        ).withColumn(
            # Volume moving average
            "volume_ma", avg("volume").over(window_spec.rowsBetween(-9, 0))
        )
        
        return enhanced_df

    def detect_anomalies(self, df):
        """Detect price anomalies and unusual trading patterns"""
        
        window_spec = Window.partitionBy("symbol").orderBy("timestamp_dt")
        
        anomaly_df = df.withColumn(
            # Price anomaly: price is more than 3 standard deviations from mean
            "price_anomaly", 
            when(abs(col("price") - avg("price").over(window_spec.rowsBetween(-99, 0))) > 
                 3 * stddev("price").over(window_spec.rowsBetween(-99, 0)), True)
            .otherwise(False)
        ).withColumn(
            # Volume spike: volume is 5x the average
            "volume_spike",
            when(col("volume") > 5 * avg("volume").over(window_spec.rowsBetween(-19, 0)), True)
            .otherwise(False)
        ).withColumn(
            # Large price movement
            "large_movement",
            when(abs(col("change_percent")) > 5.0, True).otherwise(False)
        )
        
        return anomaly_df

    def aggregate_market_data(self, df):
        """Create market-wide aggregations"""
        
        # Market summary by time window
        market_summary = df.groupBy(
            window(col("timestamp_dt"), "1 minute")
        ).agg(
            avg("price").alias("avg_market_price"),
            sum("volume").alias("total_volume"),
            count("symbol").alias("active_symbols"),
            avg("change_percent").alias("avg_change_percent"),
            max("change_percent").alias("max_change_percent"),
            min("change_percent").alias("min_change_percent")
        )
        
        return market_summary

    def write_to_database(self, df, table_name: str):
        """Write processed data to TimescaleDB"""
        
        def write_batch(batch_df, batch_id):
            try:
                # Convert to Pandas for easier database operations
                pandas_df = batch_df.toPandas()
                
                if not pandas_df.empty:
                    pandas_df.to_sql(
                        table_name, 
                        self.db_engine, 
                        if_exists='append', 
                        index=False,
                        method='multi'
                    )
                    logger.info(f"Written {len(pandas_df)} records to {table_name}")
                    
            except Exception as e:
                logger.error(f"Error writing to database: {str(e)}")
        
        return df.writeStream \
            .foreachBatch(write_batch) \
            .option("checkpointLocation", f"/tmp/checkpoint/{table_name}") \
            .start()

    def cache_to_redis(self, df):
        """Cache latest data to Redis for fast API access"""
        
        def cache_batch(batch_df, batch_id):
            try:
                pandas_df = batch_df.toPandas()
                
                for _, row in pandas_df.iterrows():
                    # Cache latest price data
                    cache_key = f"latest:{row['symbol']}"
                    cache_data = {
                        'price': float(row['price']),
                        'change': float(row['change']),
                        'change_percent': float(row['change_percent']),
                        'volume': int(row['volume']),
                        'timestamp': str(row['timestamp'])
                    }
                    
                    self.redis_client.setex(
                        cache_key, 
                        300,  # 5 minutes expiry
                        json.dumps(cache_data)
                    )
                
                logger.info(f"Cached {len(pandas_df)} records to Redis")
                
            except Exception as e:
                logger.error(f"Error caching to Redis: {str(e)}")
        
        return df.writeStream \
            .foreachBatch(cache_batch) \
            .option("checkpointLocation", "/tmp/checkpoint/redis_cache") \
            .start()

    def start_processing(self):
        """Start the stream processing pipeline"""
        logger.info("Starting stream processing pipeline...")
        
        try:
            # Read from Kafka
            raw_stream = self.read_kafka_stream()
            
            # Convert timestamp to proper datetime
            processed_stream = raw_stream.withColumn(
                "timestamp_dt", 
                to_timestamp(col("timestamp"))
            ).withWatermark("timestamp_dt", "10 seconds")
            
            # Add technical indicators
            enhanced_stream = self.calculate_technical_indicators(processed_stream)
            
            # Detect anomalies
            anomaly_stream = self.detect_anomalies(enhanced_stream)
            
            # Write enhanced data to database
            if self.db_engine:
                db_writer = self.write_to_database(enhanced_stream, "stock_data_processed")
            
            # Cache to Redis
            redis_writer = self.cache_to_redis(enhanced_stream)
            
            # Create market aggregations
            market_data = self.aggregate_market_data(enhanced_stream)
            
            # Console output for debugging (can be removed in production)
            console_writer = enhanced_stream.select(
                "symbol", "price", "change_percent", "sma_5", "sma_20", "volume"
            ).writeStream \
                .outputMode("append") \
                .format("console") \
                .option("truncate", False) \
                .option("numRows", 5) \
                .trigger(processingTime='30 seconds') \
                .start()
            
            # Market summary console output
            market_console = market_data.writeStream \
                .outputMode("complete") \
                .format("console") \
                .option("truncate", False) \
                .trigger(processingTime='60 seconds') \
                .start()
            
            logger.info("Stream processing started successfully")
            
            # Keep the streams running
            streams = [redis_writer, console_writer, market_console]
            if self.db_engine:
                streams.append(db_writer)
                
            for stream in streams:
                stream.awaitTermination()
            
        except Exception as e:
            logger.error(f"Error in stream processing: {str(e)}")
            raise

    def stop_processing(self):
        """Stop all streams and cleanup"""
        logger.info("Stopping stream processing...")
        self.spark.stop()


def main():
    """Main function"""
    processor = StockStreamProcessor()
    
    try:
        processor.start_processing()
    except KeyboardInterrupt:
        logger.info("Received interrupt signal, shutting down...")
    finally:
        processor.stop_processing()


if __name__ == "__main__":
    main()