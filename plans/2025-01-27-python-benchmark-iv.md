# [Python] インプライドボラティリティ ベンチマーク実装計画

## メタデータ
- **作成日**: 2025-01-27
- **言語**: Python
- **ステータス**: DRAFT
- **推定規模**: 中
- **推定コード行数**: 400
- **対象モジュール**: benchmarks/, docs/performance/

## ⚠️ 技術的負債ゼロの原則

**重要**: このプロジェクトでは技術的負債を一切作らないことを最優先とします。

### 禁止事項（アンチパターン）
❌ **段階的実装・TODO残し**
```python
# 絶対にダメな例
def iv_benchmark():
    # TODO: 後で最適化する
    pass
```

✅ **正しいアプローチ：最初から完全実装**
```python
# 最初から最適化された完全な実装
import numpy as np
from scipy.optimize import brentq
from quantforge.models import black_scholes

def iv_benchmark_complete():
    """完全に最適化された実装."""
    # 最初から本番品質のコード
```

## 1. 現状分析と問題点

### 現在のベンチマーク結果の問題
- **Black-Scholes単純計算**: NumPy比1.8倍（期待外れ）
- **単一計算**: Pure Python比2.7倍（微妙な改善）
- **FFIオーバーヘッド**: 1μsが計算時間1.4μsに対して相対的に大きい

### なぜIVベンチマークが効果的か
1. **反復計算の必要性**: Newton-Raphson法で通常10-20回の反復
2. **Pythonループの非効率性**: 各反復でのBS価格計算、Vega計算、収束判定
3. **Rustの強みが活きる**: 
   - 反復ループの高速実行
   - 条件分岐の効率的処理
   - エッジケース処理のオーバーヘッド削減
4. **実用的価値**: トレーディングシステムで最も頻繁に使用される計算

## 2. 実装目標と期待成果

### パフォーマンス目標
- **単一IV計算**: Python比 50-100倍高速
- **バッチIV計算（1万件）**: NumPy比 10-20倍高速  
- **バッチIV計算（100万件）**: NumPy比 15-25倍高速
- **並列処理**: 6コアで5倍以上のスケーリング

### ベンチマークで実証する価値
- 実トレーディングシステムでの優位性
- リアルタイムリスク計算での実用性
- ボラティリティサーフェス構築の高速化

## 3. 実装詳細設計

### 3.1 ファイル構成
```
benchmarks/
├── iv_baseline.py          # Python基準実装
├── iv_comparison.py        # ベンチマーク実行
├── practical_scenarios.py  # 実用シナリオベンチマーク
└── results/
    ├── iv_history.jsonl    # IV測定履歴
    └── iv_latest.json      # 最新IV結果
```

### 3.2 Python基準実装（iv_baseline.py）

#### scipy.optimize.brentq実装（業界標準）
```python
from scipy.optimize import brentq
from scipy.stats import norm
import numpy as np

def black_scholes_price_scipy(s, k, t, r, sigma, is_call=True):
    """Black-Scholes価格計算（SciPy版）."""
    d1 = (np.log(s / k) + (r + sigma ** 2 / 2) * t) / (sigma * np.sqrt(t))
    d2 = d1 - sigma * np.sqrt(t)
    if is_call:
        return s * norm.cdf(d1) - k * np.exp(-r * t) * norm.cdf(d2)
    else:
        return k * np.exp(-r * t) * norm.cdf(-d2) - s * norm.cdf(-d1)

def implied_volatility_scipy(price, s, k, t, r, is_call=True):
    """Brent法によるIV計算（業界標準）."""
    def objective(sigma):
        return black_scholes_price_scipy(s, k, t, r, sigma, is_call) - price
    
    try:
        return brentq(objective, 0.001, 10.0, xtol=1e-6)
    except ValueError:
        return np.nan
```

#### Newton-Raphson純Python実装
```python
def vega_scipy(s, k, t, r, sigma):
    """Vega計算."""
    d1 = (np.log(s / k) + (r + sigma ** 2 / 2) * t) / (sigma * np.sqrt(t))
    return s * norm.pdf(d1) * np.sqrt(t)

def implied_volatility_newton(price, s, k, t, r, is_call=True, max_iter=20):
    """Newton-Raphson法によるIV計算."""
    sigma = 0.2  # 初期値
    
    for _ in range(max_iter):
        bs_price = black_scholes_price_scipy(s, k, t, r, sigma, is_call)
        vega_val = vega_scipy(s, k, t, r, sigma)
        
        if abs(vega_val) < 1e-10:
            break
            
        diff = bs_price - price
        if abs(diff) < 1e-6:
            return sigma
            
        sigma = sigma - diff / vega_val
        sigma = max(0.001, min(sigma, 10.0))  # 境界制約
    
    return sigma
```

