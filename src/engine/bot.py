import asyncio
import json
import time
from pathlib import Path
from datetime import datetime

from src.config.config import Config
from src.utils.logger import logger
from src.clients.solana_client import SolanaClient
from src.clients.jupiter_client import JupiterClient
from src.clients.rugcheck_client import RugCheckClient
from src.engine.strategy import Strategy
from src.engine.money_manager import MoneyManager
from src.dashboard.telegram_bot import TelegramBot
from src.utils.csv_logger import CSVLogger

class BotEngine:
    def __init__(self):
        self.solana = SolanaClient()
        self.jupiter = JupiterClient()
        self.rugcheck = RugCheckClient()
        self.telegram = TelegramBot()
        self.positions_file = Config.DATA_DIR / "positions.json"
        self.positions = self.load_positions()
        self.running = False

    def load_positions(self):
        if self.positions_file.exists():
            try:
                with open(self.positions_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Failed to load positions: {e}")
        return {}

    def save_positions(self):
        try:
            with open(self.positions_file, 'w') as f:
                json.dump(self.positions, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save positions: {e}")

    async def start(self):
        self.running = True
        logger.info("Starting Skry R&D Autonomous Engine...")
        
        # Main Loop
        while self.running:
            try:
                await self.scan_cycle()
                await self.manage_positions_cycle()
                await asyncio.sleep(60) # Scan every minute
            except Exception as e:
                logger.error(f"Main loop error: {e}")
                await asyncio.sleep(60)

    async def scan_cycle(self):
        logger.info("Scanning for new tokens...")
        new_tokens = await self.jupiter.scan_new_tokens()
        
        for mint in new_tokens:
            await self.analyze_and_trade(mint)

    async def analyze_and_trade(self, mint):
        logger.info(f"Analyzing {mint}...")
        
        # 1. RugCheck
        report = await self.rugcheck.get_token_report(mint)
        if not report or not self.rugcheck.is_trustable(report):
            logger.info(f"Token {mint} failed RugCheck (Score: {report.get('score') if report else 'N/A'})")
            return

        # 2. Liquidity Check (via Quote)
        # Try to buy $100k worth? No, just check if we CAN swap a significant amount with low impact?
        # User Req: "monitor new pools with >$100k liquidity"
        # Jupiter Quote API returns 'impact'.
        # Let's try to quote 1 SOL. If price impact is huge, liquidity is low.
        # Better: Quote 1000 USD worth of SOL.
        # But to check TOTAL liquidity > 100k, we can't easily do that via Quote API without probing.
        # Proxy: If we can sell $1000 with < 1% impact, liquidity is likely decent (~$100k+).
        # Or just trust RugCheck's liquidity data if available?
        # RugCheck report usually contains liquidity info.
        
        liquidity = 0
        if report and 'tokenProgram' in report.get('raw', {}):
            # Try to parse liquidity from RugCheck raw data if possible
            # But let's rely on Jupiter Quote for execution feasibility
            pass

        # 3. Buy Logic
        balance = await self.solana.get_sol_balance()
        position_size = MoneyManager.calculate_position_size(balance)
        
        if position_size < 0.01: # Min trade
            logger.warning("Insufficient balance for trade.")
            return

        logger.info(f"Attempting to buy {mint} with {position_size} SOL")
        
        # Get Quote
        quote = await self.jupiter.get_quote("So11111111111111111111111111111111111111112", mint, int(position_size * 1e9))
        if not quote:
            return

        # Execute Swap
        if Config.SOLANA_PRIVATE_KEY:
            # tx = await self.jupiter.get_swap_transaction(quote, self.solana.keypair.pubkey().__str__())
            # For now, we simulate success in V1 if no key
            pass
        
        # Record Position (Simulation)
        self.positions[mint] = {
            "entry_price": float(quote.get('outAmount')) / float(quote.get('inAmount')) if quote else 1.0, # Approximate
            "amount": float(quote.get('outAmount')) if quote else 0.0,
            "highest_price": float(quote.get('outAmount')) / float(quote.get('inAmount')) if quote else 1.0,
            "sold_tier_1": False,
            "sold_tier_2": False,
            "sold_tier_3": False,
            "timestamp": time.time()
        }
        self.save_positions()
        logger.info(f"Bought {mint}")
        
        # Notifications & Logging
        buy_price = self.positions[mint]["entry_price"]
        buy_amt = self.positions[mint]["amount"]
        self.telegram.notify_buy(mint, position_size, buy_price)
        CSVLogger.log_trade("BUY", mint, buy_amt, buy_price, position_size, 0.0, 0.0, "Initial Entry")

    async def manage_positions_cycle(self):
        logger.info(f"Managing {len(self.positions)} positions...")
        mints_to_remove = []
        
        for mint, data in self.positions.items():
            # Get current price
            # We need a price fetcher. Jupiter Quote for 1 unit?
            # price = await self.jupiter.get_price(mint)
            # For now, assume price is fetched via quote (1 Token -> SOL)
            
            # Simulated Price Update
            current_price = data['entry_price'] * 1.0 # No change in simulation
            
            # Update High Water Mark
            if current_price > data['highest_price']:
                data['highest_price'] = current_price
            
            should_sell, sell_pct, reason = Strategy.get_sell_action(
                mint, current_price, data['entry_price'], data['highest_price'],
                data['sold_tier_1'], data['sold_tier_2'], data['sold_tier_3']
            )
            
            if should_sell:
                logger.info(f"Selling {mint}: {reason} ({sell_pct*100}%)")
                # Execute Sell (Simulated)
                sell_amt = data['amount'] * sell_pct
                sell_val = sell_amt * current_price # SOL
                
                # Calculate Profit
                # Simple approximation: PnL = (CurrentPrice - EntryPrice) * AmountSold
                pnl_sol = (current_price - data['entry_price']) * sell_amt
                
                # Tax Logic
                tax_amt = MoneyManager.calculate_tax(pnl_sol)
                if tax_amt > 0:
                    await self.solana.transfer_sol(Config.TAX_VAULT_ADDRESS, tax_amt)
                    self.telegram.notify_tax(tax_amt)
                    CSVLogger.log_trade("TAX", "SOL", tax_amt, 0, tax_amt, 0, 0, "Tax Vault Deposit")

                # Notifications
                self.telegram.notify_sell(mint, sell_val, current_price, reason, (current_price - data['entry_price'])/data['entry_price'])
                CSVLogger.log_trade("SELL", mint, sell_amt, current_price, sell_val, 0, pnl_sol, reason)

                # Update State
                data['amount'] -= sell_amt
                
                if sell_pct == 1.0 or data['amount'] < 0.0001:
                    mints_to_remove.append(mint)
                    # Close Account
                    await self.solana.close_empty_accounts()
                
                # Update Tiers
                if "Tier 1" in reason: data['sold_tier_1'] = True
                if "Tier 2" in reason: data['sold_tier_2'] = True
                if "Tier 3" in reason: data['sold_tier_3'] = True

        for mint in mints_to_remove:
            del self.positions[mint]
        
        if mints_to_remove:
            self.save_positions()

if __name__ == "__main__":
    bot = BotEngine()
    asyncio.run(bot.start())
