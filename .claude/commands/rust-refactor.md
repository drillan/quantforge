# Rustコードリファクタリング - AI実行指示プロンプト

あなたはRust + PyO3プロジェクトのリファクタリングを担当し、以下の手順に従ってコードの重複削除と品質改善を実行する。

## 🤖 自動実行原則

**重要**: コード重複とアンチパターンを検出したら、ユーザーの確認を待たずに以下を自動実行する：
- similarity-rsで重複を検出し、即座にリファクタリング案を提示
- 技術的負債となるパターンを発見次第、修正を実行
- パフォーマンス改善の機会を見つけたら、最適化を適用
- 各修正は適切なツール（Edit、MultiEdit等）で直接実行

## 🎯 実行目的

あなたはRustコードベースを以下の観点から分析し、積極的にリファクタリングを実施します：
- コード重複の排除（similarity-rs閾値80%以上）
- 汎用トレイト/ジェネリクスによる統一化
- SIMD/並列化の機会を見逃さない
- PyO3バインディングのゼロコピー最適化
- エラーハンドリングの一貫性確保

## 📋 前提条件の確認

リファクタリング開始前に以下を実行してください：

```bash
# similarity-rsのインストール確認
similarity-rs --version || cargo install similarity-rs

# 現在のコード重複状況を分析
similarity-rs --threshold 0.80 --skip-test src/

# Rustツールチェーンの確認
cargo clippy --version
cargo fmt --version
```

### パフォーマンス目標（プロジェクトごとに調整）
- **単一計算**: ナノ秒〜マイクロ秒オーダー
- **バッチ処理**: データサイズに対して線形以下の計算量
- **メモリ使用量**: 入力データサイズの1.5倍以内
- **Python比高速化**: 100倍以上を目標

## 🚫 技術的負債ゼロの絶対原則

### 禁止事項（アンチパターン）

❌ **段階的移行・暫定実装**
```rust
// 絶対にダメな例
// TODO: 後で最適化する
pub fn compute(data: &[f64]) -> Vec<f64> {
    // 暫定的な実装
}
```

❌ **重複実装の共存**
```rust
// 絶対にダメな例
fn algorithm_v1() { } // 旧実装を残す
fn algorithm_v2() { } // 新実装を追加
```

✅ **正しいアプローチ：最初から完全実装**
```rust
// 最初から最適化された完全な実装
#[inline(always)]
pub fn compute<T: Float>(data: &[T]) -> Vec<T> 
where
    T: Send + Sync + SimdElement,
{
    // 完全な実装（SIMD、並列化、エラーハンドリング含む）
}
```

## 📋 汎用リファクタリング指針

### 1. 数値計算アーキテクチャの最適化パターン

#### 計算戦略の動的選択
```rust
// 汎用的な計算戦略トレイト
pub trait ComputeStrategy {
    type Input;
    type Output;
    
    fn select_strategy(&self, size: usize) -> ExecutionMode {
        match size {
            0..=1000 => ExecutionMode::Sequential,
            1001..=10000 => ExecutionMode::Simd,
            10001..=100000 => ExecutionMode::SimdParallel(4),
            _ => ExecutionMode::SimdParallel(num_cpus::get()),
        }
    }
}

pub enum ExecutionMode {
    Sequential,
    Simd,
    SimdParallel(usize),
}
```

#### SIMD最適化の汎用パターン
```rust
// プラットフォーム非依存のSIMD実装
#[inline(always)]
pub fn apply_vectorized<T, F>(data: &[T], operation: F) -> Vec<T>
where
    T: SimdElement,
    F: Fn(T) -> T + Send + Sync,
{
    #[cfg(all(target_arch = "x86_64", target_feature = "avx2"))]
    {
        apply_avx2(data, operation)
    }
    
    #[cfg(all(target_arch = "aarch64", target_feature = "neon"))]
    {
        apply_neon(data, operation)
    }
    
    #[cfg(not(any(
        all(target_arch = "x86_64", target_feature = "avx2"),
        all(target_arch = "aarch64", target_feature = "neon")
    )))]
    {
        apply_scalar(data, operation)
    }
}
```

### 2. PyO3バインディングの最適化パターン

#### ゼロコピー実装の汎用テンプレート
```rust
use numpy::{PyArray1, PyReadonlyArray1};
use pyo3::prelude::*;

// 入力：読み取り専用NumPy配列
// 出力：新規NumPy配列（事前確保）
#[pyfunction]
pub fn process_array<'py>(
    py: Python<'py>,
    input: PyReadonlyArray1<f64>,
    // その他のパラメータ
) -> PyResult<Bound<'py, PyArray1<f64>>> {
    let len = input.len();
    
    // 出力配列の事前確保（ゼロコピー）
    let mut output = unsafe { 
        PyArray1::<f64>::new_bound(py, len, false) 
    };
    
    // GIL解放して計算実行
    py.allow_threads(|| {
        let input_slice = input.as_slice().unwrap();
        let output_slice = unsafe { 
            output.as_slice_mut().unwrap() 
        };
        
        // 実際の計算処理
        process_in_place(input_slice, output_slice);
    });
    
    Ok(output)
}

// インプレース処理の汎用パターン
fn process_in_place(input: &[f64], output: &mut [f64]) {
    // Rayon + SIMDのハイブリッド処理
    use rayon::prelude::*;
    
    input.par_chunks(1024)
        .zip(output.par_chunks_mut(1024))
        .for_each(|(inp, out)| {
            // チャンクごとのSIMD処理
            vectorized_operation(inp, out);
        });
}
```

