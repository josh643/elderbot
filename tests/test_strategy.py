import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime
import sys
import os

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.engine.strategy import Strategy
from src.config.config import Config

class TestStrategy(unittest.TestCase):
    
    @patch('src.engine.strategy.datetime')
    def test_usor_lockdown(self, mock_datetime):
        # Test inside lockdown (Jan 26)
        mock_datetime.now.return_value = datetime(2026, 1, 26)
        
        # USOR Token: +600% Gain (Should sell 5x target usually)
        # But Lockdown Mode -> Should NOT sell
        Config.USOR_ADDRESS = "USOR_MINT"
        
        should_sell, pct, reason = Strategy.get_sell_action(
            "USOR_MINT", 6.0, 1.0, 6.0, False, False, False
        )
        self.assertFalse(should_sell)
        self.assertEqual(reason, "Lockdown Mode")

    @patch('src.engine.strategy.datetime')
    def test_standard_tiers(self, mock_datetime):
        # Test inside lockdown (Jan 26) - Should NOT affect Standard
        mock_datetime.now.return_value = datetime(2026, 1, 26)
        
        # Standard Token: +30% Gain (Tier 1 is 25%)
        should_sell, pct, reason = Strategy.get_sell_action(
            "STD_MINT", 1.3, 1.0, 1.3, False, False, False
        )
        self.assertTrue(should_sell)
        self.assertEqual(pct, Config.TIER_1_PCT)

if __name__ == '__main__':
    unittest.main()
