"""
Data Aggregator

Intelligently combines data from multiple providers:
- Falls back to alternate sources if primary fails
- Merges data from multiple sources for completeness
- Caches results to minimize API calls
- Prioritizes real-time sources over delayed

Author: ARK Trading Intelligence
Version: 1.0.0
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import asyncio

from .base_provider import (
    BaseDataProvider, Quote, Bar, News, TimeFrame, MarketData
)

logger = logging.getLogger(__name__)


class DataAggregator:
    """
    Intelligent data aggregator combining multiple providers.
    
    Features:
    - Automatic fallback to alternate sources
    - Data merging and enrichment
    - Result caching
    - Source prioritization
    """
    
    def __init__(self):
        """Initialize data aggregator."""
        self.providers: Dict[str, BaseDataProvider] = {}
        self._cache: Dict[str, Any] = {}
        self._cache_ttl: Dict[str, datetime] = {}
        self.default_cache_seconds = 60
    
    def add_provider(self, provider: BaseDataProvider, priority: int = 5) -> None:
        """
        Add data provider to aggregator.
        
        Args:
            provider: Data provider instance
            priority: Provider priority (1=highest, 10=lowest)
        """
        self.providers[provider.name] = {
            "provider": provider,
            "priority": priority
        }
        logger.info(f"Added provider '{provider.name}' with priority {priority}")
    
    def _get_sorted_providers(self) -> List[BaseDataProvider]:
        """Get providers sorted by priority."""
        sorted_items = sorted(
            self.providers.items(),
            key=lambda x: x[1]['priority']
        )
        return [item[1]['provider'] for item in sorted_items]
    
    def _get_cache_key(self, method: str, symbol: str, **kwargs) -> str:
        """Generate cache key."""
        key_parts = [method, symbol]
        for k, v in sorted(kwargs.items()):
            key_parts.append(f"{k}:{v}")
        return ":".join(key_parts)
    
    def _is_cache_valid(self, key: str) -> bool:
        """Check if cache entry is still valid."""
        if key not in self._cache_ttl:
            return False
        return datetime.utcnow() < self._cache_ttl[key]
    
    def _set_cache(self, key: str, value: Any, ttl_seconds: Optional[int] = None) -> None:
        """Set cache entry with TTL."""
        self._cache[key] = value
        ttl = ttl_seconds if ttl_seconds is not None else self.default_cache_seconds
        self._cache_ttl[key] = datetime.utcnow() + timedelta(seconds=ttl)
    
    async def initialize_all(self) -> Dict[str, bool]:
        """Initialize all providers."""
        results = {}
        for name, data in self.providers.items():
            provider = data['provider']
            try:
                success = await provider.initialize()
                results[name] = success
                if success:
                    logger.info(f"✅ {name} initialized")
                else:
                    logger.warning(f"⚠️  {name} failed to initialize")
            except Exception as e:
                logger.error(f"❌ {name} initialization error: {e}")
                results[name] = False
        return results
    
    async def get_quote(self, symbol: str, use_cache: bool = True) -> Optional[Quote]:
        """
        Get quote with fallback to alternate sources.
        
        Args:
            symbol: Stock ticker
            use_cache: Use cached result if available
            
        Returns:
            Quote from first successful provider
        """
        cache_key = self._get_cache_key("quote", symbol)
        
        # Check cache
        if use_cache and self._is_cache_valid(cache_key):
            logger.debug(f"Cache hit for quote: {symbol}")
            return self._cache[cache_key]
        
        # Try providers in priority order
        for provider in self._get_sorted_providers():
            if not provider.is_initialized():
                continue
            
            try:
                quote = await provider.get_quote(symbol)
                if quote:
                    logger.debug(f"Got quote for {symbol} from {provider.name}")
                    self._set_cache(cache_key, quote, ttl_seconds=30)  # Short TTL for quotes
                    return quote
            except Exception as e:
                logger.warning(f"Provider {provider.name} failed for quote {symbol}: {e}")
                continue
        
        logger.error(f"All providers failed for quote: {symbol}")
        return None
    
    async def get_bars(self,
                      symbol: str,
                      timeframe: TimeFrame = TimeFrame.DAY_1,
                      start: Optional[datetime] = None,
                      end: Optional[datetime] = None,
                      limit: int = 100,
                      use_cache: bool = True) -> List[Bar]:
        """Get bars with fallback."""
        cache_key = self._get_cache_key("bars", symbol, tf=timeframe.value, limit=limit)
        
        # Check cache
        if use_cache and self._is_cache_valid(cache_key):
            logger.debug(f"Cache hit for bars: {symbol}")
            return self._cache[cache_key]
        
        # Try providers
        for provider in self._get_sorted_providers():
            if not provider.is_initialized():
                continue
            
            try:
                bars = await provider.get_bars(symbol, timeframe, start, end, limit)
                if bars:
                    logger.debug(f"Got {len(bars)} bars for {symbol} from {provider.name}")
                    self._set_cache(cache_key, bars, ttl_seconds=300)  # 5 min cache for bars
                    return bars
            except Exception as e:
                logger.warning(f"Provider {provider.name} failed for bars {symbol}: {e}")
                continue
        
        logger.error(f"All providers failed for bars: {symbol}")
        return []
    
    async def get_news(self, symbol: Optional[str] = None, limit: int = 10) -> List[News]:
        """Get news from all providers and merge."""
        all_news = []
        seen_ids = set()
        
        # Collect news from all providers
        for provider in self._get_sorted_providers():
            if not provider.is_initialized():
                continue
            
            try:
                news = await provider.get_news(symbol, limit)
                for article in news:
                    if article.id not in seen_ids:
                        all_news.append(article)
                        seen_ids.add(article.id)
            except Exception as e:
                logger.warning(f"Provider {provider.name} failed for news: {e}")
                continue
        
        # Sort by timestamp (most recent first)
        all_news.sort(key=lambda x: x.timestamp, reverse=True)
        
        return all_news[:limit]
    
    async def get_fundamentals(self, symbol: str, use_cache: bool = True) -> Optional[Dict[str, Any]]:
        """Get fundamentals with fallback."""
        cache_key = self._get_cache_key("fundamentals", symbol)
        
        # Check cache
        if use_cache and self._is_cache_valid(cache_key):
            logger.debug(f"Cache hit for fundamentals: {symbol}")
            return self._cache[cache_key]
        
        # Try providers
        for provider in self._get_sorted_providers():
            if not provider.is_initialized():
                continue
            
            try:
                fundamentals = await provider.get_fundamentals(symbol)
                if fundamentals:
                    logger.debug(f"Got fundamentals for {symbol} from {provider.name}")
                    self._set_cache(cache_key, fundamentals, ttl_seconds=3600)  # 1 hour cache
                    return fundamentals
            except Exception as e:
                logger.warning(f"Provider {provider.name} failed for fundamentals {symbol}: {e}")
                continue
        
        logger.error(f"All providers failed for fundamentals: {symbol}")
        return None
    
    async def get_technicals(self, symbol: str, use_cache: bool = True) -> Optional[Dict[str, Any]]:
        """Get technical indicators with fallback."""
        cache_key = self._get_cache_key("technicals", symbol)
        
        # Check cache
        if use_cache and self._is_cache_valid(cache_key):
            logger.debug(f"Cache hit for technicals: {symbol}")
            return self._cache[cache_key]
        
        # Try providers
        for provider in self._get_sorted_providers():
            if not provider.is_initialized():
                continue
            
            try:
                technicals = await provider.get_technicals(symbol)
                if technicals:
                    logger.debug(f"Got technicals for {symbol} from {provider.name}")
                    self._set_cache(cache_key, technicals, ttl_seconds=300)  # 5 min cache
                    return technicals
            except Exception as e:
                logger.warning(f"Provider {provider.name} failed for technicals {symbol}: {e}")
                continue
        
        logger.error(f"All providers failed for technicals: {symbol}")
        return None
    
    async def get_complete_market_data(self, symbol: str) -> MarketData:
        """
        Get complete market data package by aggregating all sources.
        
        This is the recommended method for getting comprehensive data.
        """
        logger.info(f"Fetching complete market data for {symbol}")
        
        # Fetch all data in parallel
        results = await asyncio.gather(
            self.get_quote(symbol),
            self.get_bars(symbol, limit=100),
            self.get_news(symbol, limit=10),
            self.get_fundamentals(symbol),
            self.get_technicals(symbol),
            return_exceptions=True
        )
        
        quote, bars, news, fundamentals, technicals = results
        
        # Handle exceptions
        if isinstance(quote, Exception):
            logger.error(f"Quote fetch failed: {quote}")
            quote = None
        if isinstance(bars, Exception):
            logger.error(f"Bars fetch failed: {bars}")
            bars = []
        if isinstance(news, Exception):
            logger.error(f"News fetch failed: {news}")
            news = []
        if isinstance(fundamentals, Exception):
            logger.error(f"Fundamentals fetch failed: {fundamentals}")
            fundamentals = None
        if isinstance(technicals, Exception):
            logger.error(f"Technicals fetch failed: {technicals}")
            technicals = None
        
        return MarketData(
            symbol=symbol,
            quote=quote,
            bars=bars,
            news=news,
            fundamentals=fundamentals,
            technicals=technicals,
            metadata={
                "fetched_at": datetime.utcnow().isoformat(),
                "providers_used": [p.name for p in self._get_sorted_providers() if p.is_initialized()]
            }
        )
    
    async def close_all(self) -> None:
        """Close all providers."""
        for name, data in self.providers.items():
            provider = data['provider']
            try:
                await provider.close()
                logger.info(f"Closed provider: {name}")
            except Exception as e:
                logger.error(f"Error closing provider {name}: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get aggregator statistics."""
        return {
            "providers_count": len(self.providers),
            "providers_initialized": sum(
                1 for data in self.providers.values()
                if data['provider'].is_initialized()
            ),
            "cache_entries": len(self._cache),
            "providers": {
                name: {
                    "initialized": data['provider'].is_initialized(),
                    "priority": data['priority']
                }
                for name, data in self.providers.items()
            }
        }


if __name__ == "__main__":
    import asyncio
    import os
    from .yfinance_provider import YFinanceProvider
    from .alpaca_provider import AlpacaProvider
    
    logging.basicConfig(level=logging.INFO)
    
    async def test():
        # Create aggregator
        aggregator = DataAggregator()
        
        # Add yfinance (FREE, priority 2)
        yf_provider = YFinanceProvider()
        aggregator.add_provider(yf_provider, priority=2)
        
        # Add Alpaca if credentials available (priority 1 - highest)
        alpaca_key = os.getenv("ALPACA_API_KEY")
        alpaca_secret = os.getenv("ALPACA_API_SECRET")
        if alpaca_key and alpaca_secret:
            alpaca_provider = AlpacaProvider(alpaca_key, alpaca_secret, paper=True)
            aggregator.add_provider(alpaca_provider, priority=1)
        
        # Initialize all
        results = await aggregator.initialize_all()
        print(f"\n✅ Initialized providers: {results}")
        
        # Get complete market data
        symbol = "AAPL"
        print(f"\n📊 Fetching complete market data for {symbol}...")
        
        market_data = await aggregator.get_complete_market_data(symbol)
        
        if market_data.quote:
            print(f"\n💹 Quote: ${market_data.quote.last:.2f}")
        
        if market_data.bars:
            print(f"\n📈 Bars: {len(market_data.bars)} historical bars")
            latest = market_data.bars[-1]
            print(f"   Latest: {latest.timestamp.date()} - Close: ${latest.close:.2f}")
        
        if market_data.fundamentals:
            print(f"\n💰 Fundamentals:")
            print(f"   Market Cap: ${market_data.fundamentals.get('market_cap', 0):,.0f}M")
            print(f"   Float: {market_data.fundamentals.get('float', 0):.1f}M")
            print(f"   P/E: {market_data.fundamentals.get('pe_ratio', 0):.1f}")
        
        if market_data.technicals:
            print(f"\n📉 Technicals:")
            print(f"   RSI: {market_data.technicals.get('rsi', 0):.1f}")
            print(f"   SMA 50: ${market_data.technicals.get('sma_50', 0):.2f}")
        
        if market_data.news:
            print(f"\n📰 News: {len(market_data.news)} articles")
            for article in market_data.news[:2]:
                print(f"   - {article.headline}")
        
        print(f"\n📊 Stats: {aggregator.get_stats()}")
        
        await aggregator.close_all()
    
    asyncio.run(test())
