"""Integration tests for all models."""
import pytest
import numpy as np
from python.quantforge import models
import json
from pathlib import Path


class TestModelsIntegration:
    """Integration tests for all models."""
    
    @pytest.fixture
    def golden_data(self):
        """Load golden master data."""
        path = Path(__file__).parent.parent.parent.parent.parent / 'tests/golden/golden_values.json'
        with open(path) as f:
            return json.load(f)
    
    def test_black_scholes_consistency(self, golden_data):
        """Test Black-Scholes against golden master."""
        for case in golden_data['test_cases']:
            if case['category'] == 'black_scholes':
                inputs = case['inputs']
                expected = case['outputs']['call_price']
                
                actual = models.black_scholes.call_price(
                    inputs['s'], inputs['k'], inputs['t'],
                    inputs['r'], inputs['v']
                )
                
                assert abs(actual - expected) < golden_data['tolerance']
    
    def test_cross_model_consistency(self):
        """Test consistency between models."""
        # Black-Scholes with q=0 should equal Merton
        bs_price = models.black_scholes.call_price(100, 100, 1, 0.05, 0.2)
        merton_price = models.merton.call_price(100, 100, 1, 0.05, 0.0, 0.2)
        
        assert abs(bs_price - merton_price) < 1e-10
    
    def test_put_call_parity_all_models(self):
        """Test put-call parity for all models."""
        params = {
            's': 100, 'k': 100, 't': 1, 'r': 0.05, 'sigma': 0.2
        }
        
        # Black-Scholes
        bs_call = models.black_scholes.call_price(**params)
        bs_put = models.black_scholes.put_price(**params)
        bs_parity = bs_call - bs_put
        bs_expected = params['s'] - params['k'] * np.exp(-params['r'] * params['t'])
        assert abs(bs_parity - bs_expected) < 1e-10
        
        # Black76
        f = params['s']  # forward = spot for comparison
        b76_call = models.black76.call_price(f, params['k'], params['t'], params['r'], params['sigma'])
        b76_put = models.black76.put_price(f, params['k'], params['t'], params['r'], params['sigma'])
        b76_parity = b76_call - b76_put
        b76_expected = np.exp(-params['r'] * params['t']) * (f - params['k'])
        assert abs(b76_parity - b76_expected) < 1e-10