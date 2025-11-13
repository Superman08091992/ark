"""
Yahoo Finance Data Provider

Provides market data via yfinance library (FREE):
- Real-time quotes
- Historical bars  
- Company info and fundamentals
- News articles
- No API key required!

Library: https://github.com/ranaroussi/yfinance

Author: ARK Trading Intelligence
Version: 1.0.0
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import asyncio

try:
    import yfinance as yf
except ImportError:
    yf = None
    logging.warning("yfinance not installed. Run: pip install yfinance")

from .base_provider import (
    BaseDataProvider, Quote, Bar, News, TimeFrame
)

logger = logging.getLogger(__name__)


class YFinanceProvider(BaseDataProvider):
    """
    Yahoo Finance data provider (FREE, no API key required).
    
    Features:
    - No authentication needed
    - Real-time delayed quotes (15-20 min delay)
    - Historical data
    - Fundamentals and company info
    - News articles
    """
    
    def __init__(self):
        """Initialize yfinance provider."""
        super().__init__("yfinance", api_key=None)
        self._cache: Dict[str, any] = {}
    
    async def initialize(self) -> bool:
        """Initialize yfinance (no auth needed)."""
        if yf is None:
            logger.error("yfinance not installed")
            return False
        
        self._initialized = True
        logger.info("yfinance provider initialized (FREE, no API key needed)")
        return True
    
    async def get_quote(self, symbol: str) -> Optional[Quote]:
        """Get latest quote from Yahoo Finance."""
        if not self._initialized:
            logger.error("yfinance not initialized")
            return None
        
        try:
            # Run yfinance in executor to avoid blocking
            ticker = await asyncio.get_event_loop().run_in_executor(
                None, yf.Ticker, symbol
            )
            
            # Get fast info (current price)
            info = await asyncio.get_event_loop().run_in_executor(
                None, lambda: ticker.fast_info
            )
            
            current_price = info.get('lastPrice', 0)
            
            # Get bid/ask from regular info (may be slower)
            full_info = await asyncio.get_event_loop().run_in_executor(
                None, lambda: ticker.info
            )
            
            return Quote(
                symbol=symbol,
                bid=full_info.get('bid', current_price * 0.999),
                ask=full_info.get('ask', current_price * 1.001),
                bid_size=full_info.get('bidSize', 0),
                ask_size=full_info.get('askSize', 0),
                last=current_price,
                last_size=full_info.get('volume', 0),
                volume=full_info.get('volume', 0),
                timestamp=datetime.utcnow(),
                source="yfinance"
            )
        except Exception as e:
            logger.error(f"Error fetching yfinance quote for {symbol}: {e}")
            return None
    
    async def get_bars(self,
                      symbol: str,
                      timeframe: TimeFrame = TimeFrame.DAY_1,
                      start: Optional[datetime] = None,
                      end: Optional[datetime] = None,
                      limit: int = 100) -> List[Bar]:
        """Get historical bars from Yahoo Finance."""
        if not self._initialized:
            logger.error("yfinance not initialized")
            return []
        
        try:
            # Map our timeframe to yfinance interval
            interval_map = {
                TimeFrame.MINUTE_1: "1m",
                TimeFrame.MINUTE_5: "5m",
                TimeFrame.MINUTE_15: "15m",
                TimeFrame.MINUTE_30: "30m",
                TimeFrame.HOUR_1: "1h",
                TimeFrame.DAY_1: "1d",
                TimeFrame.WEEK_1: "1wk",
                TimeFrame.MONTH_1: "1mo"
            }
            interval = interval_map.get(timeframe, "1d")
            
            # Determine period
            if start and end:
                period = None
                start_str = start.strftime("%Y-%m-%d")
                end_str = end.strftime("%Y-%m-%d")
            else:
                # Use period instead
                period_map = {
                    TimeFrame.MINUTE_1: "7d",
                    TimeFrame.MINUTE_5: "7d",
                    TimeFrame.MINUTE_15: "1mo",
                    TimeFrame.MINUTE_30: "1mo",
                    TimeFrame.HOUR_1: "2mo",
                    TimeFrame.DAY_1: "1y",
                    TimeFrame.WEEK_1: "5y",
                    TimeFrame.MONTH_1: "max"
                }
                period = period_map.get(timeframe, "1y")
                start_str = None
                end_str = None
            
            # Fetch data
            ticker = await asyncio.get_event_loop().run_in_executor(
                None, yf.Ticker, symbol
            )
            
            hist = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: ticker.history(
                    period=period,
                    start=start_str,
                    end=end_str,
                    interval=interval
                )
            )
            
            # Convert to Bar objects
            bars = []
            for idx, row in hist.iterrows():
                bars.append(Bar(
                    symbol=symbol,
                    open=float(row['Open']),
                    high=float(row['High']),
                    low=float(row['Low']),
                    close=float(row['Close']),
                    volume=int(row['Volume']),
                    timestamp=idx.to_pydatetime(),
                    source="yfinance"
                ))
            
            # Limit results
            if limit and len(bars) > limit:
                bars = bars[-limit:]
            
            return bars
        except Exception as e:
            logger.error(f"Error fetching yfinance bars for {symbol}: {e}")
            return []
    
    async def get_news(self, symbol: Optional[str] = None, limit: int = 10) -> List[News]:
        """Get news from Yahoo Finance."""
        if not self._initialized:
            logger.error("yfinance not initialized")
            return []
        
        if not symbol:
            logger.warning("yfinance requires symbol for news")
            return []
        
        try:
            ticker = await asyncio.get_event_loop().run_in_executor(
                None, yf.Ticker, symbol
            )
            
            news_data = await asyncio.get_event_loop().run_in_executor(
                None, lambda: ticker.news
            )
            
            news_list = []
            for item in news_data[:limit]:
                news_list.append(News(
                    id=item.get('uuid', ''),
                    headline=item.get('title', ''),
                    summary=item.get('summary', item.get('title', '')),
                    source=item.get('publisher', 'yahoo'),
                    url=item.get('link', ''),
                    symbols=[symbol],
                    timestamp=datetime.fromtimestamp(item.get('providerPublishTime', 0)),
                    sentiment=None
                ))
            
            return news_list
        except Exception as e:
            logger.error(f"Error fetching yfinance news for {symbol}: {e}")
            return []
    
    async def get_fundamentals(self, symbol: str) -> Optional[Dict[str, any]]:
        """Get fundamental data from Yahoo Finance."""
        if not self._initialized:
            return None
        
        try:
            ticker = await asyncio.get_event_loop().run_in_executor(
                None, yf.Ticker, symbol
            )
            
            info = await asyncio.get_event_loop().run_in_executor(
                None, lambda: ticker.info
            )
            
            # Extract key fundamentals
            return {
                "market_cap": info.get('marketCap', 0) / 1_000_000,  # Convert to millions
                "float": info.get('floatShares', 0) / 1_000_000,  # Convert to millions
                "shares_outstanding": info.get('sharesOutstanding', 0) / 1_000_000,
                "short_interest": info.get('shortPercentOfFloat', 0) * 100,  # Convert to %
                "pe_ratio": info.get('trailingPE'),
                "forward_pe": info.get('forwardPE'),
                "peg_ratio": info.get('pegRatio'),
                "price_to_book": info.get('priceToBook'),
                "debt_to_equity": info.get('debtToEquity'),
                "profit_margin": info.get('profitMargins', 0) * 100,
                "operating_margin": info.get('operatingMargins', 0) * 100,
                "return_on_equity": info.get('returnOnEquity', 0) * 100,
                "return_on_assets": info.get('returnOnAssets', 0) * 100,
                "revenue": info.get('totalRevenue', 0) / 1_000_000,
                "revenue_growth": info.get('revenueGrowth', 0) * 100,
                "earnings_growth": info.get('earningsGrowth', 0) * 100,
                "dividend_yield": info.get('dividendYield', 0) * 100,
                "beta": info.get('beta'),
                "52w_high": info.get('fiftyTwoWeekHigh'),
                "52w_low": info.get('fiftyTwoWeekLow'),
                "50d_avg": info.get('fiftyDayAverage'),
                "200d_avg": info.get('twoHundredDayAverage'),
                "avg_volume": info.get('averageVolume'),
                "sector": info.get('sector'),
                "industry": info.get('industry')
            }
        except Exception as e:
            logger.error(f"Error fetching yfinance fundamentals for {symbol}: {e}")
            return None
    
    async def get_technicals(self, symbol: str) -> Optional[Dict[str, any]]:
        """Calculate basic technical indicators from bar data."""
        if not self._initialized:
            return None
        
        try:
            # Get recent bars for calculations
            bars = await self.get_bars(symbol, timeframe=TimeFrame.DAY_1, limit=200)
            
            if len(bars) < 14:
                return None
            
            # Calculate simple indicators
            closes = [bar.close for bar in bars]
            volumes = [bar.volume for bar in bars]
            
            # Current price
            current = closes[-1]
            
            # Simple Moving Averages
            sma_20 = sum(closes[-20:]) / 20 if len(closes) >= 20 else None
            sma_50 = sum(closes[-50:]) / 50 if len(closes) >= 50 else None
            sma_200 = sum(closes[-200:]) / 200 if len(closes) >= 200 else None
            
            # Calculate simple RSI (14 period)
            rsi = self._calculate_rsi(closes, period=14)
            
            # Average volume
            avg_volume = sum(volumes[-20:]) / 20 if len(volumes) >= 20 else volumes[-1]
            
            # ATR (simplified - just using high-low range)
            atr = None
            if len(bars) >= 14:
                ranges = [bar.high - bar.low for bar in bars[-14:]]
                atr = sum(ranges) / 14
            
            return {
                "rsi": rsi,
                "sma_20": sma_20,
                "sma_50": sma_50,
                "sma_200": sma_200,
                "atr": atr,
                "avg_volume": avg_volume,
                "volume_ratio": volumes[-1] / avg_volume if avg_volume else 1.0
            }
        except Exception as e:
            logger.error(f"Error calculating technicals for {symbol}: {e}")
            return None
    
    def _calculate_rsi(self, prices: List[float], period: int = 14) -> Optional[float]:
        """Calculate RSI (Relative Strength Index)."""
        if len(prices) < period + 1:
            return None
        
        deltas = [prices[i] - prices[i-1] for i in range(1, len(prices))]
        
        gains = [d if d > 0 else 0 for d in deltas]
        losses = [-d if d < 0 else 0 for d in deltas]
        
        avg_gain = sum(gains[-period:]) / period
        avg_loss = sum(losses[-period:]) / period
        
        if avg_loss == 0:
            return 100
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        return round(rsi, 2)
    
    async def search_symbols(self, query: str, limit: int = 10) -> List[Dict[str, str]]:
        """Search for symbols (basic implementation)."""
        # yfinance doesn't have native search, but we can try common symbols
        logger.warning("yfinance doesn't support symbol search - returning empty")
        return []


if __name__ == "__main__":
    import asyncio
    
    logging.basicConfig(level=logging.INFO)
    
    async def test():
        provider = YFinanceProvider()
        
        if await provider.initialize():
            print("✅ yfinance initialized (FREE, no API key needed!)")
            
            # Test quote
            quote = await provider.get_quote("TSLA")
            if quote:
                print(f"\n📊 TSLA Quote:")
                print(f"   Last: ${quote.last:.2f}")
                print(f"   Bid: ${quote.bid:.2f} x {quote.bid_size}")
                print(f"   Ask: ${quote.ask:.2f} x {quote.ask_size}")
                print(f"   Volume: {quote.volume:,}")
            
            # Test bars
            bars = await provider.get_bars("TSLA", timeframe=TimeFrame.DAY_1, limit=5)
            print(f"\n📈 TSLA Bars: {len(bars)} bars")
            if bars:
                for bar in bars[-3:]:
                    print(f"   {bar.timestamp.date()}: O=${bar.open:.2f} H=${bar.high:.2f} L=${bar.low:.2f} C=${bar.close:.2f} V={bar.volume:,}")
            
            # Test fundamentals
            fundamentals = await provider.get_fundamentals("TSLA")
            if fundamentals:
                print(f"\n💰 TSLA Fundamentals:")
                print(f"   Market Cap: ${fundamentals.get('market_cap', 0):,.0f}M")
                print(f"   Float: {fundamentals.get('float', 0):.1f}M shares")
                print(f"   Short Interest: {fundamentals.get('short_interest', 0):.1f}%")
                print(f"   P/E Ratio: {fundamentals.get('pe_ratio', 0):.1f}")
                print(f"   Sector: {fundamentals.get('sector', 'N/A')}")
            
            # Test technicals
            technicals = await provider.get_technicals("TSLA")
            if technicals:
                print(f"\n📉 TSLA Technicals:")
                print(f"   RSI: {technicals.get('rsi', 0):.1f}")
                print(f"   SMA 20: ${technicals.get('sma_20', 0):.2f}")
                print(f"   SMA 50: ${technicals.get('sma_50', 0):.2f}")
                print(f"   ATR: ${technicals.get('atr', 0):.2f}")
            
            # Test news
            news = await provider.get_news("TSLA", limit=3)
            print(f"\n📰 TSLA News: {len(news)} articles")
            for article in news[:2]:
                print(f"   - {article.headline}")
            
            await provider.close()
        else:
            print("❌ Failed to initialize yfinance")
    
    asyncio.run(test())
