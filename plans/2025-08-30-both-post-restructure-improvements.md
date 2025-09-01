# [Both] Core+Bindings再構築後の改善実装計画

## メタデータ
- **作成日**: 2025-08-30
- **言語**: Both (Python + Rust)
- **ステータス**: DRAFT
- **推定規模**: 大規模
- **推定コード行数**: 2000+ 行
- **対象モジュール**: bindings/python/, src/, python/quantforge/, tests/

## ⚠️ 技術的負債ゼロの原則

**重要**: このプロジェクトでは技術的負債を一切作らないことを最優先とします。

### 禁止事項（アンチパターン）
❌ **段階的実装・TODO残し**
❌ **複数バージョンの共存**  
❌ **「後で最適化」前提の実装**
❌ **暫定的・一時的な実装**

✅ **正しいアプローチ：最初から完全実装**
- Greeks API統一は完全な設計で一度に実装
- American Optionsは完全動作するまで無効のまま
- パフォーマンス最適化は実測に基づいて実施

## タスク規模判定

### 判定基準
- [x] 推定コード行数: 2000+ 行
- [x] 新規ファイル数: 10+ 個
- [x] 影響範囲: 全体（bindings, core, tests）
- [x] Rust連携: 必要（Greeks API変更）
- [x] NumPy/Pandas使用: あり（バッチ処理）
- [ ] 非同期処理: 不要

### 規模判定結果
**大規模タスク**

## 品質管理ツール（Both）

### 適用ツール
| ツール | 必須 | 実行コマンド |
|--------|------|-------------|
| cargo test | ✅ | `cargo test --release` |
| cargo clippy | ✅ | `cargo clippy --all-targets --all-features` |
| pytest | ✅ | `uv run pytest` |
| ruff | ✅ | `uv run ruff check . --fix` |
| mypy | ✅ | `uv run mypy .` |
| similarity検査 | ✅ | Phase 4で実施 |
| ベンチマーク | ✅ | `cargo bench` + `uv run pytest --benchmark-only` |

### 品質ゲート（必達基準）
| 項目 | 基準 |
|------|------|
| テストパス率 | 95%以上（418テスト中397以上） |
| Rustコンパイル警告 | 0件 |
| Pythonリントエラー | 0件 |
| 型カバレッジ | 100% |
| パフォーマンス | NumPy同等以上 |

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
  - name: "delta"
    meaning: "デルタ（価格感応度）"
    source: "naming_conventions.md#Greeks"
  - name: "gamma"
    meaning: "ガンマ（デルタの変化率）"
    source: "naming_conventions.md#Greeks"
  - name: "vega"
    meaning: "ベガ（ボラティリティ感応度）"
    source: "naming_conventions.md#Greeks"
  - name: "theta"
    meaning: "シータ（時間価値減衰）"
    source: "naming_conventions.md#Greeks"
  - name: "rho"
    meaning: "ロー（金利感応度）"
    source: "naming_conventions.md#Greeks"
```

### 4.2 新規提案命名
```yaml
proposed_names: []  # 新規命名なし（既存の命名規則で対応可能）
```

### 4.3 命名の一貫性チェックリスト
- [x] 既存モデルとの整合性確認
- [x] naming_conventions.mdとの一致確認
- [x] ドキュメントでの使用方法定義
- [x] APIパラメータは省略形を使用
- [x] エラーメッセージでもAPI名を使用

## フェーズ構成

### Phase 1: Greeks API統一実装（緊急・2日）

#### 目標
- テスト失敗69個のうち55個（Greeks関連）を解決
- 単一計算とバッチ計算で一貫したインターフェース提供

#### タスク1.1: Rust側の統一実装
```rust
// bindings/python/src/models/common.rs（新規）
use std::collections::HashMap;
use pyo3::prelude::*;

/// 統一されたGreeks戻り値（単一・バッチ両対応）
#[pyfunction]
pub fn create_greeks_dict(
    delta: PyObject,
    gamma: PyObject,
    vega: PyObject,
    theta: PyObject,
    rho: PyObject,
) -> PyResult<HashMap<String, PyObject>> {
    let mut greeks = HashMap::new();
    greeks.insert("delta".to_string(), delta);
    greeks.insert("gamma".to_string(), gamma);
    greeks.insert("vega".to_string(), vega);
    greeks.insert("theta".to_string(), theta);
    greeks.insert("rho".to_string(), rho);
    Ok(greeks)
}
```

#### タスク1.2: 各モデルの修正
- black_scholes.rs: greeks関数をDict返却に変更
- black76.rs: 同上
- merton.rs: 同上（dividend_rho追加）

#### タスク1.3: テストの修正
```python
# 修正前（失敗）
assert greeks.delta == 0.6368

