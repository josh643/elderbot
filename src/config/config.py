import os
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
env_path = Path(__file__).parent.parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

class Config:
    # Environment
    SOLANA_PRIVATE_KEY = os.getenv("SOLANA_PRIVATE_KEY")
    RPC_URL = os.getenv("RPC_URL", "https://api.mainnet-beta.solana.com")
    TAX_VAULT_ADDRESS = os.getenv("TAX_VAULT_ADDRESS")
    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    CHAT_ID = os.getenv("CHAT_ID")
    USOR_ADDRESS = os.getenv("USOR_ADDRESS")

    # Trading Constants
    MIN_LIQUIDITY_USD = 100_000
    RUGCHECK_TRUST_THRESHOLD = 90  # Implies Risk Score < (100 - 90) * factor? Will define logic in client.
    
    # Money Management
    POSITION_SIZE_PCT = 0.10
    TAX_RATE = 0.20
    
    # Sell Logic
    TIER_1_PCT = 0.20
    TIER_1_GAIN = 0.25
    
    TIER_2_PCT = 0.30
    TIER_2_GAIN = 0.50
    
    TIER_3_PCT = 0.25
    TIER_3_GAIN = 1.00
    
    MOONBAG_PCT = 0.25
    MOONBAG_TRAILING_STOP = 0.15
    
    # USOR Logic
    USOR_TARGET_GAIN = 5.0
    USOR_TRAILING_STOP = 0.30

    # Paths
    BASE_DIR = Path(__file__).parent.parent.parent
    DATA_DIR = BASE_DIR / "data"
    TRADES_LOG = DATA_DIR / "trades.csv"

    @classmethod
    def validate(cls):
        required = ["SOLANA_PRIVATE_KEY", "TAX_VAULT_ADDRESS", "TELEGRAM_BOT_TOKEN", "CHAT_ID"]
        missing = [key for key in required if not getattr(cls, key)]
        if missing:
            raise ValueError(f"Missing configuration for: {', '.join(missing)}")

# Ensure data directory exists
Config.DATA_DIR.mkdir(parents=True, exist_ok=True)
