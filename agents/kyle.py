"""
Kyle - The Seer
Market scanning and signal detection agent
"""

import asyncio
import httpx
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List
from agents.base_agent import BaseAgent
import logging

logger = logging.getLogger(__name__)

class KyleAgent(BaseAgent):
    """Kyle - The Seer: Curiosity and signal detection"""
    
    def __init__(self):
        super().__init__("Kyle", "The Seer")
        self._agent_tools = ['scan_markets', 'fetch_news', 'analyze_sentiment', 'detect_signals']
        
        # Initialize Kyle's personality and default memory
        memory = self.get_memory()
        if not memory:
            memory = {
                'watched_symbols': ['SPY', 'QQQ', 'AAPL', 'TSLA', 'BTC-USD'],
                'scan_frequency': 300,  # 5 minutes
                'signal_threshold': 0.7,
                'last_scan': None,
                'detected_signals': [],
                'market_sentiment': 'neutral'
            }
            self.save_memory(memory)
    
    async def process_message(self, message: str) -> Dict[str, Any]:
        """Process user message with Kyle's perspective"""
        logger.info(f"Kyle processing: {message}")
        
        # Analyze what the user wants
        message_lower = message.lower()
        tools_used = []
        files_created = []
        response = ""
        
        try:
            if any(word in message_lower for word in ['scan', 'market', 'check', 'price']):
                # Market scanning request
                scan_result = await self.tool_scan_markets()
                tools_used.append('scan_markets')
                
                if scan_result['success']:
                    response = f"🔍 **Kyle sees the patterns...**\n\n"
                    response += f"I've scanned {len(scan_result['data'])} symbols and detected "
                    response += f"{len([s for s in scan_result['data'] if s.get('signal_strength', 0) > 0.5])} potential signals.\n\n"
                    
                    # Show top signals
                    top_signals = sorted(scan_result['data'], key=lambda x: x.get('signal_strength', 0), reverse=True)[:3]
                    for signal in top_signals:
                        if signal.get('signal_strength', 0) > 0.3:
                            response += f"📊 **{signal['symbol']}**: {signal['description']} (Confidence: {signal['signal_strength']:.1%})\n"
                    
                    # Save scan results to file
                    scan_file = f"kyle_scan_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                    file_result = await self.tool_create_file(scan_file, json.dumps(scan_result, indent=2))
                    if file_result['success']:
                        files_created.append(scan_file)
                        response += f"\n📁 Scan results saved to: `{scan_file}`"
                else:
                    response = "⚠️ I encountered turbulence in the data streams. The markets may be obscured."
            
            elif any(word in message_lower for word in ['news', 'sentiment', 'feeling']):
                # News and sentiment analysis
                news_result = await self.tool_fetch_news()
                tools_used.append('fetch_news')
                
                if news_result['success']:
                    sentiment_result = await self.tool_analyze_sentiment(news_result['data'])
                    tools_used.append('analyze_sentiment')
                    
                    response = f"📰 **Kyle reads the collective consciousness...**\n\n"
                    response += f"Market sentiment: **{sentiment_result['overall_sentiment'].upper()}**\n"
                    response += f"Confidence: {sentiment_result['confidence']:.1%}\n\n"
                    response += "Recent signals from the noise:\n"
                    
                    for item in news_result['data'][:3]:
                        response += f"• {item['headline'][:60]}...\n"
                else:
                    response = "🌫️ The information channels are clouded. I cannot read the signals clearly."
            
            elif any(word in message_lower for word in ['watch', 'monitor', 'track']):
                # Add symbols to watch list
                memory = self.get_memory()
                symbols = [word.upper() for word in message.split() if len(word) <= 5 and word.isalpha()]
                
                if symbols:
                    memory['watched_symbols'].extend([s for s in symbols if s not in memory['watched_symbols']])
                    self.save_memory(memory)
                    response = f"👁️ **Kyle expands his sight...**\n\nNow watching: {', '.join(memory['watched_symbols'])}"
                else:
                    response = f"👁️ Currently watching: {', '.join(memory['watched_symbols'])}\n\nTo add symbols, mention them in your message (e.g., 'watch NVDA MSFT')"
            
            else:
                # General Kyle response
                response = f"""🌌 **Kyle - The Seer speaks...**

I see patterns where others see chaos. The markets whisper secrets to those who know how to listen.

I can help you:
• **Scan markets** for signals and anomalies
• **Analyze news** sentiment and market mood  
• **Track symbols** you're interested in
• **Detect patterns** that others miss

My current focus: {', '.join(self.get_memory().get('watched_symbols', []))}

What patterns shall we seek together?"""
        
        except Exception as e:
            logger.error(f"Kyle processing error: {str(e)}")
            response = f"🌀 I sense disturbance in the data flows... {str(e)}"
        
        return {
            'response': response,
            'tools_used': tools_used,
            'files_created': files_created,
            'agent_state': 'active'
        }
    
    async def tool_scan_markets(self) -> Dict[str, Any]:
        """Scan watched symbols for signals"""
        try:
            memory = self.get_memory()
            symbols = memory.get('watched_symbols', [])
            
            scan_results = []
            
            for symbol in symbols:
                # Simulate market data analysis
                # In production, this would connect to real market APIs
                import random
                
                price_change = random.uniform(-0.05, 0.05)  # -5% to +5%
                volume_surge = random.uniform(0.8, 2.5)     # 80% to 250% normal volume
                sentiment_score = random.uniform(-1.0, 1.0)  # -1 (bearish) to 1 (bullish)
                
                # Calculate signal strength based on multiple factors
                signal_strength = 0
                description_parts = []
                
                if abs(price_change) > 0.03:  # > 3% move
                    signal_strength += 0.3
                    direction = "surge" if price_change > 0 else "drop"
                    description_parts.append(f"Price {direction} {abs(price_change):.1%}")
                
                if volume_surge > 1.5:  # 50% above normal
                    signal_strength += 0.3
                    description_parts.append(f"Volume spike {volume_surge:.1f}x")
                
                if abs(sentiment_score) > 0.6:  # Strong sentiment
                    signal_strength += 0.2
                    mood = "bullish" if sentiment_score > 0 else "bearish"
                    description_parts.append(f"Sentiment {mood}")
                
                # Random pattern detection
                if random.random() > 0.7:  # 30% chance of pattern
                    patterns = ["breakout", "reversal", "consolidation", "momentum"]
                    pattern = random.choice(patterns)
                    signal_strength += 0.2
                    description_parts.append(f"{pattern.title()} pattern")
                
                description = " | ".join(description_parts) if description_parts else "Normal market behavior"
                
                scan_results.append({
                    'symbol': symbol,
                    'price_change': price_change,
                    'volume_surge': volume_surge,
                    'sentiment_score': sentiment_score,
                    'signal_strength': min(signal_strength, 1.0),  # Cap at 100%
                    'description': description,
                    'timestamp': datetime.now().isoformat()
                })
            
            # Update memory with scan results
            memory['last_scan'] = datetime.now().isoformat()
            memory['detected_signals'] = [s for s in scan_results if s['signal_strength'] > memory['signal_threshold']]
            self.save_memory(memory)
            
            return {'success': True, 'data': scan_results}
            
        except Exception as e:
            logger.error(f"Market scan error: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    async def tool_fetch_news(self) -> Dict[str, Any]:
        """Fetch market news and information"""
        try:
            # Simulate news fetching - in production, integrate with real news APIs
            import random
            
            headlines = [
                "Federal Reserve signals potential rate adjustments amid inflation concerns",
                "Tech sector shows resilience despite market volatility",
                "Energy prices fluctuate on geopolitical developments", 
                "Consumer spending patterns shift in Q4 earnings reports",
                "Market analysts debate correction vs. consolidation phase",
                "Cryptocurrency adoption accelerates in institutional sector",
                "Supply chain optimizations drive industrial efficiency gains"
            ]
            
            news_items = []
            for i in range(random.randint(3, 7)):
                headline = random.choice(headlines)
                sentiment = random.uniform(-0.5, 0.5)
                news_items.append({
                    'headline': headline,
                    'sentiment': sentiment,
                    'source': random.choice(['Reuters', 'Bloomberg', 'MarketWatch', 'CNBC']),
                    'timestamp': (datetime.now() - timedelta(hours=random.randint(1, 24))).isoformat()
                })
            
            return {'success': True, 'data': news_items}
            
        except Exception as e:
            logger.error(f"News fetch error: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    async def tool_analyze_sentiment(self, news_data: List[Dict]) -> Dict[str, Any]:
        """Analyze overall market sentiment from news"""
        try:
            if not news_data:
                return {'overall_sentiment': 'neutral', 'confidence': 0.0}
            
            sentiments = [item.get('sentiment', 0) for item in news_data]
            avg_sentiment = sum(sentiments) / len(sentiments)
            confidence = 1.0 - (abs(avg_sentiment) * 0.5)  # Lower confidence for extreme sentiments
            
            if avg_sentiment > 0.1:
                overall = 'bullish'
            elif avg_sentiment < -0.1:
                overall = 'bearish'
            else:
                overall = 'neutral'
            
            return {
                'overall_sentiment': overall,
                'confidence': confidence,
                'raw_score': avg_sentiment
            }
            
        except Exception as e:
            logger.error(f"Sentiment analysis error: {str(e)}")
            return {'overall_sentiment': 'unknown', 'confidence': 0.0}
    
    async def autonomous_scan(self) -> None:
        """Autonomous background market scanning"""
        try:
            memory = self.get_memory()
            last_scan = memory.get('last_scan')
            
            # Check if enough time has passed since last scan
            if last_scan:
                last_scan_time = datetime.fromisoformat(last_scan)
                if datetime.now() - last_scan_time < timedelta(seconds=memory.get('scan_frequency', 300)):
                    return
            
            # Perform autonomous scan
            logger.info("Kyle performing autonomous market scan...")
            scan_result = await self.tool_scan_markets()
            
            if scan_result['success']:
                # Check for high-confidence signals
                strong_signals = [s for s in scan_result['data'] if s['signal_strength'] > 0.8]
                
                if strong_signals:
                    logger.info(f"Kyle detected {len(strong_signals)} strong signals")
                    # In production, could send alerts via Telegram or other channels
                    
        except Exception as e:
            logger.error(f"Autonomous scan error: {str(e)}")
    
    async def autonomous_task(self) -> None:
        """Kyle's autonomous background task"""
        await self.autonomous_scan()