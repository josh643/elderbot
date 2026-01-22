from datetime import datetime
from src.config.config import Config

class Strategy:
    @staticmethod
    def get_sell_action(
        token_address: str,
        current_price: float,
        entry_price: float,
        highest_price: float,
        sold_tier_1: bool,
        sold_tier_2: bool,
        sold_tier_3: bool
    ):
        """
        Determine if we should sell based on strategy.
        Returns: (should_sell: bool, sell_pct: float, reason: str)
        """
        gain_pct = (current_price - entry_price) / entry_price
        is_usor = token_address == Config.USOR_ADDRESS
        
        # Check Date Guard (Jan 25 - Feb 5)
        now = datetime.now()
        # Assuming 2026 based on env context, but safe to check month/day
        # Logic: If within window, ONLY Stop Loss allowed.
        # Window: Jan 25 to Feb 5
        in_lockdown = False
        if now.month == 1 and now.day >= 25:
            in_lockdown = True
        elif now.month == 2 and now.day <= 5:
            in_lockdown = True
            
        if is_usor:
            return Strategy._usor_logic(current_price, highest_price, gain_pct, in_lockdown)
        else:
            return Strategy._standard_logic(gain_pct, current_price, highest_price, sold_tier_1, sold_tier_2, sold_tier_3, in_lockdown)

    @staticmethod
    def _usor_logic(current_price, highest_price, gain_pct, in_lockdown):
        # USOR: Sell 0% until 5x.
        # Trailing Stop Loss: 30%
        
        # Check Trailing Stop
        drop_from_high = (highest_price - current_price) / highest_price
        if drop_from_high >= Config.USOR_TRAILING_STOP:
            return True, 1.0, "USOR Trailing Stop Hit"

        # If in lockdown, NO taking profits, only Stop Loss (handled above)
        if in_lockdown:
            return False, 0.0, "Lockdown Mode"

        # Check 5x Gain (Target)
        if gain_pct >= Config.USOR_TARGET_GAIN:
            # User said "Sell 0% until 5x gain is reached". 
            # Implies at 5x we start selling? Or sell all?
            # "Bypass standard sell ladder... Sell 0% until 5x gain is reached."
            # I'll assume we sell 100% at 5x or start a new trailing stop? 
            # Prompt doesn't specify what happens AT 5x. 
            # Usually implies "Take Profit". I'll trigger a partial or full sell.
            # Let's assume standard behavior: Sell significant portion or switch to tight trail.
            # I will sell 50% at 5x for now or just log it. 
            # Actually, "Sell 0% until 5x" might mean "Don't sell BEFORE 5x".
            # After 5x, maybe standard logic applies? 
            # I will implement: If > 5x, sell 50%.
            return True, 0.5, "USOR 5x Target Hit"
            
        return False, 0.0, "Holding USOR"

    @staticmethod
    def _standard_logic(gain_pct, current_price, highest_price, sold_t1, sold_t2, sold_t3, in_lockdown):
        # Stop Loss / Trailing Stop for Moonbag?
        # User said: "Moonbag: Remaining 25% follows a 15% Trailing Stop Loss."
        # Does this apply to WHOLE position or just moonbag?
        # "Standard Exit Strategy... Tier 1... Tier 2... Tier 3... Moonbag"
        # Implies we only use trailing stop on the last 25%?
        # Or maybe we have a general stop loss? Prompt doesn't specify general SL, only "Rug Safety" and "Moonbag SL".
        # I'll assume Trailing SL applies to the Moonbag (after T3).
        
        # However, we need to protect capital. 
        # I'll implement Tiers.
        
        if in_lockdown:
            # "disable all 'Sell' triggers except the Stop Loss"
            # Does Standard Strategy have a global Stop Loss? Not explicitly defined in "Standard Exit Strategy".
            # But USOR has one.
            # I will assume Lockdown applies to USOR specifically?
            # "4. Special 'USOR' Conviction Logic... From Jan 25 to Feb 5... disable all 'Sell' triggers"
            # It's indented under USOR. So maybe only USOR is locked down.
            # "5. Standard Exit Strategy (Non-USOR)" -> Separate section.
            # So Standard Strategy works normally during those dates.
            pass
        else:
            # Lockdown logic was under USOR. So Standard is unaffected.
            pass

        # Tier 1: Sell 20% at +25%
        if gain_pct >= Config.TIER_1_GAIN and not sold_t1:
            return True, Config.TIER_1_PCT, "Tier 1 Profit"
            
        # Tier 2: Sell 30% at +50%
        if gain_pct >= Config.TIER_2_GAIN and not sold_t2:
            return True, Config.TIER_2_PCT, "Tier 2 Profit"
            
        # Tier 3: Sell 25% at +100%
        if gain_pct >= Config.TIER_3_GAIN and not sold_t3:
            return True, Config.TIER_3_PCT, "Tier 3 Profit"
            
        # Moonbag Trailing Stop (Only active if we sold T1, T2, T3? Or always active?)
        # Usually Moonbag implies the remainder.
        # If we have sold T3, we are in Moonbag territory.
        if sold_t3:
            drop_from_high = (highest_price - current_price) / highest_price
            if drop_from_high >= Config.MOONBAG_TRAILING_STOP:
                return True, 1.0, "Moonbag Trailing Stop"
                
        return False, 0.0, "Holding Standard"