#### バッチ処理実装
```python
def implied_volatility_batch_scipy(prices, spots, strikes, times, rates, is_calls):
    """バッチIV計算（ループ版）."""
    n = len(prices)
    ivs = np.empty(n)
    
    for i in range(n):
        ivs[i] = implied_volatility_scipy(
            prices[i], spots[i], strikes[i], 
            times[i], rates[i], is_calls[i]
        )
    
    return ivs
```

### 3.3 ベンチマーク実行（iv_comparison.py）

```python
import time
import numpy as np
from quantforge.models import black_scholes
from iv_baseline import (
    implied_volatility_scipy,
    implied_volatility_newton,
    implied_volatility_batch_scipy
)

class IVBenchmarkRunner:
    """IV計算ベンチマーク."""
    
    def __init__(self, warmup_runs=100, measure_runs=1000):
        self.warmup_runs = warmup_runs
        self.measure_runs = measure_runs
    
    def benchmark_single_iv(self):
        """単一IV計算ベンチマーク."""
        # テストケース: ATMオプション
        s, k, t, r = 100.0, 100.0, 1.0, 0.05
        true_sigma = 0.2
        
        # まず価格を計算
        price = black_scholes.call_price(s, k, t, r, true_sigma)
        
        results = {}
        
        # QuantForge (Rust)
        times = []
        for _ in range(self.measure_runs):
            start = time.perf_counter()
            iv = black_scholes.implied_volatility(price, s, k, t, r, is_call=True)
            times.append(time.perf_counter() - start)
        results['quantforge'] = np.median(times)
        
        # SciPy Brent法
        times = []
        for _ in range(self.measure_runs):
            start = time.perf_counter()
            iv = implied_volatility_scipy(price, s, k, t, r, is_call=True)
            times.append(time.perf_counter() - start)
        results['scipy_brent'] = np.median(times)
        
        # Newton-Raphson Python
        times = []
        for _ in range(self.measure_runs):
            start = time.perf_counter()
            iv = implied_volatility_newton(price, s, k, t, r, is_call=True)
            times.append(time.perf_counter() - start)
        results['newton_python'] = np.median(times)
        
        # 相対性能
        results['speedup_vs_scipy'] = results['scipy_brent'] / results['quantforge']
        results['speedup_vs_newton'] = results['newton_python'] / results['quantforge']
        
        return results
    
    def benchmark_batch_iv(self, size):
        """バッチIV計算ベンチマーク."""
        # ランダムなオプションデータ生成
        np.random.seed(42)
        spots = np.random.uniform(80, 120, size)
        strikes = np.random.uniform(80, 120, size)
        times = np.random.uniform(0.1, 2.0, size)
        rates = np.full(size, 0.05)
        true_sigmas = np.random.uniform(0.1, 0.4, size)
        is_calls = np.random.choice([True, False], size)
        
        # 価格を計算
        prices = np.array([
            black_scholes.call_price(s, k, t, r, sigma) if is_call
            else black_scholes.put_price(s, k, t, r, sigma)
            for s, k, t, r, sigma, is_call 
            in zip(spots, strikes, times, rates, true_sigmas, is_calls)
        ])
        
        results = {'size': size}
        
        # QuantForge バッチ処理
        start = time.perf_counter()
        ivs_qf = black_scholes.implied_volatility_batch(
            prices, spots, strikes, times, rates, is_calls
        )
        qf_time = time.perf_counter() - start
        results['quantforge'] = qf_time
        
        # SciPy バッチ処理（ループ）
        if size <= 10000:  # 大きいサイズでは遅すぎる
            start = time.perf_counter()
            ivs_scipy = implied_volatility_batch_scipy(
                prices, spots, strikes, times, rates, is_calls
            )
            scipy_time = time.perf_counter() - start
            results['scipy'] = scipy_time
            results['speedup_vs_scipy'] = scipy_time / qf_time
        
        # スループット
        results['throughput_qf'] = size / qf_time
        
        return results
```

