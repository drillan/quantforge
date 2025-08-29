# 実践例

実務で使用される具体的なユースケースとコード例を紹介します。

## ポートフォリオ評価

### オプションポートフォリオの管理

```python
import quantforge as qf
from quantforge.models import black_scholes
import numpy as np
import pandas as pd

# ポートフォリオデータ
portfolio = pd.DataFrame({
    'instrument_id': ['OPT001', 'OPT002', 'OPT003', 'OPT004'],
    'type': ['call', 'put', 'call', 'put'],
    'spot': [100, 100, 105, 95],
    'strike': [105, 95, 110, 90],
    'volume': [100, -50, 75, -25],  # 正=ロング、負=ショート
    'sigma': [0.20, 0.22, 0.25, 0.18],
    'time': [0.25, 0.5, 0.75, 1.0]
})

# 価格とグリークス計算
def calculate_portfolio_metrics(df, rate=0.05):
    """ポートフォリオの評価指標を計算"""
    results = []
    
    for _, row in df.iterrows():
        # グリークス取得
        greeks = black_scholes.greeks(
            spot=row['spot'],
            strike=row['strike'],
            time=row['time'],
            rate=rate,
            sigma=row['sigma'],
            is_call=(row['type'] == 'call')
        )
        
        # 価格計算
        if row['type'] == 'call':
            price = black_scholes.call_price(
                spot=row['spot'],
                strike=row['strike'],
                time=row['time'],
                rate=rate,
                sigma=row['sigma']
            )
        else:
            price = black_scholes.put_price(
                spot=row['spot'],
                strike=row['strike'],
                time=row['time'],
                rate=rate,
                sigma=row['sigma']
            )
        
        # ポジション調整
        position_value = price * row['volume']
        position_delta = greeks.delta * row['volume']
        position_gamma = greeks.gamma * row['volume']
        position_vega = greeks.vega * row['volume']
        position_theta = greeks.theta * row['volume']
        
        results.append({
            'instrument_id': row['instrument_id'],
            'price': price,
            'position_value': position_value,
            'delta': position_delta,
            'gamma': position_gamma,
            'vega': position_vega,
            'theta': position_theta
        })
    
    return pd.DataFrame(results)

# 計算実行
metrics = calculate_portfolio_metrics(portfolio)
print(metrics)

# ポートフォリオ全体のリスク
total_value = metrics['position_value'].sum()
total_delta = metrics['delta'].sum()
total_gamma = metrics['gamma'].sum()
total_vega = metrics['vega'].sum()
total_theta = metrics['theta'].sum()

print(f"\nPortfolio Summary:")
print(f"Total Value: ${total_value:,.2f}")
print(f"Delta: {total_delta:.2f}")
print(f"Gamma: {total_gamma:.4f}")
print(f"Vega: {total_vega:.2f}")
print(f"Theta: {total_theta:.2f}")
```

### デルタヘッジング

```{code-block} python
:name: examples-code-delta_hedge_portfolio
:caption: delta_hedge_portfolio

def delta_hedge_portfolio(portfolio_delta, spot_price, shares_per_contract=100):
    """デルタニュートラルにするためのヘッジ量計算"""
    hedge_shares = -portfolio_delta * shares_per_contract
    hedge_value = hedge_shares * spot_price
    
    return {
        'hedge_shares': hedge_shares,
        'hedge_value': hedge_value,
        'direction': 'buy' if hedge_shares > 0 else 'sell'
    }

# デルタヘッジ計算
hedge = delta_hedge_portfolio(total_delta, 100)
print(f"\nDelta Hedge Required:")
print(f"Action: {hedge['direction'].upper()} {abs(hedge['hedge_shares']):.0f} shares")
print(f"Value: ${abs(hedge['hedge_value']):,.2f}")
```

## リスク管理

### VaR（Value at Risk）計算

