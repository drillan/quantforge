# [両言語統合] Implied Volatility Batch実装計画

## メタデータ
- **作成日**: 2025-09-03
- **言語**: Rust + Python (両言語統合)
- **ステータス**: DRAFT
- **推定規模**: 大規模
- **推定コード行数**: 800-1000行（Rust: 500行、Python: 300行）
- **対象モジュール**: 
  - core/src/compute/ (black_scholes.rs, black76.rs, merton.rs)
  - bindings/python/src/models.rs
  - tests/test_implied_volatility.py

## ⚠️ 技術的負債ゼロの原則

**重要**: このプロジェクトでは技術的負債を一切作らないことを最優先とします。

### 禁止事項（アンチパターン）
❌ **段階的実装・TODO残し**
```rust
// 絶対にダメな例
pub fn implied_volatility(...) -> Result<Arc<Float64Array>> {
    // TODO: 後で並列化する
    // とりあえずシーケンシャル実装
}
```

❌ **複数バージョンの共存**
```rust
// 絶対にダメな例
pub fn implied_volatility_v1() { }  // 旧実装
pub fn implied_volatility_v2() { }  // 新実装
```

✅ **正しいアプローチ：最初から完全実装**
```rust
// 最初から並列化を含む完全な実装
pub fn implied_volatility(
    prices: &Float64Array,
    spots: &Float64Array,
    strikes: &Float64Array,
    times: &Float64Array,
    rates: &Float64Array,
    is_calls: &BooleanArray,
) -> Result<Arc<Float64Array>> {
    let len = prices.len();
    
    if len >= PARALLEL_THRESHOLD {
        // 並列処理（最初から実装）
        let results: Vec<f64> = (0..len)
            .into_par_iter()
            .map(|i| newton_raphson_single(...))
            .collect();
        Ok(Arc::new(Float64Array::from(results)))
    } else {
        // シーケンシャル処理
        // ...
    }
}
```

## 命名定義セクション

### 4.1 使用する既存命名
```yaml
existing_names:
  # 共通パラメータ（全モデル共通）
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
  - name: "is_call"
    meaning: "コールオプションフラグ"
    source: "naming_conventions.md#共通パラメータ"
    
  # Black-Scholes固有
  - name: "s"
    meaning: "スポット価格"
    source: "naming_conventions.md#Black-Scholes系"
    
  # Black76固有
  - name: "f"
    meaning: "フォワード価格"
    source: "naming_conventions.md#Black-Scholes系"
    
  # Merton固有
  - name: "q"
    meaning: "配当利回り"
    source: "naming_conventions.md#Black-Scholes系"
    
  # バッチ処理（複数形）
  - name: "prices"
    meaning: "市場価格の配列"
    source: "既存実装パターン"
  - name: "spots"
    meaning: "スポット価格の配列"
    source: "naming_conventions.md#バッチ処理の命名規則"
  - name: "strikes"
    meaning: "権利行使価格の配列"
    source: "naming_conventions.md#バッチ処理の命名規則"
  - name: "times"
    meaning: "満期までの時間の配列"
    source: "naming_conventions.md#バッチ処理の命名規則"
  - name: "rates"
    meaning: "無リスク金利の配列"
    source: "naming_conventions.md#バッチ処理の命名規則"
  - name: "sigmas"
    meaning: "ボラティリティの配列（結果）"
    source: "naming_conventions.md#バッチ処理の命名規則"
  - name: "forwards"
    meaning: "フォワード価格の配列"
    source: "naming_conventions.md#バッチ処理の命名規則"
  - name: "dividend_yields"
    meaning: "配当利回りの配列"
    source: "naming_conventions.md#バッチ処理の命名規則"
  - name: "is_calls"
    meaning: "コールオプションフラグの配列"
    source: "既存実装パターン"
```

### 4.2 新規提案命名
```yaml
proposed_names:
  # なし - すべて既存の命名規則に従う
```

### 4.3 命名の一貫性チェックリスト
- [x] 既存モデルとの整合性確認
- [x] naming_conventions.mdとの一致確認
- [x] ドキュメントでの使用方法定義
- [x] APIパラメータは省略形を使用
- [x] エラーメッセージでもAPI名を使用

## タスク規模判定

### 判定基準
- [x] 推定コード行数: 800-1000行
- [x] 新規ファイル数: 1個（test_implied_volatility.py）
- [x] 影響範囲: 複数モジュール（core + bindings）
- [x] Rust連携: 必要（コア実装）
- [x] Arrow配列処理: 必要
- [x] 並列処理: 必要（Rayon）

### 規模判定結果
**大規模タスク**

## 実装計画詳細

### Phase 1: Rustコアライブラリ実装（core/src/compute/）

#### 1.1 Black-Scholesモデル (black_scholes.rs)
```rust
impl BlackScholes {
    /// Newton-Raphson法によるインプライドボラティリティ計算
    /// 
    /// # 設計判断
    /// - 並列処理閾値: 50,000要素（既存のPARALLEL_THRESHOLDを使用）
    /// - 初期値: 0.2（仕様書通り）
    /// - 収束条件: tolerance=1e-8, max_iterations=100
    /// - エラー処理: 収束しない要素はNaNを返す（全体を止めない）
    pub fn implied_volatility(
        prices: &Float64Array,
        spots: &Float64Array,
        strikes: &Float64Array,
        times: &Float64Array,
        rates: &Float64Array,
        is_calls: &BooleanArray,
    ) -> Result<Arc<Float64Array>> {
        validate_array_lengths(&[prices, spots, strikes, times, rates])?;
        validate_boolean_array_length(is_calls, prices.len())?;
        
        let len = prices.len();
        
        // 並列処理の判断
        if len >= PARALLEL_THRESHOLD {
            // Rayonによる並列処理
            let results: Vec<f64> = (0..len)
                .into_par_iter()
                .map(|i| {
                    newton_raphson_single(
                        prices.value(i),
                        spots.value(i),
                        strikes.value(i),
                        times.value(i),
                        rates.value(i),
                        is_calls.value(i),
                    )
                })
                .collect();
            Ok(Arc::new(Float64Array::from(results)))
        } else {
            // シーケンシャル処理
            let mut results = Vec::with_capacity(len);
            for i in 0..len {
                results.push(newton_raphson_single(
                    prices.value(i),
                    spots.value(i),
                    strikes.value(i),
                    times.value(i),
                    rates.value(i),
                    is_calls.value(i),
                ));
            }
            Ok(Arc::new(Float64Array::from(results)))
        }
    }
}
```

#### 1.2 Black76モデル (black76.rs)
```rust
impl Black76 {
    pub fn implied_volatility(
        prices: &Float64Array,
        forwards: &Float64Array,  // Black76はforwardsを使用
        strikes: &Float64Array,
        times: &Float64Array,
        rates: &Float64Array,
        is_calls: &BooleanArray,
    ) -> Result<Arc<Float64Array>>
}
```

#### 1.3 Mertonモデル (merton.rs)
```rust
impl Merton {
    pub fn implied_volatility(
        prices: &Float64Array,
        spots: &Float64Array,
        strikes: &Float64Array,
        times: &Float64Array,
        rates: &Float64Array,
        dividend_yields: &Float64Array,  // Merton固有
        is_calls: &BooleanArray,
    ) -> Result<Arc<Float64Array>>
}
```

### Phase 2: Pythonバインディング実装 (bindings/python/src/models.rs)

#### 2.1 Black-Scholes implied_volatility_batch
```rust
#[pyfunction]
pub fn implied_volatility_batch(
    py: Python,
    prices: &Bound<'_, PyAny>,
    spots: &Bound<'_, PyAny>,
    strikes: &Bound<'_, PyAny>,
    times: &Bound<'_, PyAny>,
    rates: &Bound<'_, PyAny>,
    is_calls: &Bound<'_, PyAny>,  // Broadcasting対応必要
) -> PyArrowResult<PyObject> {
    // parse_implied_volatility_params関数を新規作成
    let params = parse_implied_volatility_params(
        py, prices, spots, strikes, times, rates, is_calls
    )?;
    
    // Arrow配列の抽出
    let (prices_f64, spots_f64, strikes_f64, times_f64, rates_f64, is_calls_bool) = 
        extract_implied_volatility_arrays(&params)?;
    
    // GILを解放してコア計算実行
    let result_arc = py
        .allow_threads(|| {
            BlackScholes::implied_volatility(
                prices_f64, spots_f64, strikes_f64, 
                times_f64, rates_f64, is_calls_bool
            )
        })
        .map_err(|e| {
            ArrowError::ComputeError(
                format!("Implied volatility computation failed: {e}")
            )
        })?;
    
    // 結果をPyObjectとして返却
    wrap_result_array(py, result_arc, "implied_volatility")
}
```

#### 2.2 Black76 implied_volatility_batch
```rust
#[pyfunction]
pub fn black76_implied_volatility_batch(
    py: Python,
    prices: &Bound<'_, PyAny>,
    forwards: &Bound<'_, PyAny>,  // Black76はforwards
    strikes: &Bound<'_, PyAny>,
    times: &Bound<'_, PyAny>,
    rates: &Bound<'_, PyAny>,
    is_calls: &Bound<'_, PyAny>,
) -> PyArrowResult<PyObject>
```

#### 2.3 Merton implied_volatility_batch
```rust
#[pyfunction]
pub fn merton_implied_volatility_batch(
    py: Python,
    prices: &Bound<'_, PyAny>,
    spots: &Bound<'_, PyAny>,
    strikes: &Bound<'_, PyAny>,
    times: &Bound<'_, PyAny>,
    rates: &Bound<'_, PyAny>,
    dividend_yields: &Bound<'_, PyAny>,  // Merton固有
    is_calls: &Bound<'_, PyAny>,
) -> PyArrowResult<PyObject>
```

### Phase 3: arrow_commonモジュール拡張

#### 3.1 パラメータ解析関数の追加
```rust
// bindings/python/src/arrow_common.rs

/// is_callsパラメータのbroadcasting対応
pub fn parse_is_calls_param(
    py: Python,
    is_calls: &Bound<'_, PyAny>,
    length: usize,
) -> PyArrowResult<Arc<BooleanArray>> {
    // スカラー（bool）の場合は拡張
    // 配列の場合はそのまま使用
}

/// implied_volatility用のパラメータ解析
pub fn parse_implied_volatility_params(
    py: Python,
    prices: &Bound<'_, PyAny>,
    spots: &Bound<'_, PyAny>,
    strikes: &Bound<'_, PyAny>,
    times: &Bound<'_, PyAny>,
    rates: &Bound<'_, PyAny>,
    is_calls: &Bound<'_, PyAny>,
) -> PyArrowResult<ImpliedVolatilityParams>
```

### Phase 4: テスト実装

#### 4.1 基本機能テスト
```python
# tests/test_implied_volatility.py
import numpy as np
import pytest
from quantforge.models import black_scholes, black76, merton

class TestImpliedVolatilityBatch:
    def test_black_scholes_basic(self):
        """Black-Scholesの基本動作確認"""
        # 既知の価格からIVを逆算
        spots = np.array([100.0, 100.0, 100.0])
        strikes = np.array([90.0, 100.0, 110.0])
        times = 1.0
        rates = 0.05
        sigmas_true = np.array([0.2, 0.25, 0.3])
        
        # まず価格を計算
        prices = black_scholes.call_price_batch(
            spots, strikes, times, rates, sigmas_true
        )
        
        # IVを逆算
        ivs = black_scholes.implied_volatility_batch(
            prices, spots, strikes, times, rates, True
        )
        
        # 元のsigmaと一致することを確認
        np.testing.assert_allclose(ivs, sigmas_true, rtol=1e-6)
    
    def test_broadcasting(self):
        """Broadcasting機能のテスト"""
        prices = np.array([10.0, 11.0, 12.0])
        spots = 100.0  # スカラー → 自動拡張
        strikes = np.array([95.0, 100.0, 105.0])
        times = 1.0  # スカラー → 自動拡張
        rates = 0.05  # スカラー → 自動拡張
        is_calls = True  # スカラー → 自動拡張
        
        ivs = black_scholes.implied_volatility_batch(
            prices, spots, strikes, times, rates, is_calls
        )
        
        assert len(ivs) == 3
        assert np.all(ivs > 0)
    
    def test_mixed_call_put(self):
        """コール・プット混在のテスト"""
        prices = np.array([10.0, 5.0, 12.0])
        spots = 100.0
        strikes = np.array([90.0, 110.0, 95.0])
        times = 1.0
        rates = 0.05
        is_calls = np.array([True, False, True])  # 混在
        
        ivs = black_scholes.implied_volatility_batch(
            prices, spots, strikes, times, rates, is_calls
        )
        
        assert len(ivs) == 3
        assert np.all(ivs > 0)
    
    def test_convergence_edge_cases(self):
        """エッジケース（深いITM/OTM）での収束性"""
        # 深いITM
        price_itm = 50.0
        spot_itm = 100.0
        strike_itm = 50.0
        
        # 深いOTM
        price_otm = 0.01
        spot_otm = 100.0
        strike_otm = 150.0
        
        prices = np.array([price_itm, price_otm])
        spots = np.array([spot_itm, spot_otm])
        strikes = np.array([strike_itm, strike_otm])
        
        ivs = black_scholes.implied_volatility_batch(
            prices, spots, strikes, 1.0, 0.05, True
        )
        
        # NaNでないことを確認（収束したことを意味する）
        assert not np.any(np.isnan(ivs))
```

#### 4.2 パフォーマンステスト
```python
import time

def test_performance_scaling():
    """データサイズによるパフォーマンススケーリング"""
    sizes = [1000, 10000, 100000, 1000000]
    times_taken = []
    
    for size in sizes:
        prices = np.random.uniform(5, 20, size)
        spots = np.full(size, 100.0)
        strikes = np.random.uniform(80, 120, size)
        
        start = time.perf_counter()
        ivs = black_scholes.implied_volatility_batch(
            prices, spots, strikes, 1.0, 0.05, True
        )
        elapsed = time.perf_counter() - start
        
        times_taken.append(elapsed)
        print(f"Size: {size:7d}, Time: {elapsed:.4f}s, "
              f"Throughput: {size/elapsed:.0f} ops/sec")
    
    # 線形スケーリングの確認（並列化の効果）
    # 100万要素が1000要素の1000倍以内の時間で処理されること
    assert times_taken[-1] < times_taken[0] * 1500
```

### Phase 5: 品質チェック

```bash
# Rust品質チェック
cargo fmt --all
cargo clippy --all-targets --all-features -- -D warnings
cargo test --lib --release

# Python品質チェック
uv run ruff format .
uv run ruff check . --fix
uv run mypy .

# 統合テスト
uv run maturin develop --release
uv run pytest tests/test_implied_volatility.py -v

# ベンチマーク
uv run pytest tests/test_implied_volatility.py::test_performance_scaling -v
```

## 技術要件

### 必須要件
- [x] Newton-Raphson法による実装
- [x] 収束条件: tolerance=1e-8, max_iterations=100
- [x] 初期値: 0.2（20%）
- [x] アービトラージ条件の検証
- [x] Broadcasting完全サポート
- [x] ゼロコピーArrow処理
- [x] 並列処理（50,000要素以上）

### パフォーマンス目標
- [x] 単一計算: < 2 μs
- [x] 1,000要素バッチ: < 2 ms
- [x] 100,000要素バッチ: < 100 ms
- [x] 1,000,000要素バッチ: < 1 s

## リスクと対策

| リスク | 影響度 | 対策 |
|--------|--------|------|
| 深いITM/OTMでの収束性 | 中 | 初期値の動的調整ロジック |
| Newton-Raphson法の発散 | 低 | 最大反復回数と境界チェック |
| Vega計算のオーバーヘッド | 中 | インライン計算による最適化 |
| is_callsのbroadcasting | 低 | 既存パターンの再利用 |

## チェックリスト

### 実装前
- [x] 既存のスカラー版実装の確認完了
- [x] Arrow処理パターンの理解
- [x] 命名規則の確認（naming_conventions.md）
- [x] アンチパターンの回避確認

### 実装中
- [ ] コア実装のユニットテスト作成
- [ ] バインディング層のテスト作成
- [ ] Broadcasting機能の実装とテスト
- [ ] エッジケースのテスト

### 実装後
- [ ] 全品質ゲート通過
- [ ] パフォーマンス目標達成
- [ ] ドキュメント更新（docs/ja/api/python/implied_vol.md）
- [ ] ベンチマーク結果の記録

## 成果物

- [ ] core/src/compute/black_scholes.rs への追加
- [ ] core/src/compute/black76.rs への追加
- [ ] core/src/compute/merton.rs への追加
- [ ] bindings/python/src/models.rs の更新
- [ ] bindings/python/src/arrow_common.rs の拡張
- [ ] tests/test_implied_volatility.py（新規）
- [ ] ベンチマーク結果（benchmarks/results/）

## 備考

- Newton-Raphson法の実装は各要素が独立なため、並列化に最適
- Vega計算は既存メソッドを使わず、IV計算内で直接実装（効率化のため）
- 収束しない要素はNaNを返し、エラーで全体を止めない設計
- is_callsパラメータもbroadcasting対応（bool配列またはスカラー）