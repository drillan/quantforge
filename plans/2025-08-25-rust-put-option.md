# [Rust] ヨーロピアンプットオプション実装計画

## メタデータ
- **作成日**: 2025-08-25
- **言語**: Rust
- **ステータス**: ACTIVE
- **推定規模**: 中
- **推定コード行数**: 300-400行
- **対象モジュール**: src/models/black_scholes.rs, src/models/black_scholes_parallel.rs, src/lib.rs

## タスク規模判定

### 判定基準
- [x] 推定コード行数: 350行
- [x] 新規ファイル数: 0個（既存ファイルへの追加）
- [x] 影響範囲: 複数モジュール
- [x] PyO3バインディング: 必要
- [ ] SIMD最適化: 将来対応
- [x] 並列化: 必要（既存のRayon実装を活用）

### 規模判定結果
**中規模タスク**

## 品質管理ツール（Rust）

### 適用ツール（規模に応じて自動選択）
| ツール | 小規模 | 中規模 | 大規模 | 実行コマンド |
|--------|--------|--------|--------|-------------|
| cargo test | ✅ | ✅ | ✅ | `cargo test --all` |
| cargo clippy | ✅ | ✅ | ✅ | `cargo clippy -- -D warnings` |
| cargo fmt | ✅ | ✅ | ✅ | `cargo fmt --check` |
| similarity-rs | - | 条件付き | ✅ | `similarity-rs --threshold 0.80 src/` |
| rust-refactor.md | - | 条件付き | ✅ | `.claude/commands/rust-refactor.md` 適用 |
| cargo bench | - | 推奨 | ✅ | `cargo bench` |

## 実装詳細

### 1. Black-Scholesプットオプション公式
```rust
// ヨーロピアンプットオプション価格
P = K * exp(-r*T) * N(-d2) - S * N(-d1)

// d1, d2はコールオプションと同じ
d1 = (ln(S/K) + (r + σ²/2)*T) / (σ*√T)
d2 = d1 - σ*√T
```

### 2. 実装方針（C004/C014: 理想実装ファースト）
- 最初から理想形を実装し、技術的負債ゼロを維持
- コールオプションと同等の精度・性能を実現
- DRY原則に従い、d1/d2計算を共通化

### 3. 主要実装項目

#### src/models/black_scholes.rs
```rust
// プット価格計算（単一）
pub fn bs_put_price(s: f64, k: f64, t: f64, r: f64, v: f64) -> f64

// プット価格計算（バッチ）
pub fn bs_put_price_batch(spots: &[f64], k: f64, t: f64, r: f64, v: f64) -> Vec<f64>

// d1, d2計算の共通化（内部関数）
fn calculate_d1_d2(s: f64, k: f64, t: f64, r: f64, v: f64) -> (f64, f64)
```

#### src/models/black_scholes_parallel.rs
```rust
// 並列バッチ処理
pub fn bs_put_price_batch_parallel(spots: &[f64], k: f64, t: f64, r: f64, v: f64) -> Vec<f64>
```

#### src/lib.rs（PyO3バインディング）
```rust
#[pyfunction]
fn calculate_put_price(s: f64, k: f64, t: f64, r: f64, v: f64) -> PyResult<f64>

#[pyfunction]
fn calculate_put_price_batch<'py>(
    py: Python<'py>,
    spots: PyReadonlyArray1<f64>,
    k: f64, t: f64, r: f64, v: f64
) -> PyResult<Bound<'py, PyArray1<f64>>>
```

## フェーズ構成（中規模実装）

### Phase 1: 設計（1時間）
- [x] Black-Scholesプット公式の確認
- [x] 既存コールオプション実装の分析
- [x] DRY原則適用箇所の特定（d1/d2計算）
- [x] インターフェース設計

### Phase 2: 実装（4時間）

#### Step 1: コア機能実装
- [ ] `calculate_d1_d2()`共通関数の実装
- [ ] 既存コール関数をリファクタリング（共通関数使用）
- [ ] `bs_put_price()`実装
- [ ] `bs_put_price_batch()`実装
- [ ] 単体テスト作成

#### Step 2: 並列処理実装
- [ ] `bs_put_price_batch_parallel()`実装
- [ ] 既存の並列化閾値（30000要素）を再利用
- [ ] 並列処理テスト作成

#### Step 3: PyO3バインディング
- [ ] `calculate_put_price()`実装
- [ ] `calculate_put_price_batch()`実装
- [ ] 入力検証の実装（validate_inputs使用）
- [ ] Python型定義ファイル更新（__init__.pyi）

