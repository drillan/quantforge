# [Both] Apache Arrow パフォーマンス最適化実装計画

## メタデータ
- **作成日**: 2025-09-01
- **言語**: Both (Rust実装 + Python API)
- **ステータス**: DRAFT
- **推定規模**: 中
- **推定コード行数**: 300-400行
- **対象モジュール**: 
  - core/src/compute/black_scholes.rs
  - bindings/python/src/models.rs
  - core/src/constants.rs
  - python/quantforge/__init__.py

## タスク規模判定

### 判定基準
- [x] 推定コード行数: 350行
- [x] 新規ファイル数: 0個
- [x] 影響範囲: 複数モジュール
- [x] PyO3バインディング: 必要
- [ ] SIMD最適化: 不要
- [x] 並列化: 調整のみ

### 規模判定結果
**中規模タスク**

## 背景と動機

Apache Arrow移行後のパフォーマンス分析により、以下の改善機会を特定：

### 1. バリデーションによる不公平な比較
- QuantForge: 全入力を検証（推定50-80μs）
- NumPy+SciPy: 検証なし
- ベンチマークが不公平な状態

### 2. 並列化閾値の最適化不足
- 現在: 10,000要素から並列化
- 問題: オーバーヘッドが利益を上回る
- 最適値: 50,000要素（推定）

### 3. Broadcasting処理の非効率性
- 同じ長さの配列でも常にBroadcasting処理実行
- 不要なメモリアロケーションと判定処理

### 現状パフォーマンス（10,000要素）
- 実測値: 208-245μs
- プロトタイプ目標: 166μs
- 改善必要量: 42-79μs

## 命名定義セクション

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
```

### 4.2 新規提案命名
```yaml
proposed_names:
  - name: "_unsafe"
    meaning: "バリデーションスキップ版の関数サフィックス"
    justification: "Rust標準の命名規則に準拠"
    references: "std::slice::get_unchecked, std::ptr::read_unchecked"
    status: "standard_practice"
```

### 4.3 命名の一貫性チェックリスト
- [x] 既存モデルとの整合性確認
- [x] naming_conventions.mdとの一致確認
- [x] ドキュメントでの使用方法定義
- [x] APIパラメータは省略形を使用
- [x] エラーメッセージでもAPI名を使用

## 実装内容

### 1. バリデーションスキップ版（unsafe版）の提供

#### 設計決定：別関数パターンを採用
- `call_price_batch_unsafe()` として独立した関数を提供
- 理由：
  1. 安全性の明確な区別
  2. ゼロコスト抽象化（条件分岐なし）
  3. 静的解析ツールでの検出容易性
  4. Rustの`unsafe`哲学との一貫性

#### Rust側実装（core）
```rust
// core/src/compute/black_scholes.rs

/// バリデーションなしの高速版（内部使用）
pub fn call_price_unchecked(
    spots: &Float64Array,
    strikes: &Float64Array,
    times: &Float64Array,
    rates: &Float64Array,
    sigmas: &Float64Array,
) -> Result<ArrayRef> {
    // 直接計算（バリデーションスキップ）
    let size = spots.len();
    
    if size >= PARALLEL_THRESHOLD {
        compute_parallel_unchecked(spots, strikes, times, rates, sigmas)
    } else {
        compute_sequential_unchecked(spots, strikes, times, rates, sigmas)
    }
}
```

#### Python側実装（bindings）
```rust
// bindings/python/src/models.rs

#[pyfunction]
#[pyo3(signature = (spots, strikes, times, rates, sigmas))]
pub fn call_price_batch_unsafe<'py>(
    py: Python<'py>,
    spots: PyReadonlyArray1<f64>,
    strikes: PyReadonlyArray1<f64>,
    times: PyReadonlyArray1<f64>,
    rates: PyReadonlyArray1<f64>,
    sigmas: PyReadonlyArray1<f64>,
) -> PyResult<Bound<'py, PyArray1<f64>>> {
    // バリデーションをスキップして直接処理
    // Broadcasting処理は維持（データ整合性のため）
    
    let arrays = vec![&spots, &strikes, &times, &rates, &sigmas];
    let target_len = find_broadcast_length(&arrays).map_err(arrow_to_py_err)?;
    
    // Fast Path（同一長チェック）も組み込み
    if all_same_length(&arrays) {
        // 直接変換（Broadcasting不要）
        let result = py.allow_threads(|| {
            BlackScholes::call_price_unchecked(...)
        })?;
        return arrayref_to_numpy(py, result);
    }
    
    // 通常のBroadcasting処理（バリデーションなし）
    // ...
}
```

### 2. 並列化閾値の最適化

```rust
// core/src/constants.rs

// 以前の値（早すぎる並列化）
// pub const PARALLEL_THRESHOLD: usize = 10_000;

// 実測に基づく最適値
pub const PARALLEL_THRESHOLD: usize = 50_000;

// 環境変数でのオーバーライド可能に
pub fn get_parallel_threshold() -> usize {
    std::env::var("QUANTFORGE_PARALLEL_THRESHOLD")
        .ok()
        .and_then(|s| s.parse().ok())
        .unwrap_or(PARALLEL_THRESHOLD)
}
```

### 3. Fast Path実装（同一長配列の高速処理）

```rust
// bindings/python/src/models.rs