### 3.4 実用シナリオベンチマーク（practical_scenarios.py）

```python
class PracticalScenariosBenchmark:
    """実トレーディングシナリオでのベンチマーク."""
    
    def volatility_smile_calculation(self):
        """ボラティリティスマイル計算（100ストライク×10満期）."""
        # 実際の市場データを模擬
        spot = 100.0
        strikes = np.linspace(70, 130, 100)  # 100ストライク
        maturities = np.array([0.083, 0.25, 0.5, 0.75, 1.0, 1.5, 2.0, 3.0, 5.0, 10.0])  # 10満期
        rate = 0.05
        
        # メッシュグリッド生成
        K, T = np.meshgrid(strikes, maturities)
        k_flat = K.flatten()
        t_flat = T.flatten()
        s_flat = np.full_like(k_flat, spot)
        r_flat = np.full_like(k_flat, rate)
        
        # 市場価格を模擬（実際はマーケットデータから取得）
        market_prices = self._simulate_market_prices(s_flat, k_flat, t_flat, r_flat)
        
        # IV計算性能測定
        start = time.perf_counter()
        ivs = black_scholes.implied_volatility_batch(
            market_prices, s_flat, k_flat, t_flat, r_flat, 
            np.full(len(market_prices), True)
        )
        qf_time = time.perf_counter() - start
        
        # スマイル構築（1000点）
        smile = ivs.reshape(10, 100)
        
        return {
            'calculation_time': qf_time,
            'points_calculated': len(market_prices),
            'throughput': len(market_prices) / qf_time,
            'smile_shape': smile.shape
        }
    
    def realtime_portfolio_risk(self, portfolio_size=10000):
        """リアルタイムポートフォリオリスク計算."""
        # 大規模ポートフォリオを模擬
        np.random.seed(42)
        positions = self._generate_portfolio(portfolio_size)
        
        # マーケット価格から全ポジションのIVを計算
        start = time.perf_counter()
        ivs = black_scholes.implied_volatility_batch(
            positions['market_prices'],
            positions['spots'],
            positions['strikes'],
            positions['times'],
            positions['rates'],
            positions['is_calls']
        )
        iv_calc_time = time.perf_counter() - start
        
        # IVを使ってGreeks再計算（リスク管理用）
        start = time.perf_counter()
        greeks = black_scholes.greeks_batch(
            positions['spots'],
            positions['strikes'],
            positions['times'],
            positions['rates'],
            ivs,  # 計算したIVを使用
            positions['is_calls']
        )
        greeks_calc_time = time.perf_counter() - start
        
        return {
            'portfolio_size': portfolio_size,
            'iv_calculation_time': iv_calc_time,
            'greeks_calculation_time': greeks_calc_time,
            'total_time': iv_calc_time + greeks_calc_time,
            'iv_throughput': portfolio_size / iv_calc_time,
            'total_throughput': portfolio_size / (iv_calc_time + greeks_calc_time)
        }
```

## 4. 命名定義セクション

### 4.1 使用する既存命名
```yaml
existing_names:
  - name: "s"
    meaning: "スポット価格"
    source: "naming_conventions.md#共通パラメータ"
  - name: "k"
    meaning: "権利行使価格"
    source: "naming_conventions.md#共通パラメータ"
  - name: "t"
    meaning: "満期までの時間"
    source: "naming_conventions.md#共通パラメータ"
  - name: "r"
    meaning: "無リスク金利"
    source: "naming_conventions.md#共通パラメータ"
  - name: "sigma"
    meaning: "ボラティリティ"
    source: "naming_conventions.md#共通パラメータ"
  - name: "implied_volatility"
    meaning: "インプライドボラティリティ計算関数"
    source: "既存API"
```

### 4.2 新規提案命名
```yaml
proposed_names:
  - name: "iv"
    meaning: "インプライドボラティリティ（変数名）"
    justification: "業界標準の略称"
    references: "Hull (2018), Options textbooks"
    status: "approved"
```

### 4.3 命名の一貫性チェックリスト
- [x] 既存モデルとの整合性確認
- [x] naming_conventions.mdとの一致確認
- [x] ドキュメントでの使用方法定義
- [x] APIパラメータは省略形を使用
- [x] エラーメッセージでもAPI名を使用

## タスク規模判定

