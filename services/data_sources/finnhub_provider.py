"""
Finnhub Data Provider (Stub)

Finnhub provides:
- Real-time quotes
- Company news
- Earnings calendars
- Social sentiment

API: https://finnhub.io/
Pricing: Free tier (60 calls/minute)

Author: ARK Trading Intelligence
Version: 1.0.0 (Stub)
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime

from .base_provider import (
    BaseDataProvider, Quote, Bar, News, TimeFrame
)

logger = logging.getLogger(__name__)


class FinnhubProvider(BaseDataProvider):
    """
    Finnhub data provider (STUB).
    
    Free tier: 60 calls/minute
    Good for: News, sentiment, earnings
    """
    
    def __init__(self, api_key: str):
        super().__init__("finnhub", api_key)
        logger.info("FinnhubProvider created (STUB - not yet implemented)")
    
    async def initialize(self) -> bool:
        logger.warning("Finnhub provider is a stub - not implemented yet")
        return False
    
    async def get_quote(self, symbol: str) -> Optional[Quote]:
        logger.warning("Finnhub get_quote not implemented")
        return None
    
    async def get_bars(self, symbol: str, timeframe: TimeFrame = TimeFrame.DAY_1,
                      start: Optional[datetime] = None, end: Optional[datetime] = None,
                      limit: int = 100) -> List[Bar]:
        logger.warning("Finnhub get_bars not implemented")
        return []
    
    async def get_news(self, symbol: Optional[str] = None, limit: int = 10) -> List[News]:
        logger.warning("Finnhub get_news not implemented")
        return []
    
    async def search_symbols(self, query: str, limit: int = 10) -> List[Dict[str, str]]:
        logger.warning("Finnhub search_symbols not implemented")
        return []
