"""
Main entry point for data ingestion service
"""

import asyncio
import os
from loguru import logger
from stock_producer import main as stock_main


async def run_all_producers():
    """Run all data producers concurrently"""
    logger.info("Starting all data producers...")
    
    tasks = [
        stock_main(),
        # Add other producers here (news, crypto, etc.)
    ]
    
    await asyncio.gather(*tasks)


if __name__ == "__main__":
    logger.info("Starting Data Ingestion Service...")
    asyncio.run(run_all_producers())