# ARK Trading Intelligence - Data Sources

Unified market data access layer supporting multiple providers with automatic fallback and intelligent aggregation.

---

## 🎯 **Quick Start (FREE - No API Keys Required!)**

```python
from services.data_sources import YFinanceProvider, DataAggregator

# Option 1: Use yfinance directly (FREE, no setup)
provider = YFinanceProvider()
await provider.initialize()
quote = await provider.get_quote("AAPL")
print(f"AAPL: ${quote.last:.2f}")

# Option 2: Use aggregator (recommended)
aggregator = DataAggregator()
aggregator.add_provider(YFinanceProvider(), priority=1)
await aggregator.initialize_all()

market_data = await aggregator.get_complete_market_data("TSLA")
# Returns: quote, bars, news, fundamentals, technicals - all FREE!
```

---

## 📊 **Supported Data Sources**

### **1. Yahoo Finance (yfinance)** ⭐ **FREE**
- ✅ **No API key required**
- ✅ Real-time delayed quotes (15-20 min delay)
- ✅ Historical data (minute, day, week, month)
- ✅ Fundamental data (P/E, market cap, float, etc.)
- ✅ Technical indicators (calculated from bars)
- ✅ Company news
- ⚠️ Rate limits: Soft limits, usually sufficient for personal use

**Usage:**
```python
from services.data_sources import YFinanceProvider

provider = YFinanceProvider()
await provider.initialize()

# Get quote
quote = await provider.get_quote("AAPL")

# Get historical bars
bars = await provider.get_bars("AAPL", timeframe=TimeFrame.DAY_1, limit=100)

# Get fundamentals
fundamentals = await provider.get_fundamentals("AAPL")
# Returns: market_cap, float, short_interest, PE ratio, etc.

# Get technicals
technicals = await provider.get_technicals("AAPL")
# Returns: RSI, SMA20/50/200, ATR, volume ratios

# Get news
news = await provider.get_news("AAPL", limit=10)
```

---

### **2. Alpaca Markets** 💰 **FREE Paper Trading**
- ✅ **FREE paper trading account** (no credit card)
- ✅ Real-time quotes (for paper trading)
- ✅ Historical bars (minute, hour, day)
- ✅ Market news feed
- ✅ Commission-free paper trading
- ⚠️ Real-time data for live trading requires subscription

**Sign Up:** https://alpaca.markets/ (FREE paper account)

**Setup:**
```bash
# Add to .env
ALPACA_API_KEY=your_key_here
ALPACA_API_SECRET=your_secret_here
```

**Usage:**
```python
from services.data_sources import AlpacaProvider
import os

provider = AlpacaProvider(
    api_key=os.getenv("ALPACA_API_KEY"),
    api_secret=os.getenv("ALPACA_API_SECRET"),
    paper=True  # Use paper trading endpoint
)
await provider.initialize()

quote = await provider.get_quote("TSLA")
bars = await provider.get_bars("TSLA", timeframe=TimeFrame.MINUTE_5, limit=100)
news = await provider.get_news("TSLA", limit=10)
```

---

### **3. Polygon.io** 💰 **Freemium**
- ✅ FREE tier: 5 API calls/minute (delayed data)
- ✅ Comprehensive market data
- ✅ Options and forex data
- ✅ Company financials
- 💵 Paid tiers: Real-time data, higher limits

**Sign Up:** https://polygon.io/

**Status:** ⚠️ **Stub implementation** - add API key to activate

---

### **4. Alpha Vantage** 💰 **Freemium**
- ✅ FREE tier: 5 calls/minute, 500/day
- ✅ Technical indicators (SMA, EMA, RSI, MACD, etc.)
- ✅ Fundamental data
- ✅ Forex and crypto data
- ✅ Economic indicators

**Sign Up:** https://www.alphavantage.co/

**Status:** ⚠️ **Stub implementation** - add API key to activate

---

### **5. Finnhub** 💰 **Freemium**
- ✅ FREE tier: 60 calls/minute
- ✅ Company news
- ✅ Social sentiment analysis
- ✅ Earnings calendars
- ✅ SEC filings

**Sign Up:** https://finnhub.io/

**Status:** ⚠️ **Stub implementation** - add API key to activate

---

## 🚀 **DataAggregator (Recommended)**

The `DataAggregator` intelligently combines multiple providers with automatic fallback:

```python
from services.data_sources import (
    DataAggregator,
    YFinanceProvider,
    AlpacaProvider
)
import os

# Create aggregator
aggregator = DataAggregator()

# Add providers (lower priority = higher preference)
aggregator.add_provider(YFinanceProvider(), priority=2)

# Add Alpaca if available
if os.getenv("ALPACA_API_KEY"):
    aggregator.add_provider(
        AlpacaProvider(
            os.getenv("ALPACA_API_KEY"),
            os.getenv("ALPACA_API_SECRET"),
            paper=True
        ),
        priority=1  # Highest priority
    )

# Initialize all
await aggregator.initialize_all()

# Get comprehensive data (tries all providers automatically)
market_data = await aggregator.get_complete_market_data("AAPL")

# Access data
print(f"Quote: ${market_data.quote.last:.2f}")
print(f"Bars: {len(market_data.bars)}")
print(f"News: {len(market_data.news)}")
print(f"P/E Ratio: {market_data.fundamentals.get('pe_ratio')}")
print(f"RSI: {market_data.technicals.get('rsi')}")
```

**Features:**
- ✅ Automatic fallback if primary provider fails
- ✅ Result caching (configurable TTL)
- ✅ Priority-based provider selection
- ✅ Parallel data fetching for speed
- ✅ Unified data format across providers

---

## 📦 **Data Structures**