### 3. エラーハンドリングの汎用設計

```rust
use thiserror::Error;
use pyo3::exceptions::{PyValueError, PyRuntimeError, PyTypeError};

// 汎用的なエラー型定義
#[derive(Error, Debug)]
pub enum ComputeError {
    #[error("入力検証エラー: {context}")]
    ValidationError { context: String },
    
    #[error("数値計算エラー: {details}")]
    NumericalError { details: String },
    
    #[error("収束エラー: {iterations}回の反復後も収束せず")]
    ConvergenceError { iterations: u32 },
    
    #[error("次元不一致: 期待値 {expected}, 実際 {actual}")]
    DimensionMismatch { expected: usize, actual: usize },
    
    #[error("範囲外エラー: {value} は [{min}, {max}] の範囲外")]
    OutOfRange { value: f64, min: f64, max: f64 },
}

// Python例外への汎用マッピング
impl From<ComputeError> for PyErr {
    fn from(err: ComputeError) -> PyErr {
        match err {
            ComputeError::ValidationError { .. } |
            ComputeError::OutOfRange { .. } => {
                PyValueError::new_err(err.to_string())
            }
            ComputeError::DimensionMismatch { .. } => {
                PyTypeError::new_err(err.to_string())
            }
            ComputeError::NumericalError { .. } |
            ComputeError::ConvergenceError { .. } => {
                PyRuntimeError::new_err(err.to_string())
            }
        }
    }
}
```

### 4. 拡張可能なアーキテクチャパターン

```rust
// 汎用計算エンジントレイト
pub trait ComputeEngine: Send + Sync {
    type Input;
    type Output;
    type Config;
    type Error;
    
    // 単一計算
    fn compute_single(
        &self, 
        input: &Self::Input,
        config: &Self::Config,
    ) -> Result<Self::Output, Self::Error>;
    
    // バッチ計算（デフォルト実装提供）
    fn compute_batch(
        &self,
        inputs: &[Self::Input],
        config: &Self::Config,
    ) -> Vec<Result<Self::Output, Self::Error>> {
        inputs.iter()
            .map(|input| self.compute_single(input, config))
            .collect()
    }
    
    // 並列バッチ計算（デフォルト実装提供）
    fn compute_batch_parallel(
        &self,
        inputs: &[Self::Input],
        config: &Self::Config,
    ) -> Vec<Result<Self::Output, Self::Error>> 
    where
        Self::Input: Sync,
        Self::Output: Send,
    {
        use rayon::prelude::*;
        inputs.par_iter()
            .map(|input| self.compute_single(input, config))
            .collect()
    }
}

// 最適化ヒントトレイト
pub trait OptimizationHints {
    fn prefers_contiguous_memory(&self) -> bool { true }
    fn optimal_chunk_size(&self) -> usize { 1024 }
    fn supports_simd(&self) -> bool { true }
    fn cache_line_size(&self) -> usize { 64 }
}
```

## 🔄 similarity-rsを活用した継続的品質管理

### リファクタリングワークフロー

#### 1. 定期的な重複検出
```bash
# 基本的な重複チェック
similarity-rs \
  --threshold 0.80 \
  --min-lines 5 \
  --skip-test \
  --exclude target \
  --exclude docs \
  src/

# 実験的機能を含む詳細チェック
similarity-rs \
  --threshold 0.75 \
  --experimental-types \
  --experimental-overlap \
  --print \
  src/ > similarity-report.md
```

#### 2. CI/CD統合
```yaml
# .github/workflows/code-quality.yml
name: Code Quality Check

on: [push, pull_request]

jobs:
  similarity-check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Install similarity-rs
        run: cargo install similarity-rs
      
      - name: Check Code Duplication
        run: |
          similarity-rs \
            --threshold 0.85 \
            --skip-test \
            --fail-on-duplicates \
            src/
      
      - name: Generate Report
        if: failure()
        run: |
          similarity-rs \
            --threshold 0.85 \
            --print \
            src/ > duplication-report.md
          
      - name: Upload Report
        if: failure()
        uses: actions/upload-artifact@v2
        with:
          name: duplication-report
          path: duplication-report.md
```

#### 3. リファクタリング判断基準

