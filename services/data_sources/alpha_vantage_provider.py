"""
Alpha Vantage Data Provider (Stub)

Alpha Vantage provides:
- Technical indicators
- Fundamental data
- Forex and crypto data
- Economic indicators

API: https://www.alphavantage.co/
Pricing: Free tier (5 calls/minute, 500/day)

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


class AlphaVantageProvider(BaseDataProvider):
    """
    Alpha Vantage data provider (STUB).
    
    Free tier: 5 calls/minute, 500/day
    Good for: Technical indicators, fundamentals
    """
    
    def __init__(self, api_key: str):
        super().__init__("alpha_vantage", api_key)
        logger.info("AlphaVantageProvider created (STUB - not yet implemented)")
    
    async def initialize(self) -> bool:
        logger.warning("Alpha Vantage provider is a stub - not implemented yet")
        return False
    
    async def get_quote(self, symbol: str) -> Optional[Quote]:
        logger.warning("Alpha Vantage get_quote not implemented")
        return None
    
    async def get_bars(self, symbol: str, timeframe: TimeFrame = TimeFrame.DAY_1,
                      start: Optional[datetime] = None, end: Optional[datetime] = None,
                      limit: int = 100) -> List[Bar]:
        logger.warning("Alpha Vantage get_bars not implemented")
        return []
    
    async def get_news(self, symbol: Optional[str] = None, limit: int = 10) -> List[News]:
        logger.warning("Alpha Vantage get_news not implemented")
        return []
    
    async def search_symbols(self, query: str, limit: int = 10) -> List[Dict[str, str]]:
        logger.warning("Alpha Vantage search_symbols not implemented")
        return []