### **Quote**
```python
@dataclass
class Quote:
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
```

### **Bar (OHLCV)**
```python
@dataclass
class Bar:
    symbol: str
    open: float
    high: float
    low: float
    close: float
    volume: int
    timestamp: datetime
    vwap: Optional[float]
    trade_count: Optional[int]
    source: str
```

### **News**
```python
@dataclass
class News:
    id: str
    headline: str
    summary: str
    source: str
    url: str
    symbols: List[str]
    timestamp: datetime
    sentiment: Optional[str]
```

### **MarketData (Complete Package)**
```python
@dataclass
class MarketData:
    symbol: str
    quote: Optional[Quote]
    bars: Optional[List[Bar]]
    news: Optional[List[News]]
    fundamentals: Optional[Dict[str, Any]]
    technicals: Optional[Dict[str, Any]]
    metadata: Optional[Dict[str, Any]]
```

---

## 🔧 **Installation**

```bash
# Install core dependencies
pip install -r requirements-data-sources.txt

# Or install individually:
pip install yfinance aiohttp pandas numpy

# For Alpaca (optional):
pip install alpaca-py

# For other providers (optional):
pip install polygon-api-client alpha-vantage finnhub-python
```

---

## ⚙️ **Configuration**

Create a `.env` file:

```bash
# Alpaca (FREE paper trading)
ALPACA_API_KEY=your_key_here
ALPACA_API_SECRET=your_secret_here

# Polygon.io (optional)
POLYGON_API_KEY=your_key_here

# Alpha Vantage (optional)
ALPHA_VANTAGE_API_KEY=your_key_here

# Finnhub (optional)
FINNHUB_API_KEY=your_key_here
```

**Load in Python:**
```python
from dotenv import load_dotenv
load_dotenv()
```

---

## 📝 **Examples**

### **Example 1: Basic Usage**
```python
from services.data_sources import YFinanceProvider, TimeFrame

provider = YFinanceProvider()
await provider.initialize()

# Get complete market data
market_data = await provider.get_market_data("TSLA")

print(f"Price: ${market_data.quote.last:.2f}")
print(f"Market Cap: ${market_data.fundamentals['market_cap']:,.0f}M")
print(f"RSI: {market_data.technicals['rsi']:.1f}")
```

### **Example 2: Historical Analysis**
```python
from services.data_sources import YFinanceProvider, TimeFrame

provider = YFinanceProvider()
await provider.initialize()

# Get 1-year daily bars
bars = await provider.get_bars(
    "AAPL",
    timeframe=TimeFrame.DAY_1,
    limit=252  # ~1 trading year
)

# Calculate returns
prices = [bar.close for bar in bars]
returns = [(prices[i] - prices[i-1]) / prices[i-1] for i in range(1, len(prices))]
avg_return = sum(returns) / len(returns)
print(f"Average daily return: {avg_return:.2%}")
```

### **Example 3: Multi-Provider Aggregation**
```python
from services.data_sources import DataAggregator, YFinanceProvider
import os

aggregator = DataAggregator()

# Add all available providers
aggregator.add_provider(YFinanceProvider(), priority=2)

# Initialize
await aggregator.initialize_all()

# Get data from best available source
quote = await aggregator.get_quote("TSLA")  # Uses best provider
bars = await aggregator.get_bars("TSLA")    # Falls back if needed
news = await aggregator.get_news("TSLA")    # Merges from all sources

print(f"Quote source: {quote.source}")
print(f"News from {len(set(n.source for n in news))} sources")
```

---

## 🎯 **Best Practices**

1. **Start with yfinance (FREE)**
   - No setup required
   - Perfect for development/testing
   - Sufficient for most use cases

2. **Add Alpaca for real-time data**
   - FREE paper trading account
   - Real-time quotes for paper trading
   - Great for live testing

3. **Use DataAggregator for production**
   - Automatic fallback
   - Combines data from multiple sources
   - Built-in caching

4. **Respect rate limits**
   - yfinance: Reasonable usage
   - Alpaca: Check account limits
   - Paid APIs: Monitor usage

5. **Cache aggressively**
   - DataAggregator has built-in caching
   - Customize TTL per data type
   - Quotes: 30s, Bars: 5min, Fundamentals: 1hr

---

## 🐛 **Troubleshooting**

### **yfinance not working**
```bash
pip install --upgrade yfinance
# Or force reinstall:
pip install --force-reinstall yfinance
```

### **Alpaca authentication failed**
- Verify API keys in .env
- Check if using paper trading endpoint
- Ensure account is active

### **No data returned**
- Check symbol format (e.g., "AAPL" not "AAPL.US")
- Verify market hours (some data only available during trading)
- Check provider rate limits

### **Import errors**
```bash
# Install all dependencies:
pip install -r requirements-data-sources.txt
```

---

## 📚 **API Reference**

See `base_provider.py` for complete interface documentation.

**Key Methods:**
- `initialize()` - Initialize provider connection
- `get_quote(symbol)` - Get real-time quote
- `get_bars(symbol, timeframe, start, end, limit)` - Historical bars
- `get_news(symbol, limit)` - News articles
- `get_fundamentals(symbol)` - Company fundamentals
- `get_technicals(symbol)` - Technical indicators
- `get_market_data(symbol)` - Complete data package

---

## 🤝 **Contributing**

To add a new data provider:

1. Create new file: `services/data_sources/your_provider.py`
2. Inherit from `BaseDataProvider`
3. Implement required methods
4. Add to `__init__.py`
5. Update this README

---

## 📄 **License**

Part of ARK Trading Intelligence system.

---

**Questions?** Check the example code in `__main__` blocks of each provider file.
