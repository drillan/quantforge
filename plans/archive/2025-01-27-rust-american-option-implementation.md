# [Rust] アメリカンオプション Bjerksund-Stensland モデル実装計画

## メタデータ
- **作成日**: 2025-01-27
- **言語**: Rust
- **ステータス**: COMPLETED
- **完了日**: 2025-08-27
- **実際のコード行数**: 約1,200行（推定800-1000行）
- **推定規模**: 大
- **推定コード行数**: 800-1000行
- **対象モジュール**: src/models/american, src/python_modules.rs, src/lib.rs

## タスク規模判定

### 判定基準
- [x] 推定コード行数: 800-1000行
- [x] 新規ファイル数: 5個（mod.rs, pricing.rs, greeks.rs, implied_volatility.rs, boundary.rs）
- [x] 影響範囲: 複数モジュール（models, python_modules, lib）
- [x] PyO3バインディング: 必要
- [x] SIMD最適化: 必要（バッチ処理）
- [x] 並列化: 必要（Rayon使用）

### 規模判定結果
**大規模タスク**

## 品質管理ツール（Rust）

### 適用ツール（大規模タスク）
| ツール | 適用 | 実行コマンド |
|--------|------|-------------|
| cargo test | ✅ | `cargo test --all` |
| cargo clippy | ✅ | `cargo clippy -- -D warnings` |
| cargo fmt | ✅ | `cargo fmt --check` |
| similarity-rs | ✅ | `similarity-rs --threshold 0.80 src/` |
| rust-refactor.md | ✅ | `.claude/commands/rust-refactor.md` 適用 |
| cargo bench | ✅ | `cargo bench` |
| miri（安全性） | 推奨 | `cargo +nightly miri test` |

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
  - name: "q"
    meaning: "配当利回り"
    source: "naming_conventions.md#Black-Scholes系"
  - name: "is_call"
    meaning: "オプションタイプ"
    source: "naming_conventions.md#共通パラメータ"
  - name: "greeks"
    meaning: "全グリークス計算"
    source: "naming_conventions.md#関数命名パターン"
```

### 4.2 新規提案命名
```yaml
proposed_names:
  - name: "exercise_boundary"
    meaning: "早期行使境界"
    justification: "アメリカンオプション特有の概念"
    references: "Hull (2018) Options, Futures, and Other Derivatives"
    status: "既にAPIドキュメントで使用中"
