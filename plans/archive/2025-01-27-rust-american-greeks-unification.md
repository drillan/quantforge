# [Rust] American Greeks戻り値形式統一 実装計画

## メタデータ
- **作成日**: 2025-01-27
- **完了日**: 2025-01-27
- **言語**: Rust/Python統合
- **ステータス**: COMPLETED
- **推定規模**: 中
- **推定コード行数**: 200-300行
- **対象モジュール**: src/models/american/batch.rs, src/python_modules.rs, Python tests

## 完了報告
- **実装時間**: 約3時間
- **進捗**: 100%
- **全タスク完了**: Phase 1-4のすべてのタスクを完了
- **成果**: American modelのgreeks_batch戻り値をDict[str, np.ndarray]形式に統一

## タスク規模判定

### 判定基準
- [x] 推定コード行数: 250行
- [x] 新規ファイル数: 1個（greeks.md）
- [x] 影響範囲: 複数モジュール（American batch処理とPyO3バインディング）
- [x] PyO3バインディング: 必要（修正）
- [x] SIMD最適化: 不要（既存実装を維持）
- [x] 並列化: 不要（既存実装を維持）

### 規模判定結果
**中規模タスク**

## 品質管理ツール（Rust）

### 適用ツール（規模に応じて自動選択）
| ツール | 小規模 | 中規模 | 大規模 | 実行コマンド |
|--------|--------|--------|--------|-------------|
| cargo test | - | ✅ | - | `cargo test --all` |
| cargo clippy | - | ✅ | - | `cargo clippy -- -D warnings` |
| cargo fmt | - | ✅ | - | `cargo fmt --check` |
| similarity-rs | - | 条件付き | - | `similarity-rs --threshold 0.80 src/` |
| rust-refactor.md | - | 条件付き | - | `.claude/commands/rust-refactor.md` 適用 |
| maturin develop | - | ✅ | - | `uv run maturin develop --release` |
| pytest | - | ✅ | - | `uv run pytest playground/test_american*.py` |

## 命名定義セクション

### 4.1 使用する既存命名
```yaml
existing_names:
  - name: "greeks_batch"
    meaning: "バッチGreeks計算関数"
    source: "naming_conventions.md#関数名"
  - name: "delta, gamma, vega, theta, rho"
    meaning: "標準的なGreeks名"
    source: "業界標準"
  - name: "GreeksBatch"
    meaning: "バッチGreeks結果構造体"
    source: "既存実装（Black76, Merton）"
```

### 4.2 新規提案命名
```yaml
proposed_names:
  # 新規命名なし - 既存パターンに完全準拠
```

### 4.3 命名の一貫性チェックリスト
- [x] 既存モデルとの整合性確認
- [x] naming_conventions.mdとの一致確認
- [x] ドキュメントでの使用方法定義
- [x] APIパラメータは省略形を使用
- [x] エラーメッセージでもAPI名を使用

## 問題の背景

### 現状の不統一
- **Black-Scholes, Black76, Merton**: `Dict[str, np.ndarray]`形式
- **American**: `List[PyGreeks]`形式 ← 不統一

### 原則違反
- **C012（DRY原則）違反**: 同じ機能に2つの異なる実装パターン
- **C013（破壊的リファクタリング推奨）違反**: 不統一な実装の共存
- **C008（ドキュメント整合性）違反**: ドキュメントは統一形式を定義済み

## フェーズ構成

### Phase 1: ドキュメント作成（D-SSoT原則適用）- 30分
- [x] `docs/api/python/greeks.md` 作成 ✅
  - Greeks戻り値形式の統一仕様を定義
  - 設計根拠（NumPy親和性、SoAメモリ効率）を明記
  - すべてのモデルが従うべき契約として定義
- [x] `docs/api/python/batch_processing.md` の更新 ✅
  - Line 221-224のAmericanモデルgreeks_batchの戻り値型を明確化
  - Migration Guide（Line 407-423）にAmericanモデル固有の移行例を追加

### Phase 2: 実装（2-3時間）

#### 2.1 Rust側の修正（src/models/american/batch.rs）
- [x] `GreeksBatch`構造体の追加 ✅
  ```rust
  pub struct GreeksBatch {
      pub delta: Vec<f64>,
      pub gamma: Vec<f64>,
      pub vega: Vec<f64>,
      pub theta: Vec<f64>,
      pub rho: Vec<f64>,
  }
  ```
- [x] `greeks_batch`関数の戻り値を`Vec<Greeks>`から`GreeksBatch`に変更 ✅
- [x] 並列処理部分の修正（collectの変更） ✅
- [x] 順次処理部分の修正（Vec構築の変更） ✅

