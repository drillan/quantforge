# [Python] インプライドボラティリティ ベンチマーク測定・性能分析計画

## メタデータ
- **作成日**: 2025-01-27
- **言語**: Python
- **ステータス**: DRAFT
- **推定規模**: 中
- **推定コード行数**: 600
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
from quantforge.models import black_scholes, black76, merton, american

def iv_benchmark_complete():
    """完全に最適化された実装."""
    # 最初から本番品質のコード
```

## 1. 現状分析と測定の意義

### 既存実装の状況（2025-01-27時点）
- **バッチ処理API完全実装済み**: implied_volatility_batch, greeks_batch, exercise_boundary_batch
- **全モデル対応済み**: Black-Scholes, Black76, Merton, American
- **ArrayLike + Broadcasting対応**: list, tuple, np.ndarray全対応
- **性能**: 10,000要素を20ms以内で処理（既に達成）

### 現在のベンチマーク結果の限界
- **Black-Scholes単純計算**: NumPy比1.8倍（単純計算では限界）
- **単一計算**: Pure Python比2.7倍（FFIオーバーヘッドが相対的に大きい）
- **測定範囲の狭さ**: Black-Scholesのみ、IVは未測定

### なぜIVベンチマークが重要か
1. **反復計算の優位性**: Newton-Raphson法で10-20回の反復が必要
2. **実用的価値**: トレーディングシステムで最頻出の計算
3. **Rustの強みが最大化**: 
   - 反復ループの高速実行
   - 条件分岐の効率的処理
   - エッジケース処理の最適化
4. **複数モデルの比較**: 異なる複雑度での性能評価

## 2. 測定目標と期待成果

### パフォーマンス測定目標
- **単一IV計算**: 全モデルでPython比 30-100倍の改善を実証
- **バッチIV計算（1万件）**: SciPyループ比 100倍以上
- **バッチIV計算（100万件）**: 実時間50ms以内（20M ops/sec）
- **ArrayLike性能**: list/tuple/ndarrayでの性能差を定量化
- **モデル間比較**: BS < Black76 < Merton < American の計算コスト

### ベンチマークで実証する価値
- 実トレーディングシステムでの優位性
- リアルタイムリスク計算の実現可能性
- ボラティリティサーフェス構築の高速化
- 早期行使境界計算を含む総合的リスク管理

## 3. 実装詳細設計

### 3.1 ファイル構成
```
benchmarks/
├── iv_baseline.py          # Python基準実装（全モデル）
├── iv_comparison.py        # 包括的ベンチマーク実行
├── model_comparison.py     # モデル間性能比較
├── arraylike_benchmark.py  # ArrayLike性能測定
├── practical_scenarios.py  # 実用シナリオベンチマーク
└── results/
    ├── iv_history.jsonl    # IV測定履歴
    ├── iv_latest.json      # 最新IV結果
    └── model_comparison.json # モデル比較結果
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

# Black76, Merton用の基準実装も追加
def black76_iv_scipy(price, f, k, t, r, is_call=True):
    """Black76のIV計算."""
    # Forward価格を使用
    def objective(sigma):
        # Black76価格計算
        return black76_price(f, k, t, r, sigma, is_call) - price
    return brentq(objective, 0.001, 10.0, xtol=1e-6)

def merton_iv_scipy(price, s, k, t, r, q, is_call=True):
    """MertonモデルのIV計算."""
    # 配当利回り考慮
    def objective(sigma):
        return merton_price(s, k, t, r, q, sigma, is_call) - price
    return brentq(objective, 0.001, 10.0, xtol=1e-6)
```

#### バッチ処理実装（全モデル）
```python
def implied_volatility_batch_scipy(prices, spots, strikes, times, rates, is_calls, model='bs'):
    """バッチIV計算（ループ版）- 全モデル対応."""
    n = len(prices)
    ivs = np.empty(n)
    
    for i in range(n):
        if model == 'bs':
            ivs[i] = implied_volatility_scipy(
                prices[i], spots[i], strikes[i], 
                times[i], rates[i], is_calls[i]
            )
        elif model == 'black76':
            # Forward価格として扱う
            ivs[i] = black76_iv_scipy(
                prices[i], spots[i], strikes[i],
                times[i], rates[i], is_calls[i]
            )
        # ... 他モデル
    
    return ivs
