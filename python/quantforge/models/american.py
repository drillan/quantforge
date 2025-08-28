"""American option model direct export."""

from quantforge import models as _rust_models

# Americanサブモジュールをそのまま公開
_american = _rust_models.american

call_price = _american.call_price
put_price = _american.put_price
call_price_batch = _american.call_price_batch
put_price_batch = _american.put_price_batch
implied_volatility = _american.implied_volatility
implied_volatility_batch = _american.implied_volatility_batch
greeks = _american.greeks
greeks_batch = _american.greeks_batch

__all__ = [
    "call_price",
    "put_price",
    "call_price_batch",
    "put_price_batch",
    "implied_volatility",
    "implied_volatility_batch",
    "greeks",
    "greeks_batch",
]
