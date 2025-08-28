"""Merton model direct export."""

from quantforge import models as _rust_models

# Mertonサブモジュールをそのまま公開
_merton = _rust_models.merton

call_price = _merton.call_price
put_price = _merton.put_price
call_price_batch = _merton.call_price_batch
put_price_batch = _merton.put_price_batch
implied_volatility = _merton.implied_volatility
implied_volatility_batch = _merton.implied_volatility_batch
greeks = _merton.greeks
greeks_batch = _merton.greeks_batch

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