#### 2.2 PyO3バインディングの修正（src/python_modules.rs）
- [x] `american_greeks_batch`の戻り値を`Vec<PyGreeks>`から`PyDict`に変更 ✅
- [x] Line 1149-1186の修正 ✅
  - 他モデル（line 194-201）と完全に同じDict生成パターンを使用
  ```rust
  // Create dictionary with NumPy arrays
  let dict = PyDict::new_bound(py);
  dict.set_item("delta", PyArray1::from_vec_bound(py, greeks_batch.delta))?;
  dict.set_item("gamma", PyArray1::from_vec_bound(py, greeks_batch.gamma))?;
  dict.set_item("vega", PyArray1::from_vec_bound(py, greeks_batch.vega))?;
  dict.set_item("theta", PyArray1::from_vec_bound(py, greeks_batch.theta))?;
  dict.set_item("rho", PyArray1::from_vec_bound(py, greeks_batch.rho))?;
  ```

### Phase 3: テスト更新（30分）
- [x] `playground/test_american_batch.py` の修正 ✅
  - Line 56-57, 91: `result[i].delta` → `result['delta'][i]`
- [x] `playground/test_american_1m.py` の修正 ✅  
  - Line 111: `[g.delta for g in greeks[:3]]` → `greeks['delta'][:3].tolist()`
- [x] 実行確認 ✅
  ```bash
  uv run python playground/test_american_batch.py
  uv run python playground/test_american_1m.py
  ```

### Phase 4: 品質チェック（30分）
```bash
# Rustコンパイル確認
cargo build --release

# Rust品質チェック
cargo test --all
cargo clippy -- -D warnings
cargo fmt --check

# 重複チェック（条件付き）
similarity-rs --threshold 0.80 --skip-test src/models/american/
# 閾値超えの重複があれば rust-refactor.md 適用

# PyO3バインディング再構築
uv run maturin develop --release

# Pythonテスト実行
uv run pytest playground/test_american*.py -v
```

## 技術要件

### 必須要件
- [x] 既存のパフォーマンスを維持（6.82M ops/sec以上）
- [x] メモリ効率の改善（SoA構造化）
- [x] NumPyとの完全な互換性
- [x] 他モデルとの完全な一貫性

### パフォーマンス目標
- [x] Greeks計算: 既存の50K ops/sec以上を維持
- [x] メモリ使用量: 入力データの2倍以内
- [x] 1M要素処理: 150ms以内

### PyO3連携
- [x] Dict[str, np.ndarray]形式での返却
- [x] ゼロコピー実装の維持
- [x] GIL解放での並列処理の維持

## リスクと対策

| リスク | 影響度 | 対策 |
|--------|--------|------|
| 既存テストの破壊 | 高 | テストを先に修正し、実装が追従 |
| パフォーマンス低下 | 中 | ベクター構築方法を最適化 |
| メモリ使用量増加 | 低 | SoA構造でむしろ改善される |

## チェックリスト

### 実装前
- [x] 既存Greeks実装の確認（Black76, Merton）
- [x] ドキュメントの現状確認
- [x] 影響範囲の特定

### 実装中
- [x] ドキュメントファースト（D-SSoT原則） ✅
- [x] 段階的なコンパイル確認 ✅
- [x] テスト駆動開発（C010原則） ✅

### 実装後
- [x] すべてのテストがパス ✅
- [x] パフォーマンス維持の確認 ✅
- [x] ドキュメントとの一致確認 ✅
- [x] 計画のarchive移動 ✅

## 成果物

- [x] `docs/api/python/greeks.md`（新規） ✅
- [x] `docs/api/python/batch_processing.md`（更新） ✅
- [x] `src/models/american/batch.rs`（修正） ✅
- [x] `src/python_modules.rs`（修正） ✅
- [x] `playground/test_american_batch.py`（修正） ✅
- [x] `playground/test_american_1m.py`（修正） ✅

## 備考

### C013原則の適用
- 移行期間なし、即座に統一形式へ置換
- 後方互換性不要（ユーザーゼロ前提）
- List[PyGreeks]形式は完全削除

### 期待される効果
1. API一貫性の確立
2. NumPyエコシステムとの完全な統合
3. メモリ効率の改善（AoS → SoA）
4. 将来のモデル追加時の明確な指針

### 参照
- 既存実装: `src/models/black76/batch.rs:154-160`
- 既存実装: `src/models/merton/batch.rs:157-163`
- PyO3パターン: `src/python_modules.rs:194-201`