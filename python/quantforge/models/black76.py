"""Black76 model direct export."""

from quantforge import models as _rust_models

# Black76サブモジュールをそのまま公開
_black76 = _rust_models.black76

call_price = _black76.call_price
put_price = _black76.put_price
call_price_batch = _black76.call_price_batch
put_price_batch = _black76.put_price_batch
implied_volatility = _black76.implied_volatility
implied_volatility_batch = _black76.implied_volatility_batch
greeks = _black76.greeks
greeks_batch = _black76.greeks_batch

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