| 類似度 | アクション | 理由 |
|--------|-----------|------|
| > 95% | 即座にリファクタリング | ほぼ完全な重複 |
| 85-95% | 分析して判断 | 意図的な類似の可能性 |
| 75-85% | 監視対象 | パターンの類似 |
| < 75% | 対応不要 | 独立した実装 |

### 重複パターンの解消戦略

#### パターン1: 類似した計算ロジック
```rust
// Before: 重複した実装
fn calculate_metric_a(data: &[f64]) -> f64 { /* ... */ }
fn calculate_metric_b(data: &[f64]) -> f64 { /* ... */ }

// After: ジェネリクスによる統一
fn calculate_metric<M: Metric>(data: &[f64]) -> f64 
where
    M: Metric,
{
    M::calculate(data)
}
```

#### パターン2: 繰り返されるバリデーション
```rust
// Before: 各関数で重複
fn validate_input_a(x: f64) -> Result<(), Error> { /* ... */ }
fn validate_input_b(x: f64) -> Result<(), Error> { /* ... */ }

// After: トレイトによる統一
trait Validatable {
    fn validate(&self) -> Result<(), ValidationError>;
}
```

## 🧪 汎用テスト戦略

### テストの階層構造
```rust
#[cfg(test)]
mod tests {
    use super::*;
    
    // 1. ユニットテスト：個別機能の検証
    mod unit_tests {
        #[test]
        fn test_single_operation() { }
    }
    
    // 2. プロパティベーステスト：不変条件の検証
    mod property_tests {
        use proptest::prelude::*;
        
        proptest! {
            #[test]
            fn test_invariants(
                input in any::<Vec<f64>>()
                    .prop_filter("non-empty", |v| !v.is_empty())
            ) {
                // 不変条件の検証
            }
        }
    }
    
    // 3. パフォーマンステスト：性能要件の検証
    mod performance_tests {
        #[test]
        #[ignore] // cargo test -- --ignored で実行
        fn test_performance_requirements() {
            // ベンチマーク実行
        }
    }
    
    // 4. 統合テスト：Python連携の検証
    mod integration_tests {
        #[test]
        fn test_python_interop() { }
    }
}
```

### ベンチマークテンプレート
```rust
use criterion::{black_box, criterion_group, criterion_main, Criterion, BenchmarkId};

fn benchmark_template(c: &mut Criterion) {
    let mut group = c.benchmark_group("operation_name");
    
    // データサイズごとのベンチマーク
    for size in [100, 1000, 10000, 100000].iter() {
        let data = generate_test_data(*size);
        
        group.bench_with_input(
            BenchmarkId::new("implementation", size),
            &data,
            |b, data| {
                b.iter(|| {
                    black_box(process_data(data))
                })
            }
        );
    }
    
    group.finish();
}

criterion_group!(benches, benchmark_template);
criterion_main!(benches);
```

## 🔧 新機能追加時のチェックリスト

### 実装前
- [ ] 既存の類似実装を`similarity-rs`で確認
- [ ] 再利用可能なコンポーネントの特定
- [ ] パフォーマンス要件の明確化
- [ ] エラーケースの洗い出し

### 実装中
- [ ] 汎用トレイトの実装または利用
- [ ] SIMD最適化の考慮
- [ ] 並列化戦略の選択
- [ ] ゼロコピー実装の検討
- [ ] エラーハンドリングの統一

### 実装後
- [ ] `similarity-rs`による重複チェック
- [ ] ユニットテストの作成
- [ ] プロパティベーステストの追加
- [ ] ベンチマークの実施
- [ ] ドキュメントの作成

## ⚠️ 一般的な制約事項

- **数値精度**: プロジェクトごとに定義（一般的に相対誤差 < 1e-3）
- **Python互換性**: 3.8以上推奨
- **NumPy統合**: ゼロコピーを基本とする
- **並列安全性**: Send + Sync trait実装
- **メモリ効率**: 入力データの2倍以内

## 🎯 品質指標

- [ ] コード重複率: 5%未満（similarity-rs測定）
- [ ] テストカバレッジ: 90%以上
- [ ] ベンチマーク実行: 全機能で実施
- [ ] ドキュメント: 全public APIに対して100%
- [ ] エラーハンドリング: 全エラーケースをカバー

## 📝 リファクタリング実施例

```bash
# Step 1: 現状分析
similarity-rs --threshold 0.80 src/ > before.md

# Step 2: リファクタリング実施
# - 共通パターンの抽出
# - トレイト/ジェネリクスによる統一
# - マクロによる定型処理の削減

# Step 3: 効果測定
similarity-rs --threshold 0.80 src/ > after.md
diff before.md after.md

# Step 4: パフォーマンス確認
cargo bench -- --baseline before
```

このリファクタリング指示書は、特定の実装に依存せず、あらゆる数値計算プロジェクトに適用可能な汎用的な内容となっています。