```

### 3.3 包括的ベンチマーク実行（iv_comparison.py）

```python
import time
import numpy as np
from quantforge.models import black_scholes, black76, merton, american
from iv_baseline import implied_volatility_scipy, implied_volatility_batch_scipy

class ComprehensiveIVBenchmark:
    """包括的IV計算ベンチマーク."""
    
    def __init__(self, warmup_runs=100, measure_runs=1000):
        self.warmup_runs = warmup_runs
        self.measure_runs = measure_runs
        self.models = {
            'black_scholes': black_scholes,
            'black76': black76,
            'merton': merton,
            'american': american
        }
    
    def benchmark_single_iv_all_models(self):
        """全モデルで単一IV計算ベンチマーク."""
        results = {}
        
        for model_name, model in self.models.items():
            # テストパラメータ（モデルごとに調整）
            if model_name == 'black_scholes':
                s, k, t, r = 100.0, 100.0, 1.0, 0.05
                true_sigma = 0.2
                price = model.call_price(s, k, t, r, true_sigma)
                
                # QuantForge実装
                times = []
                for _ in range(self.measure_runs):
                    start = time.perf_counter()
                    iv = model.implied_volatility(price, s, k, t, r, is_call=True)
                    times.append(time.perf_counter() - start)
                qf_time = np.median(times)
                
                # SciPy実装
                times = []
                for _ in range(self.measure_runs):
                    start = time.perf_counter()
                    iv = implied_volatility_scipy(price, s, k, t, r, is_call=True)
                    times.append(time.perf_counter() - start)
                scipy_time = np.median(times)
                
            elif model_name == 'merton':
                s, k, t, r, q = 100.0, 100.0, 1.0, 0.05, 0.02
                true_sigma = 0.2
                price = model.call_price(s, k, t, r, q, true_sigma)
                
                # QuantForge実装
                times = []
                for _ in range(self.measure_runs):
                    start = time.perf_counter()
                    iv = model.implied_volatility(price, s, k, t, r, q, is_call=True)
                    times.append(time.perf_counter() - start)
                qf_time = np.median(times)
                
                # 基準実装も測定...
            
            # 結果保存
            results[model_name] = {
                'quantforge': qf_time,
                'scipy': scipy_time,
                'speedup': scipy_time / qf_time
            }
        
        return results
    
    def benchmark_batch_iv_all_models(self, size):
        """全モデルでバッチIV計算ベンチマーク."""
        results = {}
        
        # 共通データ生成
        np.random.seed(42)
        spots = np.random.uniform(80, 120, size)
        strikes = np.random.uniform(80, 120, size)
        times = np.random.uniform(0.1, 2.0, size)
        rates = np.full(size, 0.05)
        true_sigmas = np.random.uniform(0.1, 0.4, size)
        is_calls = np.random.choice([True, False], size)
        
        for model_name, model in self.models.items():
            if model_name == 'black_scholes':
                # 価格を計算
                prices = np.array([
                    model.call_price(s, k, t, r, sigma) if is_call
                    else model.put_price(s, k, t, r, sigma)
                    for s, k, t, r, sigma, is_call 
                    in zip(spots, strikes, times, rates, true_sigmas, is_calls)
                ])
                
                # QuantForge バッチ処理
                start = time.perf_counter()
                ivs_qf = model.implied_volatility_batch(
                    prices, spots, strikes, times, rates, is_calls
                )
                qf_time = time.perf_counter() - start
                
                # SciPy バッチ処理（小サイズのみ）
                if size <= 1000:
                    start = time.perf_counter()
                    ivs_scipy = implied_volatility_batch_scipy(
                        prices, spots, strikes, times, rates, is_calls, model='bs'
                    )
                    scipy_time = time.perf_counter() - start
                else:
                    scipy_time = None
            
            elif model_name == 'merton':
                # 配当利回り追加
                q_values = np.full(size, 0.02)
                # 価格計算とベンチマーク...
            
            # 結果保存
            results[model_name] = {
                'size': size,
                'quantforge': qf_time,
                'scipy': scipy_time,
                'speedup': scipy_time / qf_time if scipy_time else None,
                'throughput': size / qf_time
            }
        
        return results