/// すべての配列が同じ長さかチェック
fn all_same_length(arrays: &[&PyReadonlyArray1<f64>]) -> bool {
    if arrays.is_empty() {
        return true;
    }
    let first_len = arrays[0].len();
    arrays.iter().all(|arr| arr.len() == first_len)
}

/// Broadcasting不要な直接変換
fn numpy_to_arrow_direct(arr: PyReadonlyArray1<f64>) -> Result<Float64Array> {
    // 単純な変換のみ（拡張処理なし）
    let slice = arr.as_slice()?;
    Ok(Float64Array::from_slice(slice))
}
```

## 実装フェーズ

### Phase 1: 並列化閾値調整（30分）
- [ ] constants.rsのPARALLEL_THRESHOLD定数を50,000に更新
- [ ] 環境変数オーバーライド機能の追加
- [ ] ベンチマーク実行で効果測定
- [ ] 30,000、40,000、50,000で比較測定

### Phase 2: unsafe版実装（2時間）
- [ ] Core層に`call_price_unchecked`関数追加
- [ ] `put_price_unchecked`も同様に追加
- [ ] Python bindingsに`call_price_batch_unsafe`追加
- [ ] `put_price_batch_unsafe`も追加
- [ ] 既存テストの流用（入力は事前検証済みを想定）
- [ ] ドキュメントに明確な警告を追記

### Phase 3: Fast Path実装（2時間）
- [ ] `all_same_length`ヘルパー関数の実装
- [ ] `numpy_to_arrow_direct`関数の実装
- [ ] 条件分岐の追加（通常版とunsafe版両方）
- [ ] パフォーマンステスト
- [ ] エッジケース（空配列、単一要素）の確認

### Phase 4: 統合テストとベンチマーク（1時間）
- [ ] 全最適化の組み合わせテスト
- [ ] ベンチマーク比較（before/after）
- [ ] NumPy互換性確認
- [ ] PyArrow互換性確認（既に動作確認済み）
- [ ] 公平なベンチマーク（NumPyにもバリデーション追加版）

## 品質管理ツール

### Rust側
```bash
cargo test --all
cargo clippy -- -D warnings
cargo fmt --check
cargo bench -- black_scholes
```

### Python側
```bash
# 型チェック
uv run mypy python/

# リント
uv run ruff check python/
uv run ruff format python/

# ベンチマーク
pytest tests/performance/ -m benchmark

# 統合テスト
pytest tests/integration/
```

## パフォーマンス目標

| 指標 | 現在 | 目標 | 改善率 |
|------|------|------|--------|
| 10,000要素処理時間（safe） | 208-245μs | 180μs | 27% |
| 10,000要素処理時間（unsafe） | - | 135μs | 45% |
| NumPy比速度（safe） | 2.47x | 3.4x | 37%向上 |
| NumPy比速度（unsafe） | - | 4.5x | 82%向上 |
| プロトタイプ比 | +24% | -19% | 目標達成 |

## リスクと対策

| リスク | 影響度 | 対策 |
|--------|--------|------|
| unsafe版の誤用 | 高 | 明確なドキュメントと警告、関数名で危険性明示 |
| 並列化閾値の環境依存 | 中 | 環境変数でのオーバーライド機能 |
| Fast Path判定のオーバーヘッド | 低 | 単純な長さ比較のみ（O(n)でn=5） |
| 後方互換性 | なし | 新規API追加のみ、既存APIは変更なし |

## ドキュメント更新

### Python API ドキュメント
```python
def call_price_batch_unsafe(spots, strikes, times, rates, sigmas):
    """Calculate Black-Scholes call option prices WITHOUT validation.
    
    ⚠️ WARNING: This function skips ALL input validation for performance.
    
    This unsafe version provides approximately 20-30% better performance
    by skipping input validation. Use ONLY when:
    - Input data is pre-validated
    - Performance is absolutely critical
    - You understand and accept the risks
    
    Invalid inputs may cause:
    - Incorrect results (NaN, Inf)
    - Undefined behavior
    - No error messages
    
    Parameters
    ----------
    spots : array-like
        Spot prices (must be positive)
    strikes : array-like
        Strike prices (must be positive)
    times : array-like
        Time to maturity in years (must be positive)
    rates : array-like
        Risk-free interest rates
    sigmas : array-like
        Volatilities (must be positive)
    
    Returns
    -------
    np.ndarray
        Call option prices
    
    See Also
    --------
    call_price_batch : Safe version with validation
    """
```

## チェックリスト

### 実装前
- [x] 既存コードの確認
- [x] パフォーマンス分析完了
- [x] 設計レビュー（別関数 vs 引数フラグ）

### 実装中
- [ ] 定期的なテスト実行
- [ ] コミット前の品質チェック
- [ ] 段階的な動作確認

### 実装後
- [ ] 全品質ゲート通過
- [ ] ベンチマーク結果記録
- [ ] ドキュメント更新
- [ ] 計画のarchive移動

## 成果物

- [ ] 最適化されたコア実装（core/src/compute/）
- [ ] unsafe版API（bindings/python/src/models.rs）
- [ ] パフォーマンステスト結果（benchmarks/）
- [ ] 更新されたベンチマーク（tests/performance/）
- [ ] ユーザー向けドキュメント（docs/api/）
- [ ] CHANGELOG.md更新

## 備考

- PyArrowサポートは既に動作していることが確認済み（ゼロコピー）
- NumPy配列変換のオーバーヘッドは2.4%と小さいことが判明
- 本最適化により、プロトタイプ性能を超える見込み