```{code-block} python
:name: examples-code-calculate_var_options
:caption: calculate_var_options

def calculate_var_options(spot, strike, rate, sigma, time, confidence=0.95, n_sims=10000):
    """オプションポートフォリオのVaR計算"""
    np.random.seed(42)
    
    # 現在価値
    current_value = black_scholes.call_price(
        spot=spot, strike=strike, time=time, rate=rate, sigma=sigma
    )
    
    # モンテカルロシミュレーション
    dt = 1/252  # 1日
    z = np.random.standard_normal(n_sims)
    
    # 1日後のスポット価格
    future_spots = spot * np.exp((rate - 0.5*sigma**2)*dt + sigma*np.sqrt(dt)*z)
    
    # 1日後のオプション価値
    future_values = black_scholes.call_price_batch(
        spots=future_spots,
        strike=strike,
        time=time - dt,
        rate=rate,
        sigma=sigma
    )
    
    # 損益分布
    pnl = future_values - current_value
    
    # VaR計算
    var = -np.percentile(pnl, (1-confidence)*100)
    cvar = -np.mean(pnl[pnl <= -var])  # Conditional VaR
    
    return {
        'var': var,
        'cvar': cvar,
        'current_value': current_value,
        'pnl_mean': np.mean(pnl),
        'pnl_std': np.std(pnl)
    }

# VaR計算例
var_results = calculate_var_options(100, 105, 0.05, 0.25, 0.5)
print(f"1-Day VaR (95%): ${var_results['var']:.2f}")
print(f"1-Day CVaR (95%): ${var_results['cvar']:.2f}")
print(f"Expected P&L: ${var_results['pnl_mean']:.2f}")
print(f"P&L Std Dev: ${var_results['pnl_std']:.2f}")
```

### ストレステスト

```{code-block} python
:name: examples-code-stress_test_portfolio
:caption: stress_test_portfolio

def stress_test_portfolio(base_spot, base_vol, portfolio_func, 
                         spot_shocks=None, vol_shocks=None):
    """ポートフォリオのストレステスト"""
    if spot_shocks is None:
        spot_shocks = np.linspace(-0.2, 0.2, 9)  # ±20%
    if vol_shocks is None:
        vol_shocks = np.linspace(-0.5, 0.5, 9)  # ±50%相対変化
    
    base_value = portfolio_func(base_spot, base_vol)
    results = np.zeros((len(spot_shocks), len(vol_shocks)))
    
    for i, spot_shock in enumerate(spot_shocks):
        for j, vol_shock in enumerate(vol_shocks):
            shocked_spot = base_spot * (1 + spot_shock)
            shocked_vol = base_vol * (1 + vol_shock)
            shocked_value = portfolio_func(shocked_spot, shocked_vol)
            results[i, j] = shocked_value - base_value
    
    return results, spot_shocks, vol_shocks

# ポートフォリオ関数の定義
def sample_portfolio(spot, sigma):
    """サンプルポートフォリオ"""
    call = black_scholes.call_price(
        spot=spot, strike=105, time=0.5, rate=0.05, sigma=sigma
    )
    put = black_scholes.put_price(
        spot=spot, strike=95, time=0.5, rate=0.05, sigma=sigma
    )
    return 100 * call - 50 * put

# ストレステスト実行
stress_results, spot_shocks, vol_shocks = stress_test_portfolio(
    100, 0.2, sample_portfolio
)

# ヒートマップ表示
import matplotlib.pyplot as plt
fig, ax = plt.subplots(figsize=(10, 8))
im = ax.imshow(stress_results, cmap='RdGn', aspect='auto')
ax.set_xticks(range(len(vol_shocks)))
ax.set_yticks(range(len(spot_shocks)))
ax.set_xticklabels([f"{s:+.0%}" for s in vol_shocks])
ax.set_yticklabels([f"{s:+.0%}" for s in spot_shocks])
ax.set_xlabel('Volatility Shock')
ax.set_ylabel('Spot Price Shock')
ax.set_title('Portfolio P&L Under Stress Scenarios')
plt.colorbar(im, ax=ax, label='P&L')
plt.show()
```

## ボラティリティ分析

### インプライドボラティリティサーフェス