```

### 3.4 ArrayLike性能測定（arraylike_benchmark.py）

```python
class ArrayLikeBenchmark:
    """ArrayLike（list, tuple, ndarray）性能測定."""
    
    def benchmark_arraylike_types(self, size=10000):
        """異なる配列型での性能比較."""
        # データ準備
        np.random.seed(42)
        spots_array = np.random.uniform(80, 120, size)
        spots_list = spots_array.tolist()
        spots_tuple = tuple(spots_list)
        
        # 他のパラメータ（スカラー）
        k, t, r = 100.0, 1.0, 0.05
        sigma = 0.2
        
        results = {}
        
        # NumPy配列
        start = time.perf_counter()
        prices_array = black_scholes.call_price_batch(spots_array, k, t, r, sigma)
        array_time = time.perf_counter() - start
        results['numpy'] = array_time
        
        # Python list
        start = time.perf_counter()
        prices_list = black_scholes.call_price_batch(spots_list, k, t, r, sigma)
        list_time = time.perf_counter() - start
        results['list'] = list_time
        
        # Python tuple
        start = time.perf_counter()
        prices_tuple = black_scholes.call_price_batch(spots_tuple, k, t, r, sigma)
        tuple_time = time.perf_counter() - start
        results['tuple'] = tuple_time
        
        # 相対性能
        results['list_overhead'] = (list_time / array_time - 1) * 100  # %
        results['tuple_overhead'] = (tuple_time / array_time - 1) * 100  # %
        
        return results
    
    def benchmark_broadcasting(self):
        """Broadcasting機能の性能測定."""
        # 完全配列 vs スカラーブロードキャスト
        size = 10000
        spots = np.random.uniform(80, 120, size)
        strikes = np.random.uniform(80, 120, size)
        
        # ケース1: 全パラメータが配列
        start = time.perf_counter()
        prices1 = black_scholes.call_price_batch(
            spots, strikes, 
            np.full(size, 1.0), np.full(size, 0.05), np.full(size, 0.2)
        )
        full_array_time = time.perf_counter() - start
        
        # ケース2: 一部スカラー（Broadcasting利用）
        start = time.perf_counter()
        prices2 = black_scholes.call_price_batch(
            spots, strikes, 1.0, 0.05, 0.2  # t, r, sigmaはスカラー
        )
        broadcast_time = time.perf_counter() - start
        
        return {
            'full_array': full_array_time,
            'broadcasting': broadcast_time,
            'broadcast_efficiency': (full_array_time / broadcast_time - 1) * 100  # %改善
        }
