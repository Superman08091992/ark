"""
Telegram Service

Message formatting and delivery for @slavetotradesbot

Features:
- Rich message formatting with emojis
- Trade setup signal formatting
- Pattern confidence display
- Risk metrics display
- Entry/Stop/Target display
- Markdown formatting support

Integration:
- Connects to Unified Signal Router (stage 6)
- Subscribes to signal events via AgentBus
- Formats and sends to Telegram Bot API

Author: ARK Trading Intelligence
Version: 1.0.0
"""

import logging
import asyncio
import os
from typing import Dict, Any, Optional, List
from datetime import datetime

import aiohttp

logger = logging.getLogger(__name__)


class TelegramService:
    """
    Telegram bot service for trading signal notifications.
    
    Formats and sends rich trading signals to @slavetotradesbot.
    """
    
    def __init__(self, bot_token: Optional[str] = None, chat_id: Optional[str] = None):
        """
        Initialize Telegram service.
        
        Args:
            bot_token: Telegram Bot API token (from BotFather)
            chat_id: Default chat ID for sending messages
        """
        self.bot_token = bot_token or os.getenv('TELEGRAM_BOT_TOKEN')
        self.chat_id = chat_id or os.getenv('TELEGRAM_CHAT_ID')
        
        self.api_base_url = f"https://api.telegram.org/bot{self.bot_token}" if self.bot_token else None
        
        self._session: Optional[aiohttp.ClientSession] = None
        self._initialized = False
    
    async def initialize(self) -> bool:
        """
        Initialize Telegram service.
        
        Returns:
            bool: True if successfully initialized
        """
        if not self.bot_token:
            logger.warning("⚠️ TELEGRAM_BOT_TOKEN not set - Telegram notifications disabled")
            return False
        
        if not self.chat_id:
            logger.warning("⚠️ TELEGRAM_CHAT_ID not set - using broadcast mode")
        
        try:
            self._session = aiohttp.ClientSession()
            
            # Test connection
            me = await self.get_me()
            if me:
                logger.info(f"✅ Telegram service initialized - Bot: @{me.get('username', 'unknown')}")
                self._initialized = True
                return True
            else:
                logger.error("❌ Failed to connect to Telegram API")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error initializing Telegram service: {str(e)}")
            return False
    
    async def close(self):
        """Close HTTP session"""
        if self._session:
            await self._session.close()
            self._session = None
    
    async def get_me(self) -> Optional[Dict]:
        """
        Get bot information using getMe API.
        
        Returns:
            Dict with bot info or None if failed
        """
        if not self.api_base_url:
            return None
        
        try:
            async with self._session.get(f"{self.api_base_url}/getMe") as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data.get('result')
                else:
                    logger.error(f"❌ getMe failed: {resp.status}")
                    return None
        except Exception as e:
            logger.error(f"❌ Error calling getMe: {str(e)}")
            return None
    
    async def send_message(
        self,
        text: str,
        chat_id: Optional[str] = None,
        parse_mode: str = "Markdown",
        disable_web_page_preview: bool = True
    ) -> bool:
        """
        Send a message via Telegram Bot API.
        
        Args:
            text: Message text
            chat_id: Target chat ID (uses default if None)
            parse_mode: 'Markdown' or 'HTML'
            disable_web_page_preview: Disable link previews
        
        Returns:
            bool: True if sent successfully
        """
        if not self._initialized:
            logger.warning("⚠️ Telegram service not initialized - message not sent")
            return False
        
        target_chat = chat_id or self.chat_id
        if not target_chat:
            logger.error("❌ No chat_id provided and no default set")
            return False
        
        try:
            payload = {
                "chat_id": target_chat,
                "text": text,
                "parse_mode": parse_mode,
                "disable_web_page_preview": disable_web_page_preview
            }
            
            async with self._session.post(
                f"{self.api_base_url}/sendMessage",
                json=payload
            ) as resp:
                if resp.status == 200:
                    logger.info(f"✅ Sent Telegram message to {target_chat}")
                    return True
                else:
                    error = await resp.text()
                    logger.error(f"❌ sendMessage failed: {resp.status} - {error}")
                    return False
                    
        except Exception as e:
            logger.error(f"❌ Error sending Telegram message: {str(e)}")
            return False
    
    async def send_trade_signal(
        self,
        trade_setup: Dict[str, Any],
        chat_id: Optional[str] = None
    ) -> bool:
        """
        Format and send a trading signal to Telegram.
        
        Args:
            trade_setup: Complete trade setup dictionary
            chat_id: Target chat ID (uses default if None)
        
        Returns:
            bool: True if sent successfully
        """
        message = self.format_trade_signal(trade_setup)
        return await self.send_message(message, chat_id=chat_id)
    
    def format_trade_signal(self, trade_setup: Dict[str, Any]) -> str:
        """
        Format trade setup as rich Telegram message.
        
        Uses emojis, Markdown formatting, and structured layout.
        
        Args:
            trade_setup: Complete trade setup dictionary
        
        Returns:
            str: Formatted Markdown message
        """
        # Extract data
        symbol = trade_setup.get('symbol', 'UNKNOWN')
        direction = trade_setup.get('direction', 'unknown').upper()
        price = trade_setup.get('price', 0.0)
        pattern = trade_setup.get('pattern', 'Unknown Pattern')
        confidence = trade_setup.get('confidence', 0.0)
        
        # Execution plan
        exec_plan = trade_setup.get('execution_plan', {})
        entry = exec_plan.get('entry_price', price)
        stop_loss = exec_plan.get('stop_loss', 0.0)
        targets = exec_plan.get('targets', [])
        position_size = exec_plan.get('position_size_percent', 0.0)
        rr_ratio = exec_plan.get('risk_reward_ratio', 0.0)
        
        # Scores
        scores = trade_setup.get('scores', {})
        quality_score = scores.get('quality_score', 0.0)
        technical = scores.get('technical', 0.0)
        fundamental = scores.get('fundamental', 0.0)
        
        # Direction emoji
        direction_emoji = "🟢" if direction == "LONG" else "🔴"
        
        # Confidence bars
        confidence_bars = self._confidence_bars(confidence)
        quality_bars = self._confidence_bars(quality_score)
        
        # Build message
        lines = [
            f"{direction_emoji} *{symbol} - {direction} SIGNAL* {direction_emoji}",
            "",
            f"📊 *Pattern*: {pattern}",
            f"🎯 *Confidence*: {confidence:.1%} {confidence_bars}",
            f"⭐ *Quality Score*: {quality_score:.1%} {quality_bars}",
            "",
            f"💰 *Entry*: ${entry:.2f}",
            f"🛑 *Stop Loss*: ${stop_loss:.2f} ({self._calc_pct(stop_loss, entry):.1f}%)",
            ""
        ]
        
        # Targets
        if targets:
            lines.append("🎯 *Targets*:")
            for i, target in enumerate(targets[:3], 1):  # Show first 3 targets
                target_price = target.get('price', 0.0)
                target_pct = target.get('percentage', 0.0)
                exit_portion = target.get('exit_portion', 0.0)
                lines.append(
                    f"   T{i}: ${target_price:.2f} (+{target_pct:.1%}) - "
                    f"Exit {exit_portion:.0%}"
                )
            lines.append("")
        
        # Risk metrics
        lines.extend([
            "📈 *Risk Metrics*:",
            f"   • Position Size: {position_size:.1f}%",
            f"   • Risk/Reward: 1:{rr_ratio:.2f}",
            f"   • Max Risk: {self._calc_pct(stop_loss, entry):.1f}%",
            ""
        ])
        
        # Score breakdown
        if technical > 0 or fundamental > 0:
            lines.extend([
                "📊 *Score Breakdown*:",
                f"   • Technical: {technical:.1%}",
                f"   • Fundamental: {fundamental:.1%}",
                ""
            ])
        
        # Catalyst
        catalyst = trade_setup.get('catalyst')
        if catalyst:
            lines.extend([
                f"📰 *Catalyst*:",
                f"   {catalyst}",
                ""
            ])
        
        # Status
        status = trade_setup.get('status', 'unknown').upper()
        status_emoji = "✅" if status == "APPROVED" else "⏳"
        lines.append(f"{status_emoji} *Status*: {status}")
        
        # Footer
        setup_id = trade_setup.get('setup_id', 'unknown')[:8]
        correlation_id = trade_setup.get('correlation_id', 'unknown')[:8]
        lines.extend([
            "",
            f"🔖 Setup: `{setup_id}` | Trace: `{correlation_id}`",
            "",
            "⚠️ _Not financial advice. Trade at your own risk._"
        ])
        
        return "\n".join(lines)
    
    def _confidence_bars(self, confidence: float) -> str:
        """
        Generate visual confidence bars.
        
        0.0-0.4: ▪️▪️▪️▪️▪️ (5 empty)
        0.4-0.6: ▪️▪️▪️🟨🟨 (3 empty, 2 yellow)
        0.6-0.8: ▪️🟨🟨🟩🟩 (1 empty, 2 yellow, 2 green)
        0.8-1.0: 🟩🟩🟩🟩🟩 (5 green)
        """
        if confidence >= 0.8:
            return "🟩🟩🟩🟩🟩"
        elif confidence >= 0.7:
            return "🟩🟩🟩🟩▪️"
        elif confidence >= 0.6:
            return "🟩🟩🟩▪️▪️"
        elif confidence >= 0.5:
            return "🟨🟨🟨▪️▪️"
        elif confidence >= 0.4:
            return "🟨🟨▪️▪️▪️"
        else:
            return "▪️▪️▪️▪️▪️"
    
    def _calc_pct(self, value: float, reference: float) -> float:
        """Calculate percentage difference"""
        if reference == 0:
            return 0.0
        return ((value - reference) / reference) * 100
    
    def format_pattern_analysis(self, analysis: Dict[str, Any]) -> str:
        """
        Format pattern analysis result (from /analyze endpoint).
        
        Args:
            analysis: Pattern analysis response
        
        Returns:
            str: Formatted Markdown message
        """
        symbol = analysis.get('symbol', 'UNKNOWN')
        direction = analysis.get('direction', 'unknown').upper()
        patterns = analysis.get('patterns', [])
        best_pattern = analysis.get('best_pattern')
        recommendation = analysis.get('recommendation', 'unknown').upper()
        
        direction_emoji = "🟢" if direction == "LONG" else "🔴"
        
        lines = [
            f"{direction_emoji} *{symbol} Pattern Analysis* {direction_emoji}",
            "",
            f"📊 *Direction*: {direction}",
            f"💡 *Recommendation*: {recommendation}",
            ""
        ]
        
        if best_pattern:
            lines.extend([
                f"🎯 *Best Pattern*: {best_pattern.get('pattern_name')}",
                f"   Confidence: {best_pattern.get('confidence', 0):.1%}",
                ""
            ])
        
        if patterns:
            lines.append("📋 *All Matches*:")
            for i, pattern in enumerate(patterns[:5], 1):
                name = pattern.get('pattern_name', 'Unknown')
                conf = pattern.get('confidence', 0.0)
                lines.append(f"   {i}. {name} - {conf:.1%}")
            lines.append("")
        else:
            lines.append("❌ No patterns matched")
            lines.append("")
        
        lines.append("⚠️ _Analysis only - not a trade signal_")
        
        return "\n".join(lines)
    
    def format_error_alert(
        self,
        error_message: str,
        correlation_id: Optional[str] = None,
        severity: str = "ERROR"
    ) -> str:
        """
        Format error alert message.
        
        Args:
            error_message: Error description
            correlation_id: Trace ID
            severity: ERROR, WARNING, CRITICAL
        
        Returns:
            str: Formatted Markdown message
        """
        emoji_map = {
            "CRITICAL": "🚨",
            "ERROR": "❌",
            "WARNING": "⚠️"
        }
        emoji = emoji_map.get(severity, "⚠️")
        
        lines = [
            f"{emoji} *{severity}* {emoji}",
            "",
            f"📝 *Message*: {error_message}",
            ""
        ]
        
        if correlation_id:
            lines.append(f"🔖 Trace: `{correlation_id}`")
            lines.append("")
        
        lines.append(f"🕐 {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}")
        
        return "\n".join(lines)


# Singleton instance
_telegram_service: Optional[TelegramService] = None


def get_telegram_service() -> TelegramService:
    """
    Get singleton Telegram service instance.
    
    Returns:
        TelegramService: Singleton instance
    """
    global _telegram_service
    
    if _telegram_service is None:
        _telegram_service = TelegramService()
    
    return _telegram_service


# Example usage
async def main():
    """Example usage of Telegram service"""
    
    # Initialize service
    telegram = get_telegram_service()
    
    if not await telegram.initialize():
        print("❌ Failed to initialize Telegram service")
        print("Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID environment variables")
        return
    
    # Example trade setup
    trade_setup = {
        "setup_id": "abc12345-1234-5678-9abc-123456789abc",
        "correlation_id": "xyz98765-5678-1234-5678-987654321xyz",
        "symbol": "TSLA",
        "direction": "long",
        "price": 250.50,
        "pattern": "Squeezer (Low Float Big Gainer)",
        "confidence": 0.85,
        "catalyst": "Strong Q4 earnings beat + record EV deliveries announced",
        "scores": {
            "quality_score": 0.78,
            "technical": 0.82,
            "fundamental": 0.75,
            "catalyst": 0.80,
            "sentiment": 0.72
        },
        "execution_plan": {
            "entry_price": 251.00,
            "stop_loss": 238.00,
            "targets": [
                {"price": 270.00, "percentage": 0.075, "exit_portion": 0.33},
                {"price": 285.00, "percentage": 0.135, "exit_portion": 0.33},
                {"price": 305.00, "percentage": 0.215, "exit_portion": 0.34}
            ],
            "position_size_percent": 8.5,
            "risk_reward_ratio": 3.2
        },
        "status": "approved"
    }
    
    # Send signal
    success = await telegram.send_trade_signal(trade_setup)
    
    if success:
        print("✅ Signal sent successfully!")
    else:
        print("❌ Failed to send signal")
    
    # Close service
    await telegram.close()


if __name__ == "__main__":
    asyncio.run(main())
