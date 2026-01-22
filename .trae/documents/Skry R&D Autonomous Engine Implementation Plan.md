# Skry R&D Autonomous Engine (v1.0) - Implementation Plan

## 1. Environment & Infrastructure Setup
- **Directory Structure**:
  - `src/`: Core source code.
  - `config/`: Configuration files.
  - `scripts/`: Utility scripts.
  - `data/`: Local storage (logs, csv).
- **Dependencies**: Create `requirements.txt` including `solders`, `solana`, `jupiter-python-sdk`, `streamlit`, `pandas`, `python-dotenv`, `requests`.
- **Configuration**:
  - Generate `.env.template` with fields: `SOLANA_PRIVATE_KEY`, `RPC_URL`, `TAX_VAULT_ADDRESS`, `TELEGRAM_BOT_TOKEN`, `CHAT_ID`.
  - Create `config.py` to load environment variables and constants.
- **Process Management**:
  - Create `setup.sh` for one-click installation on VPS (Linux/Hostinger).
  - Create `ecosystem.config.js` for PM2 to manage `bot_engine` and `dashboard` processes.

## 2. Core Modules Implementation
### A. Solana & Jupiter Client (`src/clients/`)
- **`solana_client.py`**:
  - Initialize `AsyncClient` and `Keypair` from `solders`/`solana`.
  - Implement `get_balance`, `get_token_accounts`, `close_account` (Rent Reclaim).
  - Implement `send_transaction` with `setComputeUnitPrice` for priority fees.
- **`jupiter_client.py`**:
  - Integrate `jupiter-python-sdk` or direct V6 API calls.
  - Implement `get_quote` (checking liquidity depth > $100k by simulating impact).
  - Implement `swap` for executing trades.
  - Implement `scan_new_tokens`: Poll `https://token.jup.ag/all` to detect new mints available for trading.

### B. Security & Analysis (`src/analysis/`)
- **`rugcheck_client.py`**:
  - specific wrapper for `https://api.rugcheck.xyz/v1`.
  - Implement `get_token_report(mint)`.
  - Logic: Convert RugCheck "Risk Score" to "Trust Score" (Trust > 90 implies Risk < Low Threshold).

## 3. Trading Engine Logic (`src/engine/`)
### A. Strategy Manager (`strategy.py`)
- **USOR Logic**:
  - Check if `mint == USOR_ADDRESS`.
  - Logic: Bypass sell tiers, hold until 5x, 30% trailing stop loss.
  - Date Guard: Disable sells Jan 25 - Feb 5 (except Stop Loss).
- **Standard Logic**:
  - Tier 1: Sell 20% @ +25%.
  - Tier 2: Sell 30% @ +50%.
  - Tier 3: Sell 25% @ +100%.
  - Moonbag: 25% with 15% Trailing Stop Loss.

### B. Money Management (`money_manager.py`)
- **Position Sizing**: Calculate 10% of total SOL balance for buy size.
- **Tax Vault**: Calculate 20% of *net profit* on sells and create a transfer instruction to `TAX_VAULT_ADDRESS`.
- **Rent Reclaim**: Identify empty token accounts after sells and append `close_account` instruction.

### C. Main Loop (`bot.py`)
- Continuous loop:
  1. **Scan**: Detect new tokens via Jupiter list updates.
  2. **Filter**: Check Liquidity > $100k & RugCheck Trust > 90.
  3. **Buy**: Execute buy with dynamic priority fees.
  4. **Monitor**: Track price updates for active positions.
  5. **Sell**: Execute strategy-based sells (USOR vs Standard).
  6. **Report**: Send Telegram alerts.

## 4. Monitoring & Dashboard (`src/dashboard/`)
- **Telegram Bot**: Simple notifier for Buy/Sell/Tax events.
- **Streamlit App (`app.py`)**:
  - Password protection (simple hash check).
  - **Metrics**: Live Balance, P/L Curve, Tax Vault Total.
  - **Tables**: Active Holdings (Manual vs Bot), Trade History.
  - **Export**: Generate `trades.csv` compatible with tax software (FIFO).

## 5. Deployment
- **`setup.sh`**: Script to install Python, PM2, dependencies.
- **`start.sh`**: Launch command for PM2.

## Verification Plan
- **Mock Mode**: Implement a flag to simulate trades without using real SOL.
- **Unit Tests**: Test strategy logic (tiers, profit calcs) and Tax Vault math.
- **Dry Run**: Run the bot in read-only mode to verify scanning and API connections.