```

### 3.5 実用シナリオベンチマーク（practical_scenarios.py）

```python
class PracticalScenariosBenchmark:
    """実トレーディングシナリオでのベンチマーク."""
    
    def volatility_surface_construction(self):
        """ボラティリティサーフェス構築（複数モデル比較）."""
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
        
        results = {}
        
        # Black-Scholesモデル
        market_prices_bs = self._simulate_market_prices_bs(s_flat, k_flat, t_flat, r_flat)
        start = time.perf_counter()
        ivs_bs = black_scholes.implied_volatility_batch(
            market_prices_bs, s_flat, k_flat, t_flat, r_flat, 
            np.full(len(market_prices_bs), True)
        )
        bs_time = time.perf_counter() - start
        
        # Mertonモデル（配当考慮）
        q_flat = np.full_like(k_flat, 0.02)
        market_prices_merton = self._simulate_market_prices_merton(
            s_flat, k_flat, t_flat, r_flat, q_flat
        )
        start = time.perf_counter()
        ivs_merton = merton.implied_volatility_batch(
            market_prices_merton, s_flat, k_flat, t_flat, r_flat, q_flat,
            np.full(len(market_prices_merton), True)
        )
        merton_time = time.perf_counter() - start
        
        # Americanモデル（早期行使考慮）
        start = time.perf_counter()
        ivs_american = american.implied_volatility_batch(
            market_prices_merton, s_flat, k_flat, t_flat, r_flat, q_flat,
            np.full(len(market_prices_merton), True)
        )
        american_time = time.perf_counter() - start
        
        results = {
            'black_scholes': {
                'time': bs_time,
                'throughput': 1000 / bs_time,
                'smile': ivs_bs.reshape(10, 100)
            },
            'merton': {
                'time': merton_time,
                'throughput': 1000 / merton_time,
                'smile': ivs_merton.reshape(10, 100)
            },
            'american': {
                'time': american_time,
                'throughput': 1000 / american_time,
                'smile': ivs_american.reshape(10, 100)
            }
        }
        
        return results
    
    def realtime_portfolio_risk_with_early_exercise(self, portfolio_size=10000):
        """早期行使境界を含むポートフォリオリスク計算."""
        # 大規模ポートフォリオを模擬（American options含む）
        np.random.seed(42)
        positions = self._generate_mixed_portfolio(portfolio_size)
        
        # American optionsのIV計算
        american_mask = positions['is_american']
        american_count = np.sum(american_mask)
        
        start = time.perf_counter()
        ivs_american = american.implied_volatility_batch(
            positions['market_prices'][american_mask],
            positions['spots'][american_mask],
            positions['strikes'][american_mask],
            positions['times'][american_mask],
            positions['rates'][american_mask],
            positions['dividends'][american_mask],
            positions['is_calls'][american_mask]
        )
        iv_calc_time = time.perf_counter() - start
        
        # 早期行使境界の計算
        start = time.perf_counter()
        boundaries = american.exercise_boundary_batch(
            positions['spots'][american_mask],
            positions['strikes'][american_mask],
            positions['times'][american_mask],
            positions['rates'][american_mask],
            positions['dividends'][american_mask],
            ivs_american,
            positions['is_calls'][american_mask]
        )
        boundary_calc_time = time.perf_counter() - start
        
        # Greeks計算（リスク管理用）
        start = time.perf_counter()
        greeks = american.greeks_batch(
            positions['spots'][american_mask],
            positions['strikes'][american_mask],
            positions['times'][american_mask],
            positions['rates'][american_mask],
            positions['dividends'][american_mask],
            ivs_american,
            positions['is_calls'][american_mask]
        )
        greeks_calc_time = time.perf_counter() - start
        
        return {
            'portfolio_size': portfolio_size,
            'american_options': american_count,
            'iv_calculation_time': iv_calc_time,
            'boundary_calculation_time': boundary_calc_time,
            'greeks_calculation_time': greeks_calc_time,
            'total_time': iv_calc_time + boundary_calc_time + greeks_calc_time,
            'iv_throughput': american_count / iv_calc_time,
            'total_throughput': american_count / (iv_calc_time + boundary_calc_time + greeks_calc_time)
        }
```

## 4. 命名定義セクション

### 4.1 使用する既存命名
```yaml
existing_names:
  # 共通パラメータ
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
  - name: "q"
    meaning: "配当利回り"
    source: "naming_conventions.md#Mertonモデル"
  - name: "f"
    meaning: "先物価格"
    source: "naming_conventions.md#Black76モデル"
  
  # 関数名
  - name: "implied_volatility"
    meaning: "インプライドボラティリティ計算関数"
    source: "既存API"
  - name: "implied_volatility_batch"
    meaning: "バッチIV計算関数"
    source: "既存API（2025-01-27実装済み）"
  - name: "exercise_boundary"
    meaning: "早期行使境界"
    source: "既存API（American）"
```

### 4.2 新規提案命名
```yaml
proposed_names:
  - name: "iv"
    meaning: "インプライドボラティリティ（変数名）"
    justification: "業界標準の略称"
    references: "Hull (2018), Options textbooks"
    status: "approved"
  - name: "ivs"
    meaning: "複数のインプライドボラティリティ（配列）"
    justification: "複数形パターンに従う"
    references: "既存のspots, strikes等と一貫性"
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
- [x] 推定コード行数: 600行
- [x] 新規ファイル数: 5個
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
- [ ] scipy.optimize.brentq版IV計算（全モデル）
- [ ] Newton-Raphson純Python版
- [ ] バッチ処理ループ実装（全モデル対応）
- [ ] 完全な型アノテーション