### Phase 3: テスト実装（2時間）

#### 単体テスト（src/models/black_scholes.rs）
- [ ] ATM/ITM/OTMプットオプションテスト
- [ ] 価格境界テスト: 0 ≤ P ≤ K*exp(-rT)
- [ ] 極限値テスト（Deep ITM/OTM、満期直前）
- [ ] Put-Callパリティ検証: C - P = S - K*exp(-rT)

#### 統合テスト（tests/）
- [ ] ゴールデンマスターテスト（Hull教科書の参照値）
- [ ] プロパティベーステスト（単調性、凸性）
- [ ] パフォーマンステスト
- [ ] バッチ処理の一貫性テスト

### Phase 4: 品質チェック（1時間）
```bash
# 基本チェック
cargo test --all
cargo clippy -- -D warnings
cargo fmt --check

# Python品質チェック
uv run ruff format .
uv run ruff check .
uv run mypy .

# 重複チェック
similarity-rs --threshold 0.80 --skip-test src/
# 閾値超えの重複があれば rust-refactor.md 適用
```

## 技術要件

### 必須要件
- [x] エラー率 < `PRACTICAL_TOLERANCE` (1e-3)
- [x] メモリ安全性（Rust保証）
- [x] スレッド安全性（Send + Sync）
- [x] Put-Callパリティの保持

### パフォーマンス目標
- [ ] 単一計算: < 10ns（コールと同等）
- [ ] バッチ処理（100万件）: < 20ms
- [ ] メモリ使用量: 入力データの1.5倍以内

### PyO3連携
- [x] ゼロコピー実装（NumPy配列の直接参照）
- [x] GIL解放での並列処理
- [x] 適切なエラー変換（PyValueError）

## テスト検証項目

### 数学的性質
1. **価格境界**
   - 下限: max(K*exp(-rT) - S, 0)
   - 上限: K*exp(-rT)

2. **Put-Callパリティ**
   - C - P = S - K*exp(-rT)
   - 相対誤差 < PRACTICAL_TOLERANCE

3. **Greeks（将来実装）**
   - Delta: -N(-d1)
   - Gamma: コールと同一
   - Vega: コールと同一
   - Theta: 異なる
   - Rho: 異なる

### エッジケース
- Deep ITM: P ≈ K*exp(-rT) - S
- Deep OTM: P ≈ 0
- 満期直前: P ≈ max(K - S, 0)
- ゼロボラティリティ: P = max(K*exp(-rT) - S, 0)

## リスクと対策

| リスク | 影響度 | 対策 |
|--------|--------|------|
| d1/d2計算の重複 | 中 | 共通関数化でDRY原則遵守 |
| 数値精度劣化 | 高 | ゴールデンマスターテスト、Put-Callパリティ検証 |
| Deep OTM負値 | 低 | max(0.0)で下限クリップ |

## チェックリスト

### 実装前
- [x] 既存コールオプション実装の確認
- [x] norm_cdf関数の理解
- [x] 定数定義の確認（constants.rs）

### 実装中
- [ ] d1/d2計算の共通化確認
- [ ] 定期的なテスト実行
- [ ] コミット前の`cargo fmt`

### 実装後
- [ ] 全品質ゲート通過
- [ ] Put-Callパリティ検証
- [ ] ベンチマーク結果記録
- [ ] ドキュメント更新

## 成果物

- [ ] 実装コード（src/models/black_scholes.rs拡張）
- [ ] 並列処理コード（src/models/black_scholes_parallel.rs拡張）
- [ ] PyO3バインディング（src/lib.rs拡張）
- [ ] テストコード（単体・統合・プロパティ）
- [ ] Python型定義（python/quantforge/__init__.pyi）
- [ ] ドキュメント（rustdoc、docstring）

## 参考資料

1. Hull, J. C. (2018). Options, Futures, and Other Derivatives (10th ed.)
2. 既存実装: src/models/black_scholes.rs（コールオプション）
3. Put-Callパリティ: C - P = S - K*exp(-rT)
4. Black-Scholes公式: https://en.wikipedia.org/wiki/Black–Scholes_model

## 実装の優先順位

1. **必須（Phase 1）**
   - 基本的なプット価格計算
   - Put-Callパリティ検証
   - 単体テスト

2. **重要（Phase 2）**
   - バッチ処理
   - 並列化
   - ゴールデンマスターテスト

3. **推奨（将来）**
   - Greeks計算
   - SIMD最適化
   - インプライドボラティリティ

---

**次のステップ**: Phase 2の実装開始（d1/d2共通化から着手）