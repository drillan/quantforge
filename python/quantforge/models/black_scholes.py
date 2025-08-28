"""Black-Scholes model wrapper for API compatibility."""

from quantforge import models as _rust_models

# Black-Scholesの関数を直接公開（RustのmodelsはデフォルトでBS）
call_price = _rust_models.call_price
put_price = _rust_models.put_price
call_price_batch = _rust_models.call_price_batch
put_price_batch = _rust_models.put_price_batch
implied_volatility = _rust_models.implied_volatility
implied_volatility_batch = _rust_models.implied_volatility_batch
greeks = _rust_models.greeks
greeks_batch = _rust_models.greeks_batch

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