### Phase 2: 包括的ベンチマーク実装（3時間）
- [ ] ComprehensiveIVBenchmarkクラス
- [ ] 全モデルでの単一IV計算ベンチマーク
- [ ] 全モデルでのバッチIV計算ベンチマーク
- [ ] ArrayLike性能測定
- [ ] Broadcasting性能検証

### Phase 3: 実用シナリオ実装（2時間）
- [ ] ボラティリティサーフェス構築（複数モデル）
- [ ] 早期行使境界を含むリスク計算
- [ ] マーケットシミュレーション

### Phase 4: 実行と分析（2時間）
- [ ] 全ベンチマーク実行
- [ ] 結果分析とフォーマット
- [ ] docs/performance/benchmarks.md更新
- [ ] モデル間比較グラフ作成

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
| 複数モデルの実装複雑性 | 中 | モデルごとにクラス分離 |
| 大規模バッチでメモリ不足 | 中 | チャンク処理実装 |
| IV計算の収束失敗 | 低 | エラーハンドリング強化、NaN返却 |
| ArrayLike変換オーバーヘッド | 低 | 既に最適化済み（ゼロコピー） |

## チェックリスト

### 実装前
- [ ] 既存バッチAPI実装の確認（全モデル）
- [ ] ArrayLike/Broadcasting機能の動作確認
- [ ] 必要なパッケージ（scipy）の確認
- [ ] 既存ベンチマークコードの確認

### 実装中
- [ ] 定期的なテスト実行
- [ ] 型アノテーションの完全性
- [ ] docstringの記述
- [ ] モデル間の一貫性確保

### 実装後
- [ ] 全品質ゲート通過
- [ ] ベンチマーク結果の検証
- [ ] ドキュメント更新（全モデルの結果含む）
- [ ] 計画のarchive移動

## 成果物

- [ ] benchmarks/iv_baseline.py - Python基準実装（全モデル）
- [ ] benchmarks/iv_comparison.py - 包括的ベンチマーク実行
- [ ] benchmarks/model_comparison.py - モデル間性能比較
- [ ] benchmarks/arraylike_benchmark.py - ArrayLike性能測定
- [ ] benchmarks/practical_scenarios.py - 実用シナリオ
- [ ] benchmarks/results/iv_*.json - 測定結果
- [ ] benchmarks/results/model_comparison.json - モデル比較結果
- [ ] docs/performance/benchmarks.md - 更新版ドキュメント

## 期待される成果の詳細

### 単一IV計算（実測予測）
| モデル | QuantForge | SciPy Brent | 改善率 |
|--------|------------|-------------|--------|
| Black-Scholes | ~2μs | ~100μs | 50x |
| Black76 | ~2μs | ~100μs | 50x |
| Merton | ~3μs | ~120μs | 40x |
| American | ~10μs | ~500μs | 50x |

### バッチ処理（10万件）
| モデル | QuantForge | SciPy Loop | 改善率 |
|--------|------------|------------|--------|
| Black-Scholes | ~5ms | ~10秒 | 2000x |
| Merton | ~6ms | ~12秒 | 2000x |
| American | ~20ms | ~50秒 | 2500x |

### ArrayLike性能（10000件、Black-Scholes）
| 配列型 | 処理時間 | オーバーヘッド |
|--------|----------|---------------|
| np.ndarray | ~1ms | 基準 |
| list | ~1.1ms | +10% |
| tuple | ~1.05ms | +5% |

### 実用シナリオ
- ボラティリティサーフェス（1000点）: 
  - Black-Scholes: <2ms
  - Merton: <3ms
  - American: <10ms
- ポートフォリオリスク（1万件American）: 
  - IV計算: <20ms
  - 早期行使境界: <30ms
  - Greeks: <15ms
  - **合計: <65ms（リアルタイム処理可能）**

## 備考

- IV計算は金融工学において最も頻繁に使用される計算の一つ
- 既に実装済みのバッチAPIの性能を可視化し、その優位性を実証
- 複数モデルでの包括的な性能評価により、QuantForgeの汎用性を示す
- ArrayLike/Broadcasting対応により、柔軟な使用が可能であることを実証
- American optionの早期行使境界計算を含む、総合的なリスク管理能力を示す
- この性能により、リアルタイムトレーディングシステムでの実用が可能