# 修正後（成功）
assert greeks['delta'] == pytest.approx(0.6368, rel=1e-4)
```

#### 検証項目
- [ ] 全Greeks関連テスト（55個）がパス
- [ ] 後方互換性の考慮（ユーザーゼロなので不要）
- [ ] ドキュメント更新

### Phase 2: テスト基盤修復（1日）

#### タスク2.1: benchmarksモジュール問題解決
```toml
# pyproject.toml
[tool.pytest.ini_options]
pythonpath = [".", "benchmarks"]
testpaths = ["tests"]
```

#### タスク2.2: test_init.py修正
```python
# 新しいモジュール構造に合わせる
def test_models_has_expected_functions():
    """modelsモジュールが期待される関数を持つか確認"""
    from quantforge import models
    
    # Black-Scholesはmodelsトップレベル
    assert hasattr(models, 'call_price')
    assert hasattr(models, 'put_price')
    assert hasattr(models, 'greeks')
    
    # Black76はサブモジュール
    assert hasattr(models, 'black76')
    assert hasattr(models.black76, 'call_price')
```

#### タスク2.3: test_batch_refactored.py基底クラス修正
```python
# tests/test_base.py（修正）
from abc import ABC, abstractmethod
import numpy as np
import pytest

class BaseBatchTest(ABC):
    """バッチテストの基底クラス"""
    # インポートパスを修正
```

#### 検証項目
- [ ] pytest実行時のインポートエラー解消
- [ ] 全418テスト収集成功
- [ ] CI/CDでの実行確認

### Phase 3: パフォーマンス最適化（3日）

#### タスク3.1: プロファイリング実施
```bash
# Rustプロファイリング
cargo install flamegraph
cargo flamegraph --bench benchmarks -- --bench

# Pythonプロファイリング  
uv run python -m cProfile -o profile.stats benchmarks/__main__.py
uv run python -m snakeviz profile.stats
```

#### タスク3.2: 並列化閾値の実測調整
```rust
// src/config/parallel.rs（新規）
pub struct ParallelConfig {
    pub threshold_small: usize,
    pub threshold_medium: usize,
    pub threshold_large: usize,
}

impl Default for ParallelConfig {
    fn default() -> Self {
        // 実測に基づく値
        Self {
            threshold_small: 50_000,   // 実測: 10,000では早すぎる
            threshold_medium: 100_000,
            threshold_large: 500_000,
        }
    }
}
```

#### タスク3.3: キャッシュ最適化
```rust
// メモリアライメント最適化
#[repr(C, align(64))]  // キャッシュライン境界
pub struct AlignedParams {
    pub spot: f64,
    pub strike: f64,
    pub time: f64,
    pub rate: f64,
    pub sigma: f64,
    _padding: [u8; 24],  // 64バイトに調整
}
```

#### 検証項目
- [ ] 10,000要素: NumPyの1.5倍以上高速
- [ ] 100,000要素: NumPy同等以上
- [ ] メモリ使用量: 入力データの2倍以内

### Phase 4: リファクタリング（必須・2日）

#### タスク4.1: 重複コード検出と統合
```bash
# Rust側
similarity-rs \
  --threshold 0.80 \
  --min-lines 5 \
  --lang rust \
  src/ bindings/

# Python側  
similarity-py \
  --threshold 0.80 \
  --min-lines 5 \
  quantforge/
```

#### タスク4.2: 共通処理の抽出
```rust
// src/models/common/validation.rs（新規）
pub fn validate_positive(value: f64, name: &str) -> Result<(), ModelError> {
    if value <= 0.0 {
        return Err(ModelError::InvalidInput(
            format!("{} must be positive", name)
        ));
    }
    Ok(())
}

// 各モデルで再利用
validate_positive(spot, "s")?;
validate_positive(strike, "k")?;
```

#### タスク4.3: テストヘルパーの統合
```python
# tests/helpers/assertions.py（新規）
def assert_greeks_equal(actual, expected, rtol=1e-4):
    """Greeks辞書の比較ヘルパー"""
    for key in ['delta', 'gamma', 'vega', 'theta', 'rho']:
        assert key in actual
        np.testing.assert_allclose(
            actual[key], expected[key], rtol=rtol
        )
```

#### 検証項目
- [ ] 重複率: Rust 5%未満、Python 5%未満
- [ ] 共通処理の完全抽出
- [ ] テストの可読性向上

### Phase 5: American Options復活（5日）

#### タスク5.1: アルゴリズム実装（Binomial Tree）
```rust
// src/models/american/binomial.rs（新規）
pub struct BinomialTree {
    steps: usize,
}

impl BinomialTree {
    pub fn price(&self, params: &AmericanParams, is_call: bool) -> f64 {
        // Cox-Ross-Rubinstein model実装
        // 完全動作するまでmergeしない
    }
}
```

#### タスク5.2: Python bindings追加
```rust
// bindings/python/src/models/american.rs（新規）
#[pymodule]
pub fn american(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(call_price, m)?)?;
    m.add_function(wrap_pyfunction!(put_price, m)?)?;
    m.add_function(wrap_pyfunction!(greeks, m)?)?;
    // バッチ関数も同時に実装
    Ok(())
}
```

#### タスク5.3: テスト復活と検証
```python
# tests/unit/test_american.py（有効化）
# TODOコメントを削除し、全テストを有効化
# 32箇所のTODOを一括処理
```

#### 検証項目
- [ ] 全Americanテスト（8テストファイル）パス
- [ ] GBS実装との誤差1%以内
- [ ] パフォーマンス: 100ステップで10ms以内

### Phase 6: ドキュメント更新（2日）

#### タスク6.1: API変更の反映
```markdown
# docs/api/python/greeks.md
## Greeks計算

### 戻り値の形式（v0.1.0以降）
単一計算・バッチ計算ともに辞書形式で統一されました。

```python
# 単一計算
greeks = black_scholes.greeks(s=100, k=100, t=1, r=0.05, sigma=0.2)
print(greeks['delta'])  # 0.6368

# バッチ計算
greeks = black_scholes.greeks_batch(
    spots=[100, 105, 110],
    strikes=100,
    times=1,
    rates=0.05,
    sigmas=0.2
)
print(greeks['delta'])  # array([0.6368, 0.7092, 0.7722])
```
```

#### タスク6.2: パフォーマンスガイド追加
```markdown
# docs/performance/optimization.md
## 最適化されたバッチサイズ

実測に基づく推奨設定：

| データ数 | 推奨API | 理由 |
|---------|---------|------|
| 1-1,000 | 単一計算ループ | オーバーヘッド回避 |
| 1,000-50,000 | バッチ（並列化なし） | メモリ効率優先 |
| 50,000+ | バッチ（自動並列化） | CPU活用最大化 |
```

#### タスク6.3: 実践例の追加
```python
# examples/portfolio_valuation.py（新規）
"""ポートフォリオ評価の実践例"""
import numpy as np
from quantforge import black_scholes

def evaluate_portfolio(positions):
    """複数オプションポジションの一括評価"""
    # 実装例
```

#### 検証項目
- [ ] 全APIドキュメント更新
- [ ] 実行可能な例10個以上
- [ ] 英語・日本語両対応

## リスクと対策

| リスク | 影響度 | 対策 |
|--------|--------|------|
| Greeks API変更の影響 | 高 | ユーザーゼロなので問題なし |
| パフォーマンス未達 | 中 | プロファイリング重視、段階的最適化 |
| American実装の複雑性 | 高 | 完全動作まで無効化維持 |
| テスト実行時間増加 | 低 | pytest-xdist並列実行 |

## チェックリスト

### 実装前
- [x] 既存コードの確認
- [x] 失敗テストの分析完了
- [x] 設計方針決定

### 実装中
- [ ] 各Phase完了時の品質チェック
- [ ] コミット前の全テスト実行
- [ ] パフォーマンス測定

### 実装後
- [ ] テストパス率95%以上
- [ ] ドキュメント完全更新
- [ ] ベンチマーク結果記録
- [ ] 計画のarchive移動

## 成果物

- [ ] Greeks API統一実装（bindings/python/src/models/）
- [ ] テスト修正（tests/全体）
- [ ] American Options実装（src/models/american/）
- [ ] パフォーマンス最適化（src/config/）
- [ ] 共通処理モジュール（src/models/common/）
- [ ] ドキュメント更新（docs/）
- [ ] 実践例追加（examples/）

## 成功指標

### 短期（1週間）
- [ ] テストパス率: 95%以上（397/418）
- [ ] Greeks API一貫性: 完全解決
- [ ] ビルドエラー: ゼロ

### 中期（2週間）
- [ ] American Options: 実装完了
- [ ] パフォーマンス: NumPy同等以上
- [ ] 重複コード: 5%未満

### 長期（1ヶ月）
- [ ] 全テスト: 100%パス
- [ ] ドキュメント: 完全整備
- [ ] ベンチマーク: 自動化完了

## 備考

- Core+Bindings再構築完了後の最優先課題対応
- 技術的負債ゼロの原則を厳守
- 段階的実装は行わず、各機能を完全実装してからマージ
- American Optionsは完全動作確認まで無効化を維持

---
作成者: Claude (Opus 4.1)
参照: plans/2025-08-30-core-bindings-restructure/remaining_tasks_and_improvements.md