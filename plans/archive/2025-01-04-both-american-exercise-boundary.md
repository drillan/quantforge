# [Rust/Python] Americanオプション exercise_boundary 実装計画

## メタデータ
- **作成日**: 2025-01-04
- **言語**: Rust + Python (両言語統合)
- **ステータス**: COMPLETED
- **推定規模**: 中
- **推定コード行数**: 300-400行
- **対象モジュール**: 
  - `core/src/compute/american.rs`
  - `bindings/python/src/models.rs`
  - `docs/ja/api/python/american.md`

## 背景と問題定義

### 現在の不整合
1. **ドキュメントに記載されている機能**
   - `exercise_boundary(s, k, t, r, q, sigma, is_call)` - 単一計算
   - `exercise_boundary_batch(...)` - バッチ計算
   
2. **実装されていない機能**
   - Python APIに両関数が存在しない
   - Rust実装の`calculate_exercise_boundary`は`#[allow(dead_code)]`で未使用

3. **逆に未文書化の実装**
   - `american_binomial` - 二項ツリー法は実装済みだが文書化されていない

### ビジネス要件
早期行使境界（exercise boundary）は以下の業務で必要：
- **トレーディング**: 早期行使タイミングの判断
- **リスク管理**: デルタヘッジ戦略の調整
- **価格検証**: モデルパラメータのキャリブレーション

## タスク規模判定

### 判定基準
- [x] 推定コード行数: 350行
- [x] 新規ファイル数: 0個（既存ファイルの修正）
- [x] 影響範囲: 複数モジュール
- [x] PyO3バインディング: 必要
- [x] SIMD最適化: 不要
- [x] 並列化: 将来対応

### 規模判定結果
**中規模タスク**

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
  - name: "q"
    meaning: "配当利回り"
    source: "naming_conventions.md#Black-Scholes系"
  - name: "sigma"
    meaning: "ボラティリティ"
    source: "naming_conventions.md#共通パラメータ"
  - name: "is_call"
    meaning: "オプションタイプ"
    source: "naming_conventions.md#共通パラメータ"
  - name: "n_steps"
    meaning: "時間ステップ数"
    source: "naming_conventions.md#将来追加予定のモデル"
```

### 4.2 新規提案命名
```yaml
proposed_names:
  # 新規命名なし - すべて既存カタログから使用
```

### 4.3 命名の一貫性チェックリスト
- [x] 既存モデルとの整合性確認
- [x] naming_conventions.mdとの一致確認
- [x] ドキュメントでの使用方法定義
- [x] APIパラメータは省略形を使用
- [x] エラーメッセージでもAPI名を使用

## 実装方針

### フェーズ1: exercise_boundary実装（優先度：高）

#### 1.1 Rust層の実装
```rust
// core/src/compute/american.rs

// BAW近似を使用した安定版の実装
pub fn exercise_boundary_scalar(k: f64, t: f64, r: f64, q: f64, sigma: f64, is_call: bool) -> f64 {
    if is_call {
        calculate_critical_price_call(k, t, r, q, sigma)
    } else {
        calculate_critical_price_put(k, t, r, q, sigma)
    }
}

// Arrow Native バッチ処理
impl American {
    pub fn exercise_boundary(
        strikes: &Float64Array,
        times: &Float64Array,
        rates: &Float64Array,
        dividend_yields: &Float64Array,
        sigmas: &Float64Array,
        is_call: bool,
    ) -> Result<ArrayRef, ArrowError> {
        // Broadcasting対応のバッチ実装
    }
}
```

#### 1.2 Python バインディング
```rust
// bindings/python/src/models.rs

#[pyfunction]
#[pyo3(name = "exercise_boundary")]
#[pyo3(signature = (k, t, r, q, sigma, is_call))]
fn american_exercise_boundary(
    k: f64,
    t: f64,
    r: f64,
    q: f64,
    sigma: f64,
    is_call: bool,
) -> PyResult<f64> {
    // 入力検証
    validate_american_inputs(k, t, r, q, sigma)?;
    
    Ok(exercise_boundary_scalar(k, t, r, q, sigma, is_call))
}

#[pyfunction]
#[pyo3(name = "exercise_boundary_batch")]
fn american_exercise_boundary_batch(
    py: Python,
    strikes: PyArrayLike,
    times: PyArrayLike,
    rates: PyArrayLike,
    dividend_yields: PyArrayLike,
    sigmas: PyArrayLike,
    is_calls: PyArrayLike,
) -> PyArrowResult<PyObject> {
    // Arrow Native実装（ゼロコピー）
}
```

### フェーズ2: american_binomial文書化（優先度：中）

#### 2.1 ドキュメント追加
```markdown
### 二項ツリー法（高精度オプション）

american.binomial(s, k, t, r, q, sigma, n_steps, is_call)

