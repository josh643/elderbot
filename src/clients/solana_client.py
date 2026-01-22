import base58
from solana.rpc.async_api import AsyncClient
from solana.rpc.types import TxOpts, TokenAccountOpts
from solders.transaction import Transaction
from solders.keypair import Keypair
from solders.pubkey import Pubkey
from solders.system_program import TransferParams, transfer
from solders.compute_budget import set_compute_unit_price
from spl.token.instructions import close_account, CloseAccountParams, get_associated_token_address
from spl.token.constants import TOKEN_PROGRAM_ID
from src.config.config import Config
from src.utils.logger import logger

class SolanaClient:
    def __init__(self):
        self.rpc_url = Config.RPC_URL
        self.client = AsyncClient(self.rpc_url)
        self.keypair = None
        if Config.SOLANA_PRIVATE_KEY:
            try:
                # Attempt to decode base58
                self.keypair = Keypair.from_base58_string(Config.SOLANA_PRIVATE_KEY)
            except Exception as e:
                logger.error(f"Failed to load private key: {e}")

    async def get_sol_balance(self) -> float:
        if not self.keypair:
            return 0.0
        try:
            resp = await self.client.get_balance(self.keypair.pubkey())
            return resp.value / 1e9
        except Exception as e:
            logger.error(f"Error getting SOL balance: {e}")
            return 0.0

    async def get_token_accounts(self):
        """Get all token accounts for the wallet."""
        if not self.keypair:
            return []
        # TODO: Implement get_token_accounts_by_owner
        # For now return empty list or implement fully
        opts = TokenAccountOpts(program_id=TOKEN_PROGRAM_ID)
        resp = await self.client.get_token_accounts_by_owner(self.keypair.pubkey(), opts)
        return resp.value

    async def transfer_sol(self, to_address: str, amount_sol: float):
        """Send SOL to an address (e.g. Tax Vault)."""
        if not self.keypair:
            return False
        try:
            to_pubkey = Pubkey.from_string(to_address)
            lamports = int(amount_sol * 1e9)
            ix = transfer(TransferParams(
                from_pubkey=self.keypair.pubkey(),
                to_pubkey=to_pubkey,
                lamports=lamports
            ))
            
            # Add compute budget for speed
            cb_ix = set_compute_unit_price(1000) # Dynamic? Start with static low
            
            # Create Transaction (Legacy or V0? Jupiter uses Versioned usually, here Legacy is fine for SOL transfer)
            recent_blockhash = await self.client.get_latest_blockhash()
            txn = Transaction()
            txn.add(cb_ix)
            txn.add(ix)
            txn.recent_blockhash = recent_blockhash.value.blockhash
            txn.sign(self.keypair)
            
            resp = await self.client.send_transaction(txn)
            logger.info(f"Sent {amount_sol} SOL to {to_address}. Sig: {resp.value}")
            return True
        except Exception as e:
            logger.error(f"Transfer failed: {e}")
            return False

    async def close_empty_accounts(self):
        """Find and close empty token accounts to reclaim rent."""
        # Implementation depends on parsing token accounts
        pass
