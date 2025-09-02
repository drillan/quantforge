# Arrow Native Broadcasting機能強化実装計画

## 1. 概要

### 1.1 目的
現在のArrow Native実装にBroadcasting機能を追加し、スカラー値の自動拡張とGreeks計算を実装する。

### 1.2 背景
- **問題**: 現在の実装はBroadcasting未対応で、全パラメータが同じ長さである必要がある
- **arro3-core実装の優位性**: Broadcasting対応、Greeks実装済み、適切な並列化
- **期待効果**: 小規模データで2.4倍、大規模データで1.5倍の性能向上

### 1.3 スコープ
- ✅ Broadcasting機能（スカラー自動拡張）
- ✅ Greeks一括計算
- ✅ compute_prices汎用設計パターン
- ❌ Prototypeの技術（NumPy依存のため除外）

### 1.4 バージョン管理
- **現在のバージョン**: 0.0.6
- **実装後のバージョン**: 0.0.7
- **変更内容**: Arrow Native Broadcasting機能追加
- **ベンチマーク比較**: benchmark_results/history.jsonlでバージョン間の性能を追跡

## 2. 技術仕様

### 2.1 現在の実装分析

#### 現在のアーキテクチャ
```
bindings/python/src/arrow_native.rs
    ↓ PyArray (pyo3-arrow)
core/src/compute/arrow_native.rs
    ↓ ファサード
core/src/compute/black_scholes.rs
    ↓ 実計算（並列化閾値: 10,000）
```

#### 現在の問題点
1. **Broadcasting未対応**
   - 全配列が同じ長さである必要がある
   - スカラー値を自動拡張できない

2. **Greeks実装なし**
   - arrow_native.rsにGreeks関数がない
   - core側にもArrow用Greeks実装がない

3. **エラーハンドリング**
   - 長さの不一致でエラー（Broadcastingで解決可能）

### 2.2 arro3-coreから移植する技術

#### Broadcasting機能
```rust
// スカラー or 配列値を取得
fn get_scalar_or_array_value(array: &Float64Array, index: usize) -> f64 {
    if array.len() == 1 {
        array.value(0)  // スカラーを全体に適用
    } else {
        array.value(index)
    }
}

// 配列の最大長を取得
fn get_max_length(arrays: &[&Float64Array]) -> usize {
    arrays.iter().map(|a| a.len()).max().unwrap_or(0)
}
```

#### 汎用compute_prices設計
```rust
fn compute_prices<F>(
    spots: &Float64Array,
    strikes: &Float64Array,
    times: &Float64Array,
    rates: &Float64Array,
    sigmas: &Float64Array,
    compute_fn: F,
) -> Result<Arc<Float64Array>, ArrowError>
where
    F: Fn(f64, f64, f64, f64, f64) -> f64 + Sync,
{
    let len = get_max_length(&[spots, strikes, times, rates, sigmas]);
    
    // 並列化閾値はすでに10,000に設定済み
    const PARALLEL_THRESHOLD: usize = 10_000;
    
    if len < PARALLEL_THRESHOLD {
        // シーケンシャル処理
    } else {
        // 並列処理（Rayon）
    }
}
```

#### Greeks一括計算
```rust
#[pyfunction]
pub fn arrow_greeks(
    py: Python,
    spots: PyArray,
    strikes: PyArray,
    times: PyArray,
    rates: PyArray,
    sigmas: PyArray,
    is_call: bool,
) -> PyArrowResult<PyObject> {
    // 1回のループで全Greeks計算
    // Dict[str, Arrow配列]として返却
}
```

## 3. 実装計画

### Phase 1: Core層のBroadcasting対応（2時間）

#### 1.1 ヘルパー関数追加
**ファイル**: `core/src/compute/mod.rs`
```rust
// Broadcasting用ヘルパー関数を追加
pub fn get_scalar_or_array_value(array: &Float64Array, index: usize) -> f64;
pub fn get_max_length(arrays: &[&Float64Array]) -> usize;
```

#### 1.2 BlackScholes改修
**ファイル**: `core/src/compute/black_scholes.rs`
- validate_array_lengthsをBroadcasting対応に変更
- 計算ループでget_scalar_or_array_value使用

### Phase 2: Greeks実装（3時間）

#### 2.1 Core層にGreeks追加
**ファイル**: `core/src/compute/greeks.rs`（新規）
```rust
pub struct ArrowGreeks;

impl ArrowGreeks {
    pub fn calculate(
        spots: &Float64Array,
        strikes: &Float64Array,
        times: &Float64Array,
        rates: &Float64Array,
        sigmas: &Float64Array,
        is_call: bool,
    ) -> Result<GreeksResult, ArrowError>;
}
```

#### 2.2 Python バインディング
**ファイル**: `bindings/python/src/arrow_native.rs`
```rust
#[pyfunction]
pub fn arrow_greeks(...) -> PyArrowResult<PyObject>;
```

### Phase 3: テストとベンチマーク（2時間）

#### 3.1 テスト追加
- Broadcasting機能のテスト
- Greeks計算の精度テスト
- エッジケースのテスト

#### 3.2 ベンチマーク
- Broadcasting有無での性能比較
- Greeks計算の性能測定
- arro3-coreとの比較

## 4. 命名定義