```

### 4.3 命名の一貫性チェックリスト
- [x] 既存モデルとの整合性確認（Black-Scholes, Black76, Merton）
- [x] naming_conventions.mdとの一致確認
- [x] ドキュメントでの使用方法定義（docs/api/python/american.md）
- [x] APIパラメータは省略形を使用
- [x] エラーメッセージでもAPI名を使用

## 大規模実装フェーズ

### Phase 1: 設計フェーズ（1日）
- [ ] アーキテクチャ設計
  - [ ] American構造体定義
  - [ ] AmericanParams構造体定義
  - [ ] PricingModelトレイト実装計画
- [ ] モジュール分割設計
  - [ ] src/models/american/mod.rs - モジュール定義
  - [ ] src/models/american/pricing.rs - BS2002価格計算
  - [ ] src/models/american/greeks.rs - グリークス計算
  - [ ] src/models/american/implied_volatility.rs - IV計算
  - [ ] src/models/american/boundary.rs - 早期行使境界
- [ ] インターフェース定義
  - [ ] PricingModelトレイトの実装
  - [ ] Python API設計（PyO3）
- [ ] エラーハンドリング設計
  - [ ] 配当裁定防止（q > r）
  - [ ] 数値計算エラー処理

### Phase 2: 段階的実装（3-5日）

#### マイルストーン1: コア機能（2日）
- [ ] 基本データ構造
  - [ ] American構造体
  - [ ] AmericanParams構造体（s, k, t, r, q, sigma）
  - [ ] BS2002パラメータ（β, B∞, B0, I）
- [ ] コアアルゴリズム
  - [ ] Bjerksund-Stensland 2002実装
  - [ ] φ補助関数（draft/GBS_2025.py:_phi()参照）
  - [ ] ψ補助関数（draft/GBS_2025.py:_psi()参照）
  - [ ] 累積二変量正規分布（draft/GBS_2025.py:_cbnd()参照）
  - [ ] 早期行使境界計算
- [ ] 単体テスト
  - [ ] 価格計算テスト（GBS_2025.py L1705-1707の期待値使用）
  - [ ] 境界条件テスト
- [ ] **中間品質チェック**
  ```bash
  cargo test --lib
  cargo clippy -- -D warnings
  similarity-rs --threshold 0.80 src/models/american/
  ```

#### マイルストーン2: 拡張機能（2日）
- [ ] 追加機能実装
  - [ ] グリークス計算（早期行使考慮）
  - [ ] インプライドボラティリティ（二分探索法、GBS_2025.py:_bisection_implied_vol参照）
  - [ ] 早期行使境界API
- [ ] PyO3バインディング
  - [ ] call_price, put_price
  - [ ] call_price_batch, put_price_batch
  - [ ] greeks, implied_volatility
  - [ ] exercise_boundary
- [ ] 統合テスト
  - [ ] プロパティテスト（アメリカン ≥ ヨーロピアン）
  - [ ] ゴールデンマスターテスト（draft/GBS_2025.pyによる期待値生成）
  - [ ] プット-コール変換テスト（GBS_2025.py L1212-1224参照）
- [ ] **similarity-rs実行**

#### マイルストーン3: 最適化（1日）
- [ ] SIMD実装
  - [ ] AVX2/AVX-512対応
  - [ ] バッチ処理最適化
- [ ] 並列化（Rayon）
  - [ ] 大規模バッチ処理
  - [ ] GIL解放での並列実行
- [ ] ベンチマーク
  - [ ] 単一計算: 目標 < 50ns
  - [ ] 100万件バッチ: 目標 < 100ms

### Phase 3: 統合テスト（1日）
- [ ] 全機能の統合テスト
  - [ ] Python APIテスト
  - [ ] エッジケーステスト（GBS_2025.py L1734-1757参照）
  - [ ] 配当裁定テスト（q > r でエラー確認）
- [ ] GBS_2025.pyとの精度比較
  - [ ] 標準テストケース（L1705-1711）
  - [ ] 境界値テスト（L1742-1757）
  - [ ] 精度要件: 相対誤差 < 0.1%
- [ ] パフォーマンステスト
  - [ ] ベンチマーク実行
  - [ ] プロファイリング
  - [ ] 目標: Python実装比100倍以上高速
- [ ] メモリリークチェック
  - [ ] valgrind/miri実行

### Phase 4: リファクタリングフェーズ（必須: 1日）
- [ ] **rust-refactor.md 完全適用**
- [ ] similarity-rs で最終確認
- [ ] コード整理と最適化
  - [ ] 定数の適切な定義（constants.rs）
  - [ ] DRY原則の徹底
- [ ] ドキュメント完成
  - [ ] rustdoc完備
  - [ ] 使用例追加

## 技術要件

### 必須要件
- [x] エラー率 < PRACTICAL_TOLERANCE (1e-3)
- [x] メモリ安全性（Rust保証）
- [x] スレッド安全性（Send + Sync）
- [x] 配当裁定防止（q > r でエラー）

### パフォーマンス目標
- [ ] 単一計算: < 50ns
- [ ] 100万件バッチ: < 100ms
- [ ] メモリ使用量: 入力データの2倍以内

### PyO3連携
- [ ] ゼロコピー実装（NumPy配列）
- [ ] GIL解放での並列処理
- [ ] 適切なエラー変換（QuantForgeError → PyException）

## 定数定義（constants.rsに追加）

```rust
// Bjerksund-Stensland 2002モデル定数
pub const BS2002_BETA_MIN: f64 = 0.5;           // βパラメータ最小値
pub const BS2002_CONVERGENCE_TOL: f64 = 1e-9;   // 収束判定閾値
pub const EXERCISE_BOUNDARY_MAX_ITER: usize = 20; // 境界探索最大反復
pub const BS2002_H_FACTOR: f64 = 2.0;           // h(T)計算係数
```

## リスクと対策

| リスク | 影響度 | 対策 |
|--------|--------|------|
| BS2002近似精度 | 高 | ゴールデンマスターテスト（draft/GBS_2025.py参照） |
| 早期行使境界の不連続性 | 中 | 適応的メッシュ、スムージング |
| 配当裁定機会 | 高 | q > r での明示的エラー |
| SIMD可搬性 | 中 | 動的ディスパッチ、フォールバック実装 |

## チェックリスト

### 実装前
- [ ] 既存コードの確認（BlackScholes, Black76, Merton実装参照）
- [ ] 依存関係の確認（math::distributions、error、constants）
- [ ] 設計レビュー（アーキテクチャ、API設計）

### 実装中
- [ ] 定期的なテスト実行（TDD: Red-Green-Refactor）
- [ ] コミット前の`cargo fmt`
- [ ] 段階的な動作確認（マイルストーン毎）

### 実装後
- [ ] 全品質ゲート通過
  - [ ] cargo test --all
  - [ ] cargo clippy -- -D warnings
  - [ ] similarity-rs < 80%閾値
  - [ ] ruff/mypy（Pythonテスト）
- [ ] ベンチマーク結果記録
- [ ] ドキュメント更新
- [ ] 計画のarchive移動

## 成果物

- [ ] 実装コード（src/models/american/）
- [ ] テストコード（tests/unit/test_american_*.py）
- [ ] ベンチマーク（benches/american_benchmark.rs）
- [ ] ドキュメント（rustdoc、docs/api/python/american.md更新）
- [ ] PyO3バインディング（src/python_modules.rs追加）

## 備考

### 参考資料
- Bjerksund, P. and Stensland, G. (2002). "Closed Form Valuation of American Options"
- Hull, J.C. (2018). "Options, Futures, and Other Derivatives"
- 既存実装: BlackScholes, Black76, Merton（アーキテクチャ参照）
- **draft/GBS_2025.py**: Bjerksund-Stensland 2002の参照実装とテストケース

### 特記事項
- 配当なしコールの場合、ヨーロピアンと同価格（早期行使しない）
- プットは常にアメリカン > ヨーロピアン
- 数値精度要件: 誤差 < 0.1%（実務精度）

### GBS_2025.py参照箇所
- `_bjerksund_stensland_2002()` (L1107-1188): メインアルゴリズム実装
- `_phi()` (L1014-1033): φ補助関数
- `_psi()` (L980-1010): ψ補助関数
- `_cbnd()` (L875-972): 累積二変量正規分布
- `_american_option()` (L1197-1224): プット-コール変換
- `_bisection_implied_vol()` (L1279-1336): インプライドボラティリティ計算
- テストケース (L1705-1757): ゴールデンマスター期待値

### QuantLib不要の理由
- draft/GBS_2025.pyに同一アルゴリズム（BS2002）が実装済み
- 豊富なテストケースで精度0.001を検証済み
- 外部依存を増やさず、技術的負債ゼロを維持