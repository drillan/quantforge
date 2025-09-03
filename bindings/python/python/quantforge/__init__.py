"""QuantForge: Arrow-native option pricing library"""

from .quantforge import __version__, american, black76, black_scholes, merton

# Fix Black76 function names to match API documentation
if hasattr(black76, "black76_call_price"):
    black76.call_price = black76.black76_call_price
if hasattr(black76, "black76_put_price"):
    black76.put_price = black76.black76_put_price
if hasattr(black76, "black76_call_price_batch"):
    black76.call_price_batch = black76.black76_call_price_batch
if hasattr(black76, "black76_put_price_batch"):
    black76.put_price_batch = black76.black76_put_price_batch
if hasattr(black76, "black76_implied_volatility"):
    black76.implied_volatility = black76.black76_implied_volatility
if hasattr(black76, "black76_implied_volatility_batch"):
    black76.implied_volatility_batch = black76.black76_implied_volatility_batch

# Fix Merton function names to match API documentation
if hasattr(merton, "merton_call_price"):
    merton.call_price = merton.merton_call_price
if hasattr(merton, "merton_put_price"):
    merton.put_price = merton.merton_put_price
if hasattr(merton, "merton_greeks"):
    merton.greeks = merton.merton_greeks
if hasattr(merton, "merton_implied_volatility"):
    merton.implied_volatility = merton.merton_implied_volatility
if hasattr(merton, "merton_call_price_batch"):
    merton.call_price_batch = merton.merton_call_price_batch
if hasattr(merton, "merton_put_price_batch"):
    merton.put_price_batch = merton.merton_put_price_batch

# Fix American function names to match API documentation
if hasattr(american, "american_call_price"):
    american.call_price = american.american_call_price
if hasattr(american, "american_put_price"):
    american.put_price = american.american_put_price
if hasattr(american, "american_greeks"):
    american.greeks = american.american_greeks
if hasattr(american, "american_implied_volatility"):
    american.implied_volatility = american.american_implied_volatility
if hasattr(american, "american_binomial"):
    american.binomial_tree = american.american_binomial
if hasattr(american, "american_call_price_batch"):
    american.call_price_batch = american.american_call_price_batch
if hasattr(american, "american_put_price_batch"):
    american.put_price_batch = american.american_put_price_batch
if hasattr(american, "american_greeks_batch"):
    american.greeks_batch = american.american_greeks_batch
if hasattr(american, "american_implied_volatility_batch"):
    american.implied_volatility_batch = american.american_implied_volatility_batch

__all__ = ["__version__", "black_scholes", "black76", "merton", "american"]