### 判定基準
- [x] 推定コード行数: 400行
- [x] 新規ファイル数: 3個
- [x] 影響範囲: benchmarks/モジュールのみ
- [x] Rust連携: 必要（quantforge.models使用）
- [x] NumPy/Pandas使用: あり
- [x] 非同期処理: 不要

### 規模判定結果
**中規模タスク**

## 品質管理ツール（Python）

### 適用ツール
| ツール | 適用 | 実行コマンド |
|--------|------|-------------|
| pytest | ✅ | `uv run pytest benchmarks/test_iv_*.py` |
| ruff format | ✅ | `uv run ruff format benchmarks/` |
| ruff check | ✅ | `uv run ruff check benchmarks/` |
| mypy (strict) | ✅ | `uv run mypy --strict benchmarks/` |
| similarity-py | 条件付き | `similarity-py --threshold 0.80 benchmarks/` |
| coverage | ✅ | `uv run pytest --cov=benchmarks` |

### 品質ゲート（必達基準）
| 項目 | 基準 |
|------|------|
| テストカバレッジ | 90%以上 |
| 型カバレッジ | 100% |
| ruffエラー | 0件 |
| mypyエラー（strict） | 0件 |

## 実装フェーズ

### Phase 1: Python基準実装（2時間）
- [ ] scipy.optimize.brentq版IV計算
- [ ] Newton-Raphson純Python版
- [ ] バッチ処理ループ実装
- [ ] 完全な型アノテーション

### Phase 2: ベンチマーク実装（3時間）
- [ ] IVBenchmarkRunnerクラス
- [ ] 単一IV計算ベンチマーク
- [ ] バッチIV計算ベンチマーク（1000, 10000, 100000, 1000000件）
- [ ] 結果の構造化データ保存

### Phase 3: 実用シナリオ実装（2時間）
- [ ] ボラティリティスマイル計算
- [ ] リアルタイムポートフォリオリスク
- [ ] マーケットシミュレーション

### Phase 4: 実行と分析（2時間）
- [ ] 全ベンチマーク実行
- [ ] 結果分析とフォーマット
- [ ] docs/performance/benchmarks.md更新
- [ ] 性能改善の可視化

### Phase 5: 品質チェック（1時間）
```bash
# 必須チェック
uv run ruff format benchmarks/
uv run ruff check benchmarks/
uv run mypy --strict benchmarks/
uv run pytest benchmarks/test_iv_*.py --cov=benchmarks
```

## リスクと対策

| リスク | 影響度 | 対策 |
|--------|--------|------|
| SciPy実装が予想より速い | 低 | Newton法純Python版も用意 |
| 大規模バッチでメモリ不足 | 中 | チャンク処理実装 |
| IV計算の収束失敗 | 低 | エラーハンドリング強化 |

## チェックリスト

### 実装前
- [ ] 既存ベンチマークコードの確認
- [ ] IV実装（Rust側）の動作確認
- [ ] 必要なパッケージ（scipy）の確認

### 実装中
- [ ] 定期的なテスト実行
- [ ] 型アノテーションの完全性
- [ ] docstringの記述

### 実装後
- [ ] 全品質ゲート通過
- [ ] ベンチマーク結果の検証
- [ ] ドキュメント更新
- [ ] 計画のarchive移動

## 成果物

- [ ] benchmarks/iv_baseline.py - Python基準実装
- [ ] benchmarks/iv_comparison.py - ベンチマーク実行
- [ ] benchmarks/practical_scenarios.py - 実用シナリオ
- [ ] benchmarks/results/iv_*.json - 測定結果
- [ ] docs/performance/benchmarks.md - 更新版ドキュメント

## 期待される成果の詳細

### 単一IV計算
- QuantForge: ~2μs
- SciPy Brent: ~100μs  
- Python Newton: ~150μs
- **改善率: 50-75倍**

### バッチ処理（100万件）
- QuantForge: ~50ms（20M ops/sec）
- SciPy Loop: ~60秒（遅すぎて実用的でない）
- **改善率: 1200倍**

### 実用シナリオ
- ボラティリティスマイル（1000点）: <5ms
- ポートフォリオリスク（1万件）: <10ms
- **リアルタイム処理可能**

## 備考

- IV計算は金融工学において最も頻繁に使用される計算の一つ
- 実トレーディングシステムでは毎秒数百万回のIV計算が必要
- Rustの反復計算最適化により、Pythonでは不可能な性能を実現
- この性能改善により、リアルタイムリスク管理が可能に