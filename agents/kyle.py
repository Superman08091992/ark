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
from reasoning.kyle_reasoner import KyleReasoner
from reasoning.intra_agent_reasoner import ReasoningDepth
import logging

logger = logging.getLogger(__name__)

class KyleAgent(BaseAgent):
    """Kyle - The Seer: Curiosity and signal detection"""
    
    def __init__(self):
        super().__init__("Kyle", "The Seer")
        self._agent_tools = ['scan_markets', 'fetch_news', 'analyze_sentiment', 'detect_signals']
        
        # Initialize Kyle-specific hierarchical reasoner
        # With no speed constraints, we use DEEP reasoning by default
        self.intra_reasoner = KyleReasoner(
            default_depth=ReasoningDepth.DEEP,
            enable_tree_of_selfs=True,
            max_branches_per_level=5
        )
        
        # Initialize Kyle's personality and default memory
        memory = self.get_memory()
        if not memory:
            memory = {
                'watched_symbols': ['SPY', 'QQQ', 'AAPL', 'TSLA', 'BTC-USD'],
                'scan_frequency': 300,  # 5 minutes
                'signal_threshold': 0.7,
                'last_scan': None,
                'detected_signals': [],
                'market_sentiment': 'neutral',
                'reasoning_mode': 'DEEP'  # Can be SHALLOW, MODERATE, DEEP, EXHAUSTIVE
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
        """Scan watched symbols for signals using hierarchical reasoning"""
        try:
            memory = self.get_memory()
            symbols = memory.get('watched_symbols', [])
            reasoning_mode = memory.get('reasoning_mode', 'DEEP')
            
            # Determine reasoning depth
            depth_map = {
                'SHALLOW': ReasoningDepth.SHALLOW,
                'MODERATE': ReasoningDepth.MODERATE,
                'DEEP': ReasoningDepth.DEEP,
                'EXHAUSTIVE': ReasoningDepth.EXHAUSTIVE
            }
            reasoning_depth = depth_map.get(reasoning_mode, ReasoningDepth.DEEP)
            
            scan_results = []
            
            for symbol in symbols:
                # Gather raw market data
                # In production, this would connect to real market APIs
                import random
                
                price_change = random.uniform(-0.05, 0.05)  # -5% to +5%
                volume_surge = random.uniform(0.8, 2.5)     # 80% to 250% normal volume
                sentiment_score = random.uniform(-1.0, 1.0)  # -1 (bearish) to 1 (bullish)
                
                # Prepare raw signal data for hierarchical reasoning
                raw_signal_data = {
                    'symbol': symbol,
                    'price_change': price_change,
                    'volume_surge': volume_surge,
                    'sentiment_score': sentiment_score,
                    'timestamp': datetime.now().isoformat()
                }
                
                # Use hierarchical reasoning to analyze signal
                reasoning_context = {
                    'agent_role': 'market_scanner',
                    'threshold': memory.get('signal_threshold', 0.7),
                    'historical_patterns': memory.get('detected_signals', [])[-10:],  # Last 10 signals
                    'market_sentiment': memory.get('market_sentiment', 'neutral')
                }
                
                # Execute hierarchical reasoning
                decision = await self.intra_reasoner.reason(
                    input_data=raw_signal_data,
                    depth=reasoning_depth,
                    context=reasoning_context
                )
                
                # Extract reasoning results from Level 5 decision output
                signal_analysis = decision.final_decision
                if isinstance(signal_analysis, dict):
                    # Kyle reasoner returns decision with 'selected_option'
                    selected_option = signal_analysis.get('selected_option', {})
                    signal_strength = selected_option.get('signal_strength', decision.confidence)
                    description = selected_option.get('description', 'Signal analyzed')
                    
                    # Extract patterns from Level 2 analysis
                    patterns = []
                    for level in decision.cognitive_levels:
                        if level.level == 2 and hasattr(level, 'output_data'):
                            analysis_output = level.output_data
                            if isinstance(analysis_output, dict):
                                detected_patterns = analysis_output.get('patterns', [])
                                patterns.extend([p.get('type', 'unknown') for p in detected_patterns])
                else:
                    # Fallback if reasoning returns non-dict
                    signal_strength = decision.confidence
                    description = f"Hierarchical analysis (confidence: {decision.confidence:.2f})"
                    patterns = []
                
                # Build comprehensive result with reasoning chain
                scan_results.append({
                    'symbol': symbol,
                    'price_change': price_change,
                    'volume_surge': volume_surge,
                    'sentiment_score': sentiment_score,
                    'signal_strength': signal_strength,
                    'description': description,
                    'patterns': patterns,
                    'timestamp': datetime.now().isoformat(),
                    'reasoning': {
                        'depth': reasoning_depth.name,
                        'confidence': decision.confidence,
                        'alternatives_considered': decision.alternatives_considered,
                        'duration_ms': decision.total_duration_ms,
                        'cognitive_path': [
                            {'level': cl.level, 'name': cl.name, 'confidence': cl.confidence}
                            for cl in decision.cognitive_levels
                        ]
                    }
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
    
    def get_reasoning_statistics(self) -> Dict[str, Any]:
        """Get Kyle's hierarchical reasoning statistics"""
        return {
            'agent': 'Kyle',
            'total_decisions': self.intra_reasoner.total_decisions,
            'total_reasoning_time_ms': self.intra_reasoner.total_reasoning_time,
            'avg_reasoning_time_ms': (
                self.intra_reasoner.total_reasoning_time / self.intra_reasoner.total_decisions
                if self.intra_reasoner.total_decisions > 0 else 0
            ),
            'history_size': len(self.intra_reasoner.reasoning_history),
            'default_depth': self.intra_reasoner.default_depth.name,
            'tree_of_selfs_enabled': self.intra_reasoner.enable_tree_of_selfs
        }
    
    async def set_reasoning_mode(self, mode: str) -> Dict[str, Any]:
        """Set Kyle's reasoning depth mode"""
        valid_modes = ['SHALLOW', 'MODERATE', 'DEEP', 'EXHAUSTIVE']
        if mode.upper() not in valid_modes:
            return {
                'success': False,
                'error': f'Invalid mode. Must be one of: {", ".join(valid_modes)}'
            }
        
        memory = self.get_memory()
        memory['reasoning_mode'] = mode.upper()
        self.save_memory(memory)
        
        return {
            'success': True,
            'message': f'Kyle reasoning mode set to {mode.upper()}',
            'current_mode': mode.upper()
        }