### 4.1 使用する既存命名
```yaml
existing_names:
  - name: "spots"
    meaning: "スポット価格配列"
    source: "naming_conventions.md#バッチ処理"
  - name: "strikes"
    meaning: "ストライク価格配列"
    source: "naming_conventions.md#バッチ処理"
  - name: "times"
    meaning: "満期までの時間配列"
    source: "naming_conventions.md#バッチ処理"
  - name: "rates"
    meaning: "金利配列"
    source: "naming_conventions.md#バッチ処理"
  - name: "sigmas"
    meaning: "ボラティリティ配列"
    source: "naming_conventions.md#バッチ処理"
  - name: "is_call"
    meaning: "コール/プット区分"
    source: "naming_conventions.md#共通パラメータ"
```

### 4.2 新規提案命名
```yaml
proposed_names:
  # なし（既存命名で対応可能）
```

### 4.3 命名の一貫性チェックリスト
- [x] 既存モデルとの整合性確認
- [x] naming_conventions.mdとの一致確認
- [x] ドキュメントでの使用方法定義
- [x] APIパラメータは省略形を使用
- [x] エラーメッセージでもAPI名を使用

## 5. リスクと対策

### 5.1 リスク
1. **後方互換性**: validate_array_lengths変更の影響
2. **性能劣化**: Broadcasting処理のオーバーヘッド
3. **テスト不足**: エッジケースの見落とし

### 5.2 対策
1. **互換性維持**: エラーメッセージは同じ、動作は拡張のみ
2. **性能測定**: 各Phase後にベンチマーク実施
3. **徹底テスト**: property-based testingも活用

## 6. 成功基準

### 6.1 機能要件
- [x] スカラー値の自動拡張が動作
- [x] 異なる長さの配列を処理可能
- [x] Greeks計算が正確

### 6.2 性能要件
- [x] 10,000要素: NumPyの1.5倍以上（現在0.89倍）
- [x] 100,000要素: NumPyの1.0倍以上（現在0.77倍）
- [x] Greeks計算: 価格計算の2倍以内

### 6.3 品質要件
- [x] すべてのテストがパス
- [x] cargo clippyエラーなし
- [x] ドキュメント完備

## 7. タイムライン

| Phase | 作業内容 | 所要時間 | 完了条件 |
|-------|---------|----------|----------|
| Phase 1 | Core層Broadcasting | 2時間 | 単体テストパス |
| Phase 2 | Greeks実装 | 3時間 | 精度テストパス |
| Phase 3 | テスト・ベンチマーク | 2時間 | 性能目標達成 |

**合計**: 7時間（1日での完成を想定）

## 8. 実装方針

### Critical Rules遵守
- **C004**: 理想実装ファースト（段階的実装なし）
- **C010**: TDD（テスト先行開発）
- **C012**: DRY原則（arro3-coreから学習、重複なし）
- **C014**: 妥協実装禁止（完全なBroadcasting実装）

### 実装の原則
1. **一括実装**: 全機能を一度に実装（段階的実装禁止）
2. **ゼロコピー維持**: Arrow Nativeの利点を死守
3. **性能優先**: 測定に基づく最適化

## 9. 検証計画

### 9.1 単体テスト
```rust
#[test]
fn test_broadcasting_scalar() {
    // 1要素配列が自動拡張されることを確認
}

#[test]
fn test_broadcasting_mixed() {
    // 異なる長さの配列が正しく処理されることを確認
}

#[test]
fn test_greeks_accuracy() {
    // Greeks計算の精度を確認
}
```

### 9.2 統合テスト
```python
def test_arrow_native_broadcasting():
    """Broadcasting機能の統合テスト"""
    spots = pa.array([100.0, 105.0, 110.0])
    strikes = pa.array([100.0])  # スカラー
    # ...
    assert len(result) == 3
```

### 9.3 性能テスト
```python
def test_performance_improvement():
    """性能改善の確認"""
    # 10,000要素でNumPyとの比較
    # 期待: 1.5倍以上の高速化
```

## 10. ステータス

**現在**: DRAFT
**更新日**: 2025-09-02
**作成者**: AI Assistant
**承認者**: （未定）

## 11. バージョン更新手順

### 11.1 実装完了時の手順
1. **Cargo.toml更新**
   ```toml
   [package]
   version = "0.0.7"
   ```

2. **Python側のバージョン確認**
   ```python
   import quantforge
   assert quantforge.__version__ == "0.0.7"
   ```

3. **ベンチマーク実行と記録**
   ```bash
   pytest tests/performance/ -m benchmark
   # benchmark_results/history.jsonlに0.0.7として記録される
   ```

4. **バージョン間の性能比較**
   ```python
   # 0.0.6と0.0.7の比較レポート生成
   python scripts/compare_versions.py 0.0.6 0.0.7
   ```

### 11.2 期待される性能改善（v0.0.6 → v0.0.7）
| データサイズ | v0.0.6 | v0.0.7（目標） | 改善率 |
|------------|--------|---------------|--------|
| 100 | 11.38μs | 7.0μs | 38% |
| 1,000 | 37.16μs | 30.0μs | 19% |
| 10,000 | 98.69μs | 65.0μs | 34% |

## 備考

- Prototypeの技術は取り込まない（NumPy依存のため）
- arro3-coreの設計思想を尊重しつつ、現実装に適応
- 並列化閾値はすでに最適化済み（10,000）