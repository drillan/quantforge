# [Rust] アメリカンオプション価格計算実装計画

## メタデータ
- **作成日**: 2025-09-03
- **言語**: Rust + Python (PyO3)
- **ステータス**: DRAFT
- **推定規模**: 大
- **推定コード行数**: 800-1200行
- **対象モジュール**: core/src/compute/american.rs, bindings/python/src/models.rs

## タスク規模判定

### 判定基準
- [x] 推定コード行数: 800-1200行
- [x] 新規ファイル数: 0個（既存ファイルの完全実装）
- [x] 影響範囲: 複数モジュール（Core + Bindings）
- [x] PyO3バインディング: 必要
- [ ] SIMD最適化: 不要（コンパイラの自動ベクトル化に任せる）
- [x] 並列化: 必要（Rayon使用）

### 規模判定結果
**大規模タスク**

## 品質管理ツール（Rust）

### 適用ツール
| ツール | 適用 | 実行コマンド |
|--------|------|-------------|
| cargo test | ✅ | `cargo test --all --release` |
| cargo clippy | ✅ | `cargo clippy --all-targets --all-features -- -D warnings` |
| cargo fmt | ✅ | `cargo fmt --all` |
| similarity-rs | ✅ | `similarity-rs --threshold 0.80 core/src/` |
| rust-refactor.md | ✅ | `.claude/commands/rust-refactor.md` 適用 |
| cargo bench | ✅ | `cargo bench american` |
| miri（安全性） | 推奨 | `cargo +nightly miri test` |

## 命名定義セクション

### 4.1 使用する既存命名

```yaml
existing_names:
  # 共通パラメータ（naming_conventions.md準拠）
  - name: "s"
    meaning: "スポット価格"
    source: "naming_conventions.md#共通パラメータ"
  - name: "k"
    meaning: "権利行使価格"
    source: "naming_conventions.md#共通パラメータ"
  - name: "t"
    meaning: "満期までの時間（年）"
    source: "naming_conventions.md#共通パラメータ"
  - name: "r"
    meaning: "無リスク金利"
    source: "naming_conventions.md#共通パラメータ"
  - name: "sigma"
    meaning: "ボラティリティ"
    source: "naming_conventions.md#共通パラメータ"
  - name: "q"
    meaning: "配当利回り"
    source: "naming_conventions.md#Black-Scholes系"
  - name: "is_call"
    meaning: "コールオプションフラグ"
    source: "naming_conventions.md#共通パラメータ"
```

### 4.2 新規提案命名

```yaml
proposed_names:
  - name: "n_steps"
    meaning: "二項ツリーのステップ数"
    justification: "naming_conventions.mdに既存定義あり（サンプリング頻度）"
    references: "Cox-Ross-Rubinstein (1979)"
    status: "既存カタログ準拠"
  
  - name: "method"
    meaning: "計算方法の選択"
    justification: "BS2002またはBinomialを選択"
    references: "内部実装での切り替え用"
    status: "内部使用のみ"
```

### 4.3 命名の一貫性チェックリスト
- [x] 既存モデル（Black-Scholes, Black76）との整合性確認
- [x] naming_conventions.mdとの一致確認
- [x] ドキュメントでの使用方法定義
- [x] APIパラメータは省略形を使用
- [x] エラーメッセージでもAPI名を使用

## 実装方針（理想実装ファースト）

### アーキテクチャ設計
1. **Bjerksund-Stensland 2002（BS2002）近似解法**
   - デフォルトの高速実装
   - 解析的近似による高速計算
   - 定数は既にconstants.rsに定義済み

2. **二項ツリー法（オプション）**
   - 高精度が必要な場合の代替手段
   - Cox-Ross-Rubinsteinモデル
   - メモリ効率的な1次元配列実装

3. **Arrow Native実装**
   - ゼロコピーFFI
   - pyo3-arrow統合
   - Broadcasting対応

## フェーズ構成

### Phase 1: 設計とテスト作成（TDD）

#### 1.1 テスト設計（Red Phase）
- [ ] Put-Call不等式テスト: `P ≥ max(K-S, 0)`, `C ≥ max(S-K, 0)`
- [ ] ヨーロピアンとの関係: `American ≥ European`
- [ ] 境界条件テスト: `S→0`, `S→∞`, `t→0`
- [ ] 早期行使プレミアムの存在確認
- [ ] 既知のベンチマーク値との比較（Barone-Adesi-Whaley等）

```rust
// tests/test_american.rs
#[test]
fn test_american_put_intrinsic_value() {
    // アメリカンプットは常に内在価値以上
    let s = 90.0;
    let k = 100.0;
    let american_put = american_put_scalar(s, k, t, r, q, sigma);
    assert!(american_put >= (k - s).max(0.0));
}

#[test]
fn test_american_european_relationship() {
    // アメリカン >= ヨーロピアン
    let european = black_scholes_put_scalar(s, k, t, r, sigma);
    let american = american_put_scalar(s, k, t, r, q, sigma);
    assert!(american >= european);
}
```

### Phase 2: BS2002実装（Green Phase）

#### 2.1 スカラー関数実装
```rust
// core/src/compute/american.rs

use crate::constants::{
    BS2002_BETA_MIN, BS2002_CONVERGENCE_TOL, 
    BS2002_H_FACTOR, EXERCISE_BOUNDARY_MAX_ITER
};

/// Bjerksund-Stensland 2002モデルでアメリカンコールオプション価格を計算
#[inline(always)]
pub fn american_call_scalar(s: f64, k: f64, t: f64, r: f64, q: f64, sigma: f64) -> f64 {
    // 配当なしの場合はヨーロピアンと同じ
    if q <= 0.0 {
        return black_scholes_call_scalar(s, k, t, r, sigma);
    }
    
    // BS2002アルゴリズム実装
    let beta = calculate_beta(r, q, sigma);
    let boundary = calculate_exercise_boundary(k, t, r, q, sigma, beta);
    
    if s >= boundary {
        // 早期行使領域
        s - k
    } else {
        // 継続保有領域
        calculate_bs2002_value(s, k, t, r, q, sigma, beta, boundary)
    }
}

/// Bjerksund-Stensland 2002モデルでアメリカンプットオプション価格を計算
#[inline(always)]
pub fn american_put_scalar(s: f64, k: f64, t: f64, r: f64, q: f64, sigma: f64) -> f64 {
    // Put-Call変換を使用
    american_call_scalar(k, s, t, q, r, sigma)
}
```

#### 2.2 Arrow Native実装
```rust
impl American {
    /// Arrow Native版コールオプション価格計算
    pub fn call_price(
        spots: &Float64Array,
        strikes: &Float64Array,
        times: &Float64Array,
        rates: &Float64Array,
        dividend_yields: &Float64Array,
        sigmas: &Float64Array,
    ) -> Result<ArrayRef, ArrowError> {
        let len = validate_broadcast_compatibility(&[
            spots, strikes, times, rates, dividend_yields, sigmas
        ])?;
        
        if len == 0 {
            return Ok(Arc::new(Float64Builder::new().finish()));
        }
        
        let mut builder = Float64Builder::with_capacity(len);
        
        if len >= get_parallel_threshold() {
            // 並列処理
            use rayon::prelude::*;
            
            let results: Vec<f64> = (0..len)
                .into_par_iter()
                .map(|i| {
                    let s = get_scalar_or_array_value(spots, i);
                    let k = get_scalar_or_array_value(strikes, i);
                    let t = get_scalar_or_array_value(times, i);
                    let r = get_scalar_or_array_value(rates, i);
                    let q = get_scalar_or_array_value(dividend_yields, i);
                    let sigma = get_scalar_or_array_value(sigmas, i);
                    
                    american_call_scalar(s, k, t, r, q, sigma)
                })
                .collect();
            
            builder.append_slice(&results);
        } else {
            // シーケンシャル処理
            for i in 0..len {
                let s = get_scalar_or_array_value(spots, i);
                let k = get_scalar_or_array_value(strikes, i);
                let t = get_scalar_or_array_value(times, i);
                let r = get_scalar_or_array_value(rates, i);
                let q = get_scalar_or_array_value(dividend_yields, i);
                let sigma = get_scalar_or_array_value(sigmas, i);
                
                let price = american_call_scalar(s, k, t, r, q, sigma);
                builder.append_value(price);
            }
        }
        
        Ok(Arc::new(builder.finish()))
    }
}
```

### Phase 3: 二項ツリー実装（オプション）

#### 3.1 メモリ効率的な実装
```rust
/// Cox-Ross-Rubinstein二項ツリーモデル
pub fn american_binomial(
    s: f64, k: f64, t: f64, r: f64, q: f64, sigma: f64,
    n_steps: usize, is_call: bool
) -> f64 {
    let dt = t / n_steps as f64;
    let u = (sigma * dt.sqrt()).exp();
    let d = 1.0 / u;
    let p = ((r - q) * dt).exp() - d) / (u - d);
    let discount = (-r * dt).exp();
    
    // メモリ効率的な1次元配列使用（後方帰納法）
    let mut values = vec![0.0; n_steps + 1];
    
    // 満期時点のペイオフ
    for i in 0..=n_steps {
        let spot_t = s * u.powi(i as i32) * d.powi((n_steps - i) as i32);
        values[i] = if is_call {
            (spot_t - k).max(0.0)
        } else {
            (k - spot_t).max(0.0)
        };
    }
    
    // 後方帰納法
    for step in (0..n_steps).rev() {
        for i in 0..=step {
            let spot = s * u.powi(i as i32) * d.powi((step - i) as i32);
            let hold_value = discount * (p * values[i + 1] + (1.0 - p) * values[i]);
            let exercise_value = if is_call {
                (spot - k).max(0.0)
            } else {
                (k - spot).max(0.0)
            };
            values[i] = hold_value.max(exercise_value);
        }
    }
    
    values[0]
}
```

### Phase 4: Greeks実装

#### 4.1 有限差分近似
```rust
impl American {
    /// Delta計算（有限差分）
    pub fn delta(
        spots: &Float64Array,
        strikes: &Float64Array,
        times: &Float64Array,
        rates: &Float64Array,
        dividend_yields: &Float64Array,
        sigmas: &Float64Array,
        is_call: bool,
    ) -> Result<ArrayRef, ArrowError> {
        let h = 0.01; // 1%の変化
        let len = validate_broadcast_compatibility(&[
            spots, strikes, times, rates, dividend_yields, sigmas
        ])?;
        
        let mut builder = Float64Builder::with_capacity(len);
        
        for i in 0..len {
            let s = get_scalar_or_array_value(spots, i);
            let k = get_scalar_or_array_value(strikes, i);
            let t = get_scalar_or_array_value(times, i);
            let r = get_scalar_or_array_value(rates, i);
            let q = get_scalar_or_array_value(dividend_yields, i);
            let sigma = get_scalar_or_array_value(sigmas, i);
            
            let s_up = s * (1.0 + h);
            let s_down = s * (1.0 - h);
            
            let price_up = if is_call {
                american_call_scalar(s_up, k, t, r, q, sigma)
            } else {
                american_put_scalar(s_up, k, t, r, q, sigma)
            };
            
            let price_down = if is_call {
                american_call_scalar(s_down, k, t, r, q, sigma)
            } else {
                american_put_scalar(s_down, k, t, r, q, sigma)
            };
            
            let delta = (price_up - price_down) / (2.0 * s * h);
            builder.append_value(delta);
        }
        
        Ok(Arc::new(builder.finish()))
    }
    
    // Gamma, Vega, Theta, Rho も同様に有限差分で実装
}
```

### Phase 5: Pythonバインディング

#### 5.1 PyO3実装
```rust
// bindings/python/src/models.rs

/// American call price (BS2002 approximation)
#[pyfunction]
#[pyo3(signature = (s, k, t, r, q, sigma))]
pub fn american_call_price(
    s: f64, k: f64, t: f64, r: f64, q: f64, sigma: f64
) -> PyResult<f64> {
    validate_positive(s, "s")?;
    validate_positive(k, "k")?;
    validate_positive(t, "t")?;
    validate_positive(sigma, "sigma")?;
    validate_rate(r)?;
    validate_rate(q)?;
    
    Ok(quantforge_core::compute::american::american_call_scalar(s, k, t, r, q, sigma))
}

/// American call price batch (Arrow Native)
#[pyfunction]
#[pyo3(signature = (spots, strikes, times, rates, dividend_yields, sigmas))]
pub fn american_call_price_batch(
    py: Python,
    spots: PyArray,
    strikes: PyArray,
    times: PyArray,
    rates: PyArray,
    dividend_yields: PyArray,
    sigmas: PyArray,
) -> PyArrowResult<PyObject> {
    let spots_array = spots.to_arrow()?;
    let strikes_array = strikes.to_arrow()?;
    let times_array = times.to_arrow()?;
    let rates_array = rates.to_arrow()?;
    let dividend_yields_array = dividend_yields.to_arrow()?;
    let sigmas_array = sigmas.to_arrow()?;
    
    let result = American::call_price(
        &spots_array,
        &strikes_array,
        &times_array,
        &rates_array,
        &dividend_yields_array,
        &sigmas_array,
    )?;
    
    result.to_arro3(py)
}
```

#### 5.2 Pythonモジュール設定
```python
# python/quantforge/models/american.py

from quantforge import american_call_price, american_put_price
from quantforge import american_call_price_batch, american_put_price_batch
from quantforge import american_greeks

__all__ = [
    'call_price',
    'put_price', 
    'call_price_batch',
    'put_price_batch',
    'greeks',
]

# 既存のAPIパターンに従う
call_price = american_call_price
put_price = american_put_price
call_price_batch = american_call_price_batch
put_price_batch = american_put_price_batch
greeks = american_greeks
```

## 技術要件

### 必須要件
- [x] エラー率 < PRACTICAL_TOLERANCE（1e-3）
- [x] メモリ安全性（Rust保証）
- [x] スレッド安全性（Send + Sync）
- [x] Arrow Nativeゼロコピー実装

### パフォーマンス目標
- [ ] 単一計算（BS2002）: < 100ns
- [ ] 単一計算（二項100ステップ）: < 10μs  
- [ ] 全Greeks: < 200ns
- [ ] 100万件バッチ: < 50ms
- [ ] メモリ使用量: O(1)（BS2002）、O(n)（二項ツリー）

### PyO3連携
- [x] ゼロコピー実装（pyo3-arrow）
- [x] GIL解放での並列処理
- [x] 適切なエラー変換

## リスクと対策

| リスク | 影響度 | 対策 |
|--------|--------|------|
| BS2002の精度限界 | 中 | 二項ツリーオプションを提供 |
| 早期行使境界の収束失敗 | 低 | 最大反復回数とフォールバック |
| 有限差分の精度 | 中 | 適応的なステップサイズ |
| 大規模バッチのメモリ | 低 | チャンク処理とstreaming |

## チェックリスト

### 実装前
- [x] 既存コードの確認（Black-Scholesとの共通部分）
- [x] 定数定義の確認（constants.rsのBS2002関連）
- [x] 命名規則の確認（naming_conventions.md）

### 実装中
- [ ] TDD: テスト作成 → 実装 → リファクタリング
- [ ] 定期的なcargo test実行
- [ ] similarity-rsでの重複チェック
- [ ] コミット前のcargo fmt

### 実装後
- [ ] 全品質ゲート通過
- [ ] ベンチマーク結果記録
- [ ] ドキュメント更新（docs/api/）
- [ ] 計画のarchive移動

## 成果物

- [ ] 実装コード（core/src/compute/american.rs）
- [ ] テストコード（tests/test_american.rs）
- [ ] ベンチマーク（benches/american_benchmark.rs）
- [ ] ドキュメント（rustdoc + docs/api/）
- [ ] PyO3バインディング（bindings/python/src/models.rs）
- [ ] Pythonテスト（tests/test_american.py）

## 備考

- BS2002実装は高速だが近似解法なので、高精度が必要な場合は二項ツリーを使用
- 配当なしのアメリカンコールはヨーロピアンと同じ（早期行使の利点なし）
- プットオプションの早期行使は配当の有無に関わらず常に考慮が必要
- 将来的にはLongstaff-Schwartz法（LSM）などのモンテカルロ法も検討可能