import requests
import asyncio
from src.config.config import Config
from src.utils.logger import logger

class TelegramBot:
    def __init__(self):
        self.token = Config.TELEGRAM_BOT_TOKEN
        self.chat_id = Config.CHAT_ID
        self.base_url = f"https://api.telegram.org/bot{self.token}"
        self.offset = 0
        self.bot_engine = None  # Reference to the bot engine

    def set_engine(self, engine):
        self.bot_engine = engine

    def send_message(self, message: str):
        if not self.token or not self.chat_id:
            return

        url = f"{self.base_url}/sendMessage"
        payload = {
            "chat_id": self.chat_id,
            "text": message,
            "parse_mode": "Markdown"
        }
        try:
            requests.post(url, json=payload, timeout=5)
        except Exception as e:
            logger.error(f"Failed to send Telegram message: {e}")

    async def poll_updates(self):
        """Simple long-polling for commands"""
        if not self.token: 
            return

        while True:
            try:
                url = f"{self.base_url}/getUpdates"
                params = {"offset": self.offset, "timeout": 30}
                # Use requests in thread executor to not block asyncio loop
                loop = asyncio.get_event_loop()
                resp = await loop.run_in_executor(None, lambda: requests.get(url, params=params, timeout=35))
                
                if resp.status_code == 200:
                    data = resp.json()
                    if data["ok"]:
                        for result in data["result"]:
                            self.offset = result["update_id"] + 1
                            await self.handle_update(result)
            except Exception as e:
                logger.error(f"Telegram polling error: {e}")
                await asyncio.sleep(5)
            
            await asyncio.sleep(1)

    async def handle_update(self, update):
        if "message" not in update: return
        msg = update["message"]
        text = msg.get("text", "")
        chat_id = str(msg.get("chat", {}).get("id"))

        # Security: Only respond to admin
        if chat_id != str(self.chat_id):
            return

        if text == "/status":
            if self.bot_engine:
                status = "🟢 Running" if self.bot_engine.running else "🔴 Stopped"
                pos_count = len(self.bot_engine.positions)
                await self.send_message_async(f"**Bot Status**: {status}\nPositions: {pos_count}")
            else:
                await self.send_message_async("Bot engine not connected.")
        
        elif text == "/start_bot":
            if self.bot_engine:
                self.bot_engine.running = True
                # Restart loop if it was broken? 
                # Actually, the loop checks 'running'. If it exited, we can't restart easily without re-triggering start()
                # But typically 'running' controls the while loop.
                await self.send_message_async("✅ Bot resumed.")
        
        elif text == "/stop_bot":
            if self.bot_engine:
                self.bot_engine.running = False
                await self.send_message_async("🛑 Bot paused (finishing current cycle).")

        elif text == "/balance":
            if self.bot_engine:
                bal = await self.bot_engine.solana.get_sol_balance()
                await self.send_message_async(f"💰 **Balance**: {bal:.4f} SOL")

    async def send_message_async(self, message):
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, lambda: self.send_message(message))

    def notify_buy(self, mint, amount_sol, price):
        self.send_message(f"🟢 **BUY ALERT**\nToken: `{mint}`\nAmount: {amount_sol} SOL\nPrice: {price}")

    def notify_sell(self, mint, amount_sol, price, reason, pnl_pct):
        self.send_message(f"🔴 **SELL ALERT**\nToken: `{mint}`\nReason: {reason}\nPnL: {pnl_pct*100:.2f}%")

    def notify_tax(self, amount_sol):
        self.send_message(f"🏛️ **TAX DEPOSIT**\nSent {amount_sol} SOL to Vault.")
