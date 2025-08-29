# mathematical model

The mathematical foundations and theoretical background of option pricing models implemented in QuantForge.

## Model List

### Implemented Models
- [Black-Scholes Model](black_scholes.md) - The standard model for European options ✅
- [Black76 Model](black76.md) - Commodity Futures & Interest Rate Futures Options ✅
- [Merton Model](merton.md) - Options on assets with dividends ✅
- [American Options](american_options.md) - Bjerksund-Stensland 2002 Approximation ✅

### Development Model
- [Asian Options](asian_options.md) - Average Price Options ⚠️

### Future implementation
- Garman-Kohlhagen Model - FX Options
- Spread Options - Kirk Approximation
- Barrier Options - Knock-in/Knock-out
- Lookback Option - Path-Dependent

## Basic Assumption

QuantForge's models are based on the following assumptions:

### Market Assumptions
1. **Perfect Market**: No transaction costs, taxes, or borrowing restrictions
2. **No arbitrage opportunities**: There should be no risk-free profit opportunities.
3. **Liquidity**: There are always buyers and sellers available

### Assumptions for Underlying Asset
1. **Geometric Brownian Motion**: $dS_t = \mu S_t dt + \sigma S_t dW_t$
2. **Constant volatility**: $\sigma$ is independent of both time and price
3. **Dividends**: Continuous dividend rate $q$ or discrete dividends

## Risk-neutral valuation

### Risk-neutral probability

Expected value in a risk-neutral world:

$$V_0 = e^{-rT} \mathbb{E}^\mathbb{Q}[V_T]$$

where:
- $\mathbb{Q}$: Risk-neutral probability measure
- $r$: risk-free interest rate
- $T$: Time to maturity

### Girsanov's Theorem

Conversion from a real probability measure $\mathbb{P}$ to a risk-neutral measure $\mathbb{Q}$:

$$\frac{d\mathbb{Q}}{d\mathbb{P}} = \exp\left(-\frac{1}{2}\int_0^T \theta_s^2 ds - \int_0^T \theta_s dW_s\right)$$

## Numerical Computation Methods

### analytical solution

The following models have analytical solutions:
- Black-Scholes (European)
- geometric meanAsian
- Digital Options

### Approximation Methods

High-speed computation for complex models:
- **Bjerksund-Stensland**: American options
- **Kirk Approximation**: Spread Options
- **Volatility Adjustment**: Arithmetic Average Asian

### numerical integration

Calculating the Cumulative Normal Distribution Function:

```python
def cumulative_normal(x):
    """High-precision cumulative normal distribution"""
    # Hart68 algorithm
    # Precision: < 1e-15
```

## Greeks

### first derivative

| Greek | symbol | Definition | interpretation |
|----------|------|------|------|
| Delta | $\Delta$ | $\frac{\partial V}{\partial S}$ | Price Sensitivity |
| Vega | $\nu$ | $\frac{\partial V}{\partial \sigma}$ | Volatility Sensitivity |
| Theta | $\Theta$ | $-\frac{\partial V}{\partial t}$ | Time Value Reduction |
| Rho | $\rho$ | $\frac{\partial V}{\partial r}$ | Interest Rate Sensitivity |

### second derivative

| Greek | symbol | Definition | interpretation |
|----------|------|------|------|
| Gamma | $\Gamma$ | $\frac{\partial^2 V}{\partial S^2}$ | Delta Rate of Change |
| Vanna | | $\frac{\partial^2 V}{\partial S \partial \sigma}$ | Delta Volatility Sensitivity |
| Volga | | $\frac{\partial^2 V}{\partial \sigma^2}$ | Vega Rate of Change |

## numerical stability

### Underflow Prevention

Stability at extreme parameters:

```rust
fn stable_calculation(spot: f64, strike: f64, vol: f64, time: f64) -> f64 {
    // Special handling for small time values
    if time < 1e-7 {
        return intrinsic_value(spot, strike);
    }
    
    // Special handling for small volatility values
    if vol < 1e-7 {
        return discounted_intrinsic(spot, strike, rate, time);
    }
    
    // Normal calculation
    black_scholes_call(spot, strike, rate, vol, time)
}
```

### precision assurance

Maximum error in double precision (f64):
- Black-Scholes: < 1e-15
- American: < 1e-10
- Asian: < 1e-12

## Performance Optimization

### precalculation

Reuse of common elements:

```rust
struct PrecomputedValues {
    sqrt_time: f64,
    vol_sqrt_time: f64,
    discount_factor: f64,
    d1: f64,
    d2: f64,
    nd1: f64,
    nd2: f64,
}
```

### Parallel Processing

Batch processing with Rayon:

```rust
use rayon::prelude::*;

fn black_scholes_parallel(
    spots: &[f64],
    strikes: &[f64],
    rate: f64,
    vol: f64,
    time: f64,
) -> __m512d {
    // Calculate 8 options simultaneously
}
```

## Validation Test

### Put-Call Parity

$$C - P = S_0 e^{-qT} - K e^{-rT}$$

### boundary conditions

- $C \geq \max(S - Ke^{-rT}, 0)$
- $P \geq \max(Ke^{-rT} - S, 0)$
- $C \leq S$
- $P \leq Ke^{-rT}$

### monotonicity

- $\frac{\partial C}{\partial S} > 0$ (call increases with S)
- $\frac{\partial P}{\partial S} < 0$ (Put decreases in S)
- $\frac{\partial V}{\partial \sigma} > 0$ (increase in volatility)

## References

1. Black, F., & Scholes, M. (1973). The Pricing of Options and Corporate Liabilities.
2. Bjerksund, P., & Stensland, G. (2002). Closed Form Valuation of American Options.
3. Kirk, E. (1995). Correlation in the Energy Markets.
4. Hull, J. C. (2018). Options, Futures, and Other Derivatives.

## Next Step

- [Black-Scholes Model](black_scholes.md) - Detailed theory and implementation
- [Black76 Model](black76.md) - Theory of Futures Options
- [Merton Model](merton.md) - Extension with Dividend Considerations
- [American Options](american_options.md) - Mathematics of Early Exercise
- [Asian Options](asian_options.md) - Path-dependent options
