"""
Alpaca Data Provider

Provides market data via Alpaca Markets API:
- Real-time quotes
- Historical bars
- News feed
- Free tier available with paper trading account

API Docs: https://alpaca.markets/docs/

Author: ARK Trading Intelligence
Version: 1.0.0
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import aiohttp

from .base_provider import (
    BaseDataProvider, Quote, Bar, News, TimeFrame
)

logger = logging.getLogger(__name__)


class AlpacaProvider(BaseDataProvider):
    """
    Alpaca Markets data provider.
    
    Requires:
    - ALPACA_API_KEY
    - ALPACA_API_SECRET
    - ALPACA_BASE_URL (paper: https://paper-api.alpaca.markets)
    """
    
    # API endpoints
    BASE_URL_PAPER = "https://paper-api.alpaca.markets"
    BASE_URL_LIVE = "https://api.alpaca.markets"
    DATA_URL = "https://data.alpaca.markets"
    
    def __init__(self, api_key: str, api_secret: str, paper: bool = True):
        """
        Initialize Alpaca provider.
        
        Args:
            api_key: Alpaca API key
            api_secret: Alpaca API secret
            paper: Use paper trading endpoint (default True)
        """
        super().__init__("alpaca", api_key)
        self.api_secret = api_secret
        self.base_url = self.BASE_URL_PAPER if paper else self.BASE_URL_LIVE
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def initialize(self) -> bool:
        """Initialize HTTP session with headers."""
        try:
            self.session = aiohttp.ClientSession(headers={
                "APCA-API-KEY-ID": self.api_key,
                "APCA-API-SECRET-KEY": self.api_secret
            })
            
            # Verify credentials by fetching account
            async with self.session.get(f"{self.base_url}/v2/account") as resp:
                if resp.status == 200:
                    self._initialized = True
                    logger.info("Alpaca provider initialized successfully")
                    return True
                else:
                    logger.error(f"Alpaca auth failed: {resp.status}")
                    return False
        except Exception as e:
            logger.error(f"Failed to initialize Alpaca: {e}")
            return False
    
    async def get_quote(self, symbol: str) -> Optional[Quote]:
        """Get latest quote from Alpaca."""
        if not self._initialized or not self.session:
            logger.error("Alpaca not initialized")
            return None
        
        try:
            url = f"{self.DATA_URL}/v2/stocks/{symbol}/quotes/latest"
            async with self.session.get(url) as resp:
                if resp.status != 200:
                    logger.error(f"Alpaca quote failed for {symbol}: {resp.status}")
                    return None
                
                data = await resp.json()
                quote_data = data.get('quote', {})
                
                return Quote(
                    symbol=symbol,
                    bid=quote_data.get('bp', 0),
                    ask=quote_data.get('ap', 0),
                    bid_size=quote_data.get('bs', 0),
                    ask_size=quote_data.get('as', 0),
                    last=quote_data.get('ap', 0),  # Use ask as last
                    last_size=0,
                    volume=0,
                    timestamp=datetime.fromisoformat(quote_data.get('t', datetime.utcnow().isoformat()).replace('Z', '+00:00')),
                    source="alpaca"
                )
        except Exception as e:
            logger.error(f"Error fetching Alpaca quote for {symbol}: {e}")
            return None
    
    async def get_bars(self,
                      symbol: str,
                      timeframe: TimeFrame = TimeFrame.DAY_1,
                      start: Optional[datetime] = None,
                      end: Optional[datetime] = None,
                      limit: int = 100) -> List[Bar]:
        """Get historical bars from Alpaca."""
        if not self._initialized or not self.session:
            logger.error("Alpaca not initialized")
            return []
        
        try:
            # Map our timeframe to Alpaca format
            tf_map = {
                TimeFrame.MINUTE_1: "1Min",
                TimeFrame.MINUTE_5: "5Min",
                TimeFrame.MINUTE_15: "15Min",
                TimeFrame.HOUR_1: "1Hour",
                TimeFrame.DAY_1: "1Day"
            }
            alpaca_tf = tf_map.get(timeframe, "1Day")
            
            # Default date range if not provided
            if not end:
                end = datetime.utcnow()
            if not start:
                start = end - timedelta(days=30)
            
            url = f"{self.DATA_URL}/v2/stocks/{symbol}/bars"
            params = {
                "timeframe": alpaca_tf,
                "start": start.isoformat(),
                "end": end.isoformat(),
                "limit": limit
            }
            
            async with self.session.get(url, params=params) as resp:
                if resp.status != 200:
                    logger.error(f"Alpaca bars failed for {symbol}: {resp.status}")
                    return []
                
                data = await resp.json()
                bars_data = data.get('bars', [])
                
                bars = []
                for bar in bars_data:
                    bars.append(Bar(
                        symbol=symbol,
                        open=bar.get('o', 0),
                        high=bar.get('h', 0),
                        low=bar.get('l', 0),
                        close=bar.get('c', 0),
                        volume=bar.get('v', 0),
                        timestamp=datetime.fromisoformat(bar.get('t', '').replace('Z', '+00:00')),
                        vwap=bar.get('vw'),
                        trade_count=bar.get('n'),
                        source="alpaca"
                    ))
                
                return bars
        except Exception as e:
            logger.error(f"Error fetching Alpaca bars for {symbol}: {e}")
            return []
    
    async def get_news(self, symbol: Optional[str] = None, limit: int = 10) -> List[News]:
        """Get news from Alpaca."""
        if not self._initialized or not self.session:
            logger.error("Alpaca not initialized")
            return []
        
        try:
            url = f"{self.DATA_URL}/v1beta1/news"
            params = {"limit": limit}
            
            if symbol:
                params["symbols"] = symbol
            
            async with self.session.get(url, params=params) as resp:
                if resp.status != 200:
                    logger.error(f"Alpaca news failed: {resp.status}")
                    return []
                
                data = await resp.json()
                news_items = data.get('news', [])
                
                news_list = []
                for item in news_items:
                    news_list.append(News(
                        id=str(item.get('id', '')),
                        headline=item.get('headline', ''),
                        summary=item.get('summary', ''),
                        source=item.get('source', 'alpaca'),
                        url=item.get('url', ''),
                        symbols=item.get('symbols', []),
                        timestamp=datetime.fromisoformat(item.get('created_at', datetime.utcnow().isoformat()).replace('Z', '+00:00')),
                        sentiment=None
                    ))
                
                return news_list
        except Exception as e:
            logger.error(f"Error fetching Alpaca news: {e}")
            return []
    
    async def search_symbols(self, query: str, limit: int = 10) -> List[Dict[str, str]]:
        """Search for symbols (Alpaca doesn't have native search, return empty)."""
        logger.warning("Alpaca doesn't support symbol search")
        return []
    
    async def close(self) -> None:
        """Close HTTP session."""
        if self.session:
            await self.session.close()
        await super().close()


if __name__ == "__main__":
    import asyncio
    import os
    
    logging.basicConfig(level=logging.INFO)
    
    async def test():
        # Test Alpaca provider (requires env vars)
        api_key = os.getenv("ALPACA_API_KEY", "")
        api_secret = os.getenv("ALPACA_API_SECRET", "")
        
        if not api_key or not api_secret:
            print("⚠️  Set ALPACA_API_KEY and ALPACA_API_SECRET environment variables")
            return
        
        provider = AlpacaProvider(api_key, api_secret, paper=True)
        
        if await provider.initialize():
            print("✅ Alpaca initialized")
            
            # Test quote
            quote = await provider.get_quote("AAPL")
            if quote:
                print(f"📊 AAPL Quote: ${quote.last:.2f} (bid: ${quote.bid:.2f}, ask: ${quote.ask:.2f})")
            
            # Test bars
            bars = await provider.get_bars("AAPL", timeframe=TimeFrame.DAY_1, limit=5)
            print(f"📈 AAPL Bars: {len(bars)} bars fetched")
            if bars:
                latest = bars[-1]
                print(f"   Latest: O=${latest.open:.2f} H=${latest.high:.2f} L=${latest.low:.2f} C=${latest.close:.2f}")
            
            # Test news
            news = await provider.get_news("AAPL", limit=3)
            print(f"📰 AAPL News: {len(news)} articles")
            for article in news[:2]:
                print(f"   - {article.headline}")
            
            await provider.close()
        else:
            print("❌ Failed to initialize Alpaca")
    
    asyncio.run(test())
