import csv
import os
from datetime import datetime
from src.config.config import Config

class CSVLogger:
    HEADERS = ["Timestamp", "Date", "Type", "Token", "Amount", "Price", "Total_SOL", "Fee_SOL", "PnL_SOL", "Reason"]

    @staticmethod
    def log_trade(trade_type, token, amount, price, total, fee=0.0, pnl=0.0, reason=""):
        file_exists = os.path.isfile(Config.TRADES_LOG)
        
        with open(Config.TRADES_LOG, 'a', newline='') as f:
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow(CSVLogger.HEADERS)
            
            writer.writerow([
                datetime.now().isoformat(),
                datetime.now().strftime("%Y-%m-%d"),
                trade_type,
                token,
                amount,
                price,
                total,
                fee,
                pnl,
                reason
            ])