高精度が必要な場合に使用する二項ツリー法。
計算時間はO(n_steps^2)だが、より正確な価格を提供。

パラメータ:
- n_steps: 時間ステップ数（デフォルト: 100）
```

### フェーズ3: BS2002修正（優先度：低/将来）

#### 3.1 数値安定性の改善
- Newton-Raphson法の収束条件改善
- 境界条件での特殊処理
- テストケースの拡充

## 品質管理ツール（Rust + Python）

### 適用ツール
| ツール | 実行コマンド | 目的 |
|--------|-------------|------|
| cargo test | `cargo test --all` | Rustユニットテスト |
| cargo clippy | `cargo clippy -- -D warnings` | Rustリント |
| pytest | `uv run pytest tests/` | Python統合テスト |
| ruff | `uv run ruff check .` | Pythonリント |
| mypy | `uv run mypy .` | Python型チェック |

## 実装チェックリスト

### Phase 1: 設計（完了）
- [x] 既存実装の調査
- [x] BAW近似の動作確認
- [x] 命名規則の確認

### Phase 2: 実装（4-6時間）
- [x] exercise_boundary_scalar関数の実装 ✅
- [x] Arrowバッチ処理の実装 ✅
- [x] Python バインディング追加 ✅
- [x] 入力検証の実装 ✅

### Phase 3: テスト（2時間）
- [x] Rustユニットテスト作成 ✅
- [x] Python統合テスト作成 ✅
- [x] 既知の解析解との比較 ✅
- [x] エッジケースのテスト ✅

### Phase 4: 文書化（1時間）
- [x] exercise_boundary関数のドキュメント修正 ✅
- [x] american_binomial関数の文書追加 ✅
- [x] 使用例の追加 ✅
- [x] パフォーマンス指標の測定 ✅

### Phase 5: 品質チェック（1時間） ✅
```bash
# Rust品質チェック
cargo test --all
cargo clippy -- -D warnings
cargo fmt --check

# Python品質チェック  
uv run ruff format .
uv run ruff check . --fix
uv run mypy .
uv run pytest tests/test_american.py

# 統合確認
uv run maturin develop --release
uv run python -c "from quantforge.american import exercise_boundary; help(exercise_boundary)"
```

## テスト戦略

### 単体テスト
```rust
#[test]
fn test_exercise_boundary_call() {
    // ATMコールの境界価格
    let boundary = exercise_boundary_scalar(100.0, 1.0, 0.05, 0.03, 0.2, true);
    assert!(boundary > 100.0); // コールの境界は権利行使価格より高い
}

#[test]
fn test_exercise_boundary_put() {
    // ATMプットの境界価格
    let boundary = exercise_boundary_scalar(100.0, 1.0, 0.05, 0.03, 0.2, false);
    assert!(boundary < 100.0); // プットの境界は権利行使価格より低い
}
```

### 統合テスト
```python
def test_exercise_boundary():
    # 単一計算
    boundary = american.exercise_boundary(100, 1.0, 0.05, 0.03, 0.2, True)
    assert boundary > 100  # Call boundary above strike
    
    # バッチ計算
    boundaries = american.exercise_boundary_batch(
        strikes=[95, 100, 105],
        times=1.0,
        rates=0.05,
        dividend_yields=0.03,
        sigmas=0.2,
        is_calls=True
    )
    assert len(boundaries) == 3
```

## パフォーマンス目標

| 操作 | 目標 | 測定方法 |
|------|------|----------|
| 単一境界計算 | < 100 ns | cargo bench |
| 1万件バッチ | < 10 ms | pytest-benchmark |
| メモリ使用 | 入力の1.5倍以内 | memory_profiler |

## リスクと対策

| リスク | 影響度 | 対策 |
|--------|--------|------|
| BS2002の数値不安定性 | 中 | BAW近似を先に実装、BS2002は将来対応 |
| 境界価格の精度 | 中 | 二項ツリー法との比較検証 |
| パフォーマンス劣化 | 低 | 並列化は将来検討 |

## 成果物

- [x] 実装計画書（本文書）
- [x] Rust実装コード（core/src/compute/american.rs） ✅
- [x] Pythonバインディング（bindings/python/src/models.rs） ✅
- [x] テストコード（tests/test_american.py） ✅
- [x] ドキュメント更新（docs/ja/api/python/american.md） ✅
- [x] ベンチマーク結果 ✅

## 完了条件

1. すべてのテストが成功
2. ドキュメントと実装の完全一致
3. 品質ゲートをすべて通過
4. パフォーマンス目標を達成

## 備考

- BS2002の完全実装は数値安定性の問題があるため、当面はBAW近似版を使用
- american_binomial（二項ツリー法）は既に実装済みで安定動作している
- 将来的にBS2002の数値問題を解決したら、より高精度な実装に切り替え可能