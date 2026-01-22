import httpx
import base64
import socket
from src.utils.logger import logger
from src.config.config import Config

class JupiterClient:
    QUOTE_API_URL = "https://quote-api.jup.ag/v6"
    TOKEN_LIST_URL = "https://token.jup.ag/all"

    def __init__(self):
        self.known_tokens = set()
        # Create a custom transport to force IPv4
        # Note: httpx uses 'transport' not 'connector' (aiohttp)
        # However, httpx handles IPv4 fallback better usually.
        # But if we want to be explicit with httpx:
        # We can pass local_address="0.0.0.0" to force IPv4 binding? 
        # Or just trust that system certs fixed it.
        # But to be safe against the 'No address' error which is often DNS family mismatch:
        pass

    async def get_quote(self, input_mint: str, output_mint: str, amount: int, slippage_bps: int = 50):
        url = f"{self.QUOTE_API_URL}/quote"
        params = {
            "inputMint": input_mint,
            "outputMint": output_mint,
            "amount": amount,
            "slippageBps": slippage_bps,
            "onlyDirectRoutes": "false",
            "asLegacyTransaction": "false" # Use versioned
        }
        # Force IPv4 transport if needed, or rely on system DNS. 
        # Since we added ca-certificates, standard client should work.
        # But let's add a verify=False fallback if certificates are still weird (Not recommended for prod but for debug)
        # Actually, let's keep verify=True but use a standard client.
        async with httpx.AsyncClient() as client:
            try:
                resp = await client.get(url, params=params)
                if resp.status_code == 200:
                    return resp.json()
                else:
                    logger.warning(f"Jupiter quote failed: {resp.text}")
                    return None
            except Exception as e:
                logger.error(f"Jupiter quote error: {e}")
                return None

    async def get_swap_transaction(self, quote_response: dict, user_pubkey: str):
        url = f"{self.QUOTE_API_URL}/swap"
        payload = {
            "quoteResponse": quote_response,
            "userPublicKey": user_pubkey,
            "wrapAndUnwrapSol": True,
            # "computeUnitPriceMicroLamports": "auto" # Or use dynamic priority fees via solders
            "dynamicComputeUnitLimit": True, 
            "prioritizationFeeLamports": "auto"
        }
        async with httpx.AsyncClient() as client:
            try:
                resp = await client.post(url, json=payload)
                if resp.status_code == 200:
                    return resp.json().get("swapTransaction")
                else:
                    logger.error(f"Jupiter swap build failed: {resp.text}")
                    return None
            except Exception as e:
                logger.error(f"Jupiter swap error: {e}")
                return None

    async def scan_new_tokens(self):
        """
        Fetch token list and identify new additions.
        In a real scenario, this should be stateful (store known tokens in DB/File).
        For this v1, we fetch 'all' and if it's the first run, we just populate.
        Subsequent runs (if kept in memory) will detect diffs.
        """
        async with httpx.AsyncClient() as client:
            try:
                resp = await client.get(self.TOKEN_LIST_URL)
                if resp.status_code == 200:
                    tokens = resp.json()
                    current_mints = {t['address'] for t in tokens}
                    
                    if not self.known_tokens:
                        self.known_tokens = current_mints
                        logger.info(f"Initialized scan with {len(current_mints)} tokens.")
                        return []
                    
                    new_mints = current_mints - self.known_tokens
                    self.known_tokens = current_mints
                    
                    if new_mints:
                        logger.info(f"Found {len(new_mints)} new tokens.")
                        return list(new_mints)
                    return []
            except Exception as e:
                logger.error(f"Token scan failed: {e}")
                return []
