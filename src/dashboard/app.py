import streamlit as st
import pandas as pd
import json
import asyncio
import sys
import os
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from src.config.config import Config
from src.clients.solana_client import SolanaClient

# Page Config
st.set_page_config(page_title="Skry R&D Dashboard", layout="wide")

# Password Protection
def check_password():
    """Returns `True` if the user had the correct password."""

    def password_entered():
        """Checks whether a password entered by the user is correct."""
        if st.session_state["password"] == "Skry2026": # Default simple password
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # don't store password
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        # First run, show input for password.
        st.text_input(
            "Password", type="password", on_change=password_entered, key="password"
        )
        return False
    elif not st.session_state["password_correct"]:
        # Password not correct, show input + error.
        st.text_input(
            "Password", type="password", on_change=password_entered, key="password"
        )
        st.error("😕 Password incorrect")
        return False
    else:
        # Password correct.
        return True

if check_password():
    st.title("Skry R&D Autonomous Engine (v1.0)")
    
    # Sidebar
    st.sidebar.header("Status")
    
    # Async Data Fetch
    async def get_data():
        client = SolanaClient()
        balance = await client.get_sol_balance()
        return balance

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    balance = loop.run_until_complete(get_data())
    
    st.sidebar.metric("Wallet Balance (SOL)", f"{balance:.4f}")

    # Load Positions
    positions_file = Config.DATA_DIR / "positions.json"
    if positions_file.exists():
        with open(positions_file, 'r') as f:
            positions = json.load(f)
    else:
        positions = {}

    st.sidebar.metric("Active Positions", len(positions))

    # Dashboard Main
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Active Holdings")
        if positions:
            df_pos = pd.DataFrame.from_dict(positions, orient='index')
            st.dataframe(df_pos)
        else:
            st.info("No active positions.")

    with col2:
        st.subheader("Tax Vault")
        # Calculate from trades.csv
        trades_file = Config.TRADES_LOG
        if trades_file.exists():
            df_trades = pd.read_csv(trades_file)
            if 'Type' in df_trades.columns:
                tax_txs = df_trades[df_trades['Reason'].str.contains("Tax", na=False)]
                # Assuming we log Tax deposits? Or we calculate from PnL?
                # Let's assume we logged Tax deposits as 'SELL' or 'TAX' type?
                # If we didn't log them explicitly in CSVLogger, we might miss it.
                # But we can sum PnL and apply 20%.
                total_pnl = df_trades['PnL_SOL'].sum()
                est_tax = total_pnl * 0.20 if total_pnl > 0 else 0
                st.metric("Est. Tax Liability (20%)", f"{est_tax:.4f} SOL")
                
                st.subheader("Recent Trades")
                st.dataframe(df_trades.tail(10))
        else:
            st.info("No trade history.")

    # P/L Curve (Mock or Real)
    st.subheader("Performance Curve")
    if trades_file.exists() and not df_trades.empty:
        df_trades['Cumulative_PnL'] = df_trades['PnL_SOL'].cumsum()
        st.line_chart(df_trades['Cumulative_PnL'])
