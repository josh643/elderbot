from src.config.config import Config

class MoneyManager:
    @staticmethod
    def calculate_position_size(total_sol_balance: float) -> float:
        """
        Auto-Compounding: Position size = 10% of total wallet SOL balance.
        """
        return total_sol_balance * Config.POSITION_SIZE_PCT

    @staticmethod
    def calculate_tax(net_profit_sol: float) -> float:
        """
        The Tax Vault: 20% of net profit.
        """
        if net_profit_sol <= 0:
            return 0.0
        return net_profit_sol * Config.TAX_RATE

    @staticmethod
    def should_reclaim_rent(token_balance: float) -> bool:
        """
        Account Reclaim: Close empty SPL token accounts.
        """
        return token_balance == 0