```{code-block} python
:name: examples-code-build_iv_surface
:caption: build_iv_surface

def build_iv_surface(market_prices, spot, strikes, times, rate=0.05):
    """市場価格からIVサーフェスを構築"""
    iv_surface = np.zeros_like(market_prices)
    
    for i in range(len(strikes)):
        for j in range(len(times)):
            if market_prices[i, j] > 0:
                iv = black_scholes.implied_volatility(
                    price=market_prices[i, j],
                    spot=spot,
                    strike=strikes[i],
                    time=times[j],
                    rate=rate,
                    is_call=True
                )
                iv_surface[i, j] = iv
    
    return iv_surface

# サンプルデータ生成
strikes = np.array([90, 95, 100, 105, 110])
times = np.array([0.25, 0.5, 0.75, 1.0])
spot = 100

# 仮想的な市場価格（スマイル効果を含む）
market_prices = np.array([
    [12.5, 13.8, 15.0, 16.1],  # K=90
    [8.5, 10.2, 11.5, 12.7],   # K=95
    [5.2, 7.1, 8.6, 9.9],      # K=100
    [2.8, 4.5, 6.0, 7.3],      # K=105
    [1.3, 2.6, 3.9, 5.1],      # K=110
])

# IVサーフェス構築
iv_surface = build_iv_surface(market_prices, spot, strikes, times)

# 3Dプロット
from mpl_toolkits.mplot3d import Axes3D
fig = plt.figure(figsize=(12, 8))
ax = fig.add_subplot(111, projection='3d')

T, K = np.meshgrid(times, strikes)
surf = ax.plot_surface(T, K, iv_surface * 100, cmap='viridis')

ax.set_xlabel('Time to Maturity')
ax.set_ylabel('Strike Price')
ax.set_zlabel('Implied Volatility (%)')
ax.set_title('Implied Volatility Surface')
plt.colorbar(surf)
plt.show()
```

### ボラティリティアービトラージ

```{code-block} python
:name: examples-code-identify_vol_arbitrage
:caption: identify_vol_arbitrage

def identify_vol_arbitrage(market_iv, model_vol, threshold=0.02):
    """ボラティリティアービトラージ機会の特定"""
    diff = market_iv - model_vol
    
    opportunities = []
    if abs(diff) > threshold:
        if diff > 0:
            # 市場IVが高い → オプション売り
            strategy = "Sell options (overpriced)"
        else:
            # 市場IVが低い → オプション買い
            strategy = "Buy options (underpriced)"
        
        opportunities.append({
            'market_iv': market_iv,
            'model_vol': model_vol,
            'difference': diff,
            'strategy': strategy
        })
    
    return opportunities

# アービトラージ機会の検出
market_iv = 0.28
model_vol = 0.22
arb_opps = identify_vol_arbitrage(market_iv, model_vol)

for opp in arb_opps:
    print(f"Arbitrage Opportunity Detected!")
    print(f"Market IV: {opp['market_iv']:.1%}")
    print(f"Model Vol: {opp['model_vol']:.1%}")
    print(f"Difference: {opp['difference']:.1%}")
    print(f"Strategy: {opp['strategy']}")
```

## 自動取引戦略

### オプションマーケットメイキング

```python
class OptionMarketMaker:
    def __init__(self, base_vol, spread_bps=50):
        self.base_vol = base_vol
        self.spread_bps = spread_bps / 10000
        
    def quote_option(self, spot, strike, rate, time, option_type='call'):
        """ビッド・アスク価格を生成"""
        # 中間価格
        if option_type == 'call':
            mid = black_scholes.call_price(
                spot=spot, strike=strike, time=time, rate=rate, sigma=self.base_vol
            )
        else:
            mid = black_scholes.put_price(
                spot=spot, strike=strike, time=time, rate=rate, sigma=self.base_vol
            )
        
        # ボラティリティスプレッド
        bid_vol = self.base_vol * (1 - self.spread_bps)
        ask_vol = self.base_vol * (1 + self.spread_bps)
        
        # ビッド・アスク価格
        if option_type == 'call':
            bid = black_scholes.call_price(
                spot=spot, strike=strike, time=time, rate=rate, sigma=bid_vol
            )
            ask = black_scholes.call_price(
                spot=spot, strike=strike, time=time, rate=rate, sigma=ask_vol
            )
        else:
            bid = black_scholes.put_price(
                spot=spot, strike=strike, time=time, rate=rate, sigma=bid_vol
            )
            ask = black_scholes.put_price(
                spot=spot, strike=strike, time=time, rate=rate, sigma=ask_vol
            )
        
        return {
            'bid': bid,
            'ask': ask,
            'mid': mid,
            'spread': ask - bid,
            'spread_pct': (ask - bid) / mid * 100 if mid > 0 else 0
        }
    
    def adjust_quotes(self, inventory, max_inventory=1000):
        """在庫に基づく価格調整"""
        inventory_ratio = inventory / max_inventory
        # 在庫が多い場合はスプレッドを広げる
        adjusted_spread = self.spread_bps * (1 + abs(inventory_ratio))
        self.spread_bps = min(adjusted_spread, 0.01)  # 最大1%

# マーケットメイカーの実行
mm = OptionMarketMaker(base_vol=0.25, spread_bps=25)

# クォート生成
quote = mm.quote_option(100, 105, 0.05, 0.5, 'call')
print(f"Market Making Quote:")
print(f"Bid: ${quote['bid']:.3f}")
print(f"Ask: ${quote['ask']:.3f}")
print(f"Mid: ${quote['mid']:.3f}")
print(f"Spread: ${quote['spread']:.3f} ({quote['spread_pct']:.2f}%)")

# 在庫調整
mm.adjust_quotes(inventory=800)
adjusted_quote = mm.quote_option(100, 105, 0.05, 0.5, 'call')
print(f"\nAdjusted Quote (High Inventory):")
print(f"Spread: ${adjusted_quote['spread']:.3f} ({adjusted_quote['spread_pct']:.2f}%)")
```

## バックテスト

### オプション戦略のバックテスト

```{code-block} python
:name: examples-code-backtest_covered_call
:caption: backtest_covered_call

def backtest_covered_call(price_path, strike, sigma, rate, dt=1/252):
    """カバードコール戦略のバックテスト"""
    results = []
    
    for i in range(len(price_path) - 21):  # 21営業日 = 1ヶ月
        spot = price_path[i]
        time_to_expiry = 21 * dt
        
        # オプション売却
        premium = black_scholes.call_price(
            spot=spot, strike=strike, time=time_to_expiry, rate=rate, sigma=sigma
        )
        
        # 満期時の損益
        final_spot = price_path[i + 21]
        stock_pnl = final_spot - spot
        option_pnl = -max(final_spot - strike, 0) + premium
        total_pnl = stock_pnl + option_pnl
        
        results.append({
            'date': i,
            'initial_spot': spot,
            'final_spot': final_spot,
            'premium': premium,
            'stock_pnl': stock_pnl,
            'option_pnl': option_pnl,
            'total_pnl': total_pnl,
            'return': total_pnl / spot
        })
    
    return pd.DataFrame(results)

# 価格パスの生成
np.random.seed(42)
n_days = 252
price_path = [100]
for _ in range(n_days):
    ret = np.random.normal(0.0005, 0.015)  # 日次リターン
    price_path.append(price_path[-1] * (1 + ret))

# バックテスト実行
backtest_results = backtest_covered_call(
    price_path, 
    strike=105, 
    sigma=0.2, 
    rate=0.05
)

# 結果分析
total_return = backtest_results['return'].sum()
avg_return = backtest_results['return'].mean()
sharpe = avg_return / backtest_results['return'].std() * np.sqrt(252/21)

print(f"Covered Call Strategy Backtest:")
print(f"Total Return: {total_return:.2%}")
print(f"Average Monthly Return: {avg_return:.2%}")
print(f"Annualized Sharpe Ratio: {sharpe:.2f}")
print(f"Win Rate: {(backtest_results['total_pnl'] > 0).mean():.1%}")
```

## まとめ

実践例では以下を学びました：

- **ポートフォリオ評価**: 複数オプションの統合管理
- **リスク管理**: VaR、ストレステストの実装
- **ボラティリティ分析**: IVサーフェスとアービトラージ
- **自動取引**: マーケットメイキング戦略
- **バックテスト**: 戦略の過去パフォーマンス検証

これらの例を参考に、実務での応用を進めてください。