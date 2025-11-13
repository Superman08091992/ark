"""
Base Data Provider Interface

Defines standard interface for all market data providers.
All providers must implement these methods for unified access.

Author: ARK Trading Intelligence
Version: 1.0.0
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class TimeFrame(str, Enum):
    """Standard timeframes for bar data."""
    MINUTE_1 = "1Min"
    MINUTE_5 = "5Min"
    MINUTE_15 = "15Min"
    MINUTE_30 = "30Min"
    HOUR_1 = "1Hour"
    HOUR_4 = "4Hour"
    DAY_1 = "1Day"
    WEEK_1 = "1Week"
    MONTH_1 = "1Month"


@dataclass
class Quote:
    """Real-time quote data."""
    symbol: str
    bid: float
    ask: float
    bid_size: int
    ask_size: int
    last: float
    last_size: int
    volume: int
    timestamp: datetime
    source: str


@dataclass
class Bar:
    """OHLCV bar data."""
    symbol: str
    open: float
    high: float
    low: float
    close: float
    volume: int
    timestamp: datetime
    vwap: Optional[float] = None
    trade_count: Optional[int] = None
    source: str = ""


@dataclass
class News:
    """News article data."""
    id: str
    headline: str
    summary: str
    source: str
    url: str
    symbols: List[str]
    timestamp: datetime
    sentiment: Optional[str] = None


@dataclass
class MarketData:
    """Complete market data package."""
    symbol: str
    quote: Optional[Quote] = None
    bars: Optional[List[Bar]] = None
    news: Optional[List[News]] = None
    fundamentals: Optional[Dict[str, Any]] = None
    technicals: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None


class BaseDataProvider(ABC):
    """
    Abstract base class for market data providers.
    
    All data source implementations must inherit from this class
    and implement the required methods.
    """
    
    def __init__(self, name: str, api_key: Optional[str] = None):
        """
        Initialize data provider.
        
        Args:
            name: Provider name
            api_key: API key for authentication (if required)
        """
        self.name = name
        self.api_key = api_key
        self._initialized = False
    
    @abstractmethod
    async def initialize(self) -> bool:
        """
        Initialize provider connection.
        
        Returns:
            True if successful, False otherwise
        """
        pass
    
    @abstractmethod
    async def get_quote(self, symbol: str) -> Optional[Quote]:
        """
        Get real-time quote for symbol.
        
        Args:
            symbol: Stock ticker symbol
            
        Returns:
            Quote object or None if unavailable
        """
        pass
    
    @abstractmethod
    async def get_bars(self, 
                      symbol: str,
                      timeframe: TimeFrame = TimeFrame.DAY_1,
                      start: Optional[datetime] = None,
                      end: Optional[datetime] = None,
                      limit: int = 100) -> List[Bar]:
        """
        Get historical bar data.
        
        Args:
            symbol: Stock ticker symbol
            timeframe: Bar timeframe
            start: Start datetime (optional)
            end: End datetime (optional)
            limit: Maximum bars to return
            
        Returns:
            List of Bar objects
        """
        pass
    
    @abstractmethod
    async def get_news(self, 
                      symbol: Optional[str] = None,
                      limit: int = 10) -> List[News]:
        """
        Get news articles.
        
        Args:
            symbol: Stock ticker symbol (None for general market news)
            limit: Maximum articles to return
            
        Returns:
            List of News objects
        """
        pass
    
    async def get_fundamentals(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Get fundamental data (market cap, PE ratio, etc.).
        
        Args:
            symbol: Stock ticker symbol
            
        Returns:
            Dictionary of fundamental metrics or None
        """
        return None
    
    async def get_technicals(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Get technical indicators (RSI, MACD, etc.).
        
        Args:
            symbol: Stock ticker symbol
            
        Returns:
            Dictionary of technical indicators or None
        """
        return None
    
    async def get_market_data(self, 
                             symbol: str,
                             include_bars: bool = True,
                             include_news: bool = True,
                             include_fundamentals: bool = True,
                             include_technicals: bool = True) -> MarketData:
        """
        Get comprehensive market data package.
        
        Args:
            symbol: Stock ticker symbol
            include_bars: Include historical bars
            include_news: Include news articles
            include_fundamentals: Include fundamentals
            include_technicals: Include technical indicators
            
        Returns:
            MarketData object with requested data
        """
        market_data = MarketData(symbol=symbol)
        
        # Get quote (always included)
        market_data.quote = await self.get_quote(symbol)
        
        # Get bars if requested
        if include_bars:
            market_data.bars = await self.get_bars(symbol, limit=100)
        
        # Get news if requested
        if include_news:
            market_data.news = await self.get_news(symbol, limit=10)
        
        # Get fundamentals if requested
        if include_fundamentals:
            market_data.fundamentals = await self.get_fundamentals(symbol)
        
        # Get technicals if requested
        if include_technicals:
            market_data.technicals = await self.get_technicals(symbol)
        
        return market_data
    
    @abstractmethod
    async def search_symbols(self, query: str, limit: int = 10) -> List[Dict[str, str]]:
        """
        Search for symbols matching query.
        
        Args:
            query: Search query
            limit: Maximum results
            
        Returns:
            List of symbol info dicts
        """
        pass
    
    async def close(self) -> None:
        """Close provider connection."""
        self._initialized = False
    
    def is_initialized(self) -> bool:
        """Check if provider is initialized."""
        return self._initialized
