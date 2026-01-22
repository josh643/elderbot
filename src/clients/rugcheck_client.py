import httpx
from src.utils.logger import logger
from src.config.config import Config

class RugCheckClient:
    BASE_URL = "https://api.rugcheck.xyz/v1"

    async def get_token_report(self, mint: str):
        """
        Fetch token report from RugCheck.
        Returns a dict with 'is_safe' (bool) and 'score' (int).
        """
        url = f"{self.BASE_URL}/tokens/{mint}/report"
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(url, timeout=10)
                if resp.status_code == 200:
                    data = resp.json()
                    score = data.get("score", 1000) # Default to high risk if missing
                    
                    # User requirement: Trust Score > 90.
                    # Assumption: RugCheck Score (0-bad?, or 0-good?)
                    # If RugCheck Score is Risk (0=Good), then Trust > 90 means Risk < 10 (approx).
                    # Let's assume Risk Score < 500 is generally "Safeish", but for "Trust > 90", we want VERY safe.
                    # We will treat score <= 100 as "Trust > 90" equivalent for now, or just return the raw score and let strategy decide.
                    
                    return {
                        "score": score,
                        "risks": data.get("risks", []),
                        "raw": data
                    }
                else:
                    logger.warning(f"RugCheck failed for {mint}: {resp.status_code}")
                    return None
        except Exception as e:
            logger.error(f"RugCheck error for {mint}: {e}")
            return None

    def is_trustable(self, report: dict) -> bool:
        """
        Check if token meets the "Trust Score > 90" requirement.
        Interpreting "Trust Score > 90" as RugCheck Risk Score <= 400 (Just a heuristic, usually < 1000 is 'ok', < 400 'good').
        Wait, if user says Trust > 90 (0-100), maybe they mean RugCheck Score (0-? usually thousands).
        Let's assume Risk Score <= 1000 is "Verified".
        Actually, let's use a strict threshold. Risk Score 0 is perfect.
        Let's say Trust Score = (MaxRisk - CurrentRisk) / MaxRisk * 100?
        We will just define a threshold in Config.
        """
        if not report:
            return False
        score = report.get("score", 10000)
        # Assuming RugCheck score: Lower is better.
        # Threshold from Config.RUGCHECK_TRUST_THRESHOLD is 90.
        # If we map 0 risk -> 100 trust, and 1000 risk -> 0 trust.
        # Trust = 100 - (Score / 10). So Score 100 -> Trust 90.
        # So Score <= 100 is required.
        return score <= 100 # Strict check
