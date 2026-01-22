import requests
from src.config.config import Config
from src.utils.logger import logger

class TelegramBot:
    def __init__(self):
        self.token = Config.TELEGRAM_BOT_TOKEN
        self.chat_id = Config.CHAT_ID
        self.base_url = f"https://api.telegram.org/bot{self.token}"

    def send_message(self, message: str):
        if not self.token or not self.chat_id:
            # logger.warning("Telegram token or chat_id not set.")
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

    def notify_buy(self, mint, amount_sol, price):
        self.send_message(f"🟢 **BUY ALERT**\nToken: `{mint}`\nAmount: {amount_sol} SOL\nPrice: {price}")

    def notify_sell(self, mint, amount_sol, price, reason, pnl_pct):
        self.send_message(f"🔴 **SELL ALERT**\nToken: `{mint}`\nReason: {reason}\nPnL: {pnl_pct*100:.2f}%")

    def notify_tax(self, amount_sol):
        self.send_message(f"🏛️ **TAX DEPOSIT**\nSent {amount_sol} SOL to Vault.")
