"""
Data Sources Package

Unified interface for multiple market data providers:
- Alpaca API (real-time, historical, news)
- yfinance (Yahoo Finance free data)
- Polygon.io (market data aggregator)
- Alpha Vantage (technical indicators)
- Finnhub (news and fundamentals)

Author: ARK Trading Intelligence
Version: 1.0.0
"""

from .base_provider import BaseDataProvider, MarketData, Quote, Bar, News
from .alpaca_provider import AlpacaProvider
from .yfinance_provider import YFinanceProvider
from .polygon_provider import PolygonProvider
from .alpha_vantage_provider import AlphaVantageProvider
from .finnhub_provider import FinnhubProvider
from .aggregator import DataAggregator

__all__ = [
    'BaseDataProvider',
    'MarketData',
    'Quote',
    'Bar',
    'News',
    'AlpacaProvider',
    'YFinanceProvider',
    'PolygonProvider',
    'AlphaVantageProvider',
    'FinnhubProvider',
    'DataAggregator'
]

__version__ = "1.0.0"
