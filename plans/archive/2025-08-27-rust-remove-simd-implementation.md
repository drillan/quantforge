# [Rust] SIMD実装の完全削除計画

## メタデータ
- **作成日**: 2025-08-27
- **言語**: Rust
- **ステータス**: DRAFT
- **推定規模**: 中規模
- **推定コード行数**: -210行（削除）、+20行（リファクタリング）
- **対象モジュール**: src/simd、src/lib.rs、src/models/american、src/math、docs/

## 背景と理由

### 現状の問題点
1. **未使用コード**: `src/simd/mod.rs`（210行）が存在するが一切使用されていない
2. **虚偽のドキュメント**: ドキュメントに「SIMD最適化済み」と記載されているが実装されていない
3. **誤解を招くAPI**: `call_price_batch_simd`という名前だが実際はRayonの並列処理のみ
4. **技術的負債**: 中途半端な実装が存在（C004、C014違反）
5. **精度リスク**: Taylor展開が4次までで金融計算に必要な精度（1e-3）を満たせない

### 削除の正当性（Critical Rules適用）
- **C004（理想実装ファースト）**: 中途半端なSIMD実装より完全なスカラー実装
- **C008（ドキュメント整合性）**: 実装と一致しない虚偽記載の除去
- **C013（破壊的リファクタリング推奨）**: V2を作らず既存を修正
- **C014（妥協実装絶対禁止）**: 未完成のSIMD実装は技術的負債

## タスク規模判定

### 判定基準
- [x] 推定コード行数: -210行（削除）、+20行（リファクタリング）
- [x] 削除ファイル数: 1個（src/simd/mod.rs）
- [x] 影響範囲: 複数モジュール（src/, docs/, benches/）
- [x] PyO3バインディング: 影響なし
- [x] SIMD最適化: **削除対象**
- [x] 並列化: Rayonは維持

### 規模判定結果
**中規模タスク**（主に削除作業だが、影響範囲が広い）

## 実装計画

### Phase 1: ドキュメント修正（1.5時間）【最優先】

> **理由**: ドキュメントの虚偽記載（C008違反）を最優先で修正し、ユーザーへの誤情報提供を防ぐ。
> コードは未使用なので後回しでも問題ない。

#### 1.1 最優先修正（虚偽記載の除去）
- [ ] `docs/performance/benchmarks.md`
  - "## SIMD最適化効果" セクション削除
  - "### AVX2 vs スカラー" テーブル削除
  - エネルギー効率セクションの "(SIMD)" 削除
- [ ] `docs/index.md`
  - "AVX2/AVX-512 SIMD命令セットによる並列計算" 削除
- [ ] `docs/faq.md`
  - "ARM（Apple Silicon含む）でも動作しますが、SIMD最適化は限定的です" 修正
  - "SIMD + 並列" → "並列処理"

#### 1.2 アーキテクチャドキュメント修正
- [ ] `docs/development/architecture.md`（14箇所）
  - SIMDエンジン関連の図と説明を削除
  - 処理戦略からSIMD関連を削除
- [ ] `docs/api/rust/index.md`（10箇所）
  - SIMD最適化セクション削除
  - SimdProcessor関連コード例削除

#### 1.3 その他のドキュメント修正
- [ ] `docs/performance/optimization.md`（8箇所）
- [ ] `docs/roadmap.md`（2箇所）
- [ ] `docs/user_guide/index.md`（1箇所）
- [ ] `docs/performance/tuning.md`（1箇所）
- [ ] `docs/models/` 各ファイル（計3箇所）
- [ ] `docs/internal/` 各ファイル（計2箇所）
- [ ] `docs/installation.md`（1箇所）
- [ ] `docs/changelog.md`（1箇所）
- [ ] `docs/development/setup.md`（1箇所）

#### 1.4 CLAUDE.md修正
- [ ] 96行目: "SIMDエンジン（AVX2/AVX-512対応）" 削除
- [ ] 103行目: "SIMD/スレッド並列を自動選択" → "スレッド並列を自動選択"
- [ ] 130行目: "「後でSIMD化する」前提の実装" 削除
- [ ] 137行目: "SIMD/並列化を最初から組み込む" → "並列化を最初から組み込む"
- [ ] 819行目: コメント例を修正

### Phase 2: コード削除とリファクタリング（2時間）

#### 2.1 ファイル削除
- [ ] `src/simd/mod.rs` 完全削除
- [ ] `src/lib.rs` から `pub mod simd;` 削除

#### 2.2 American Optionのリファクタリング
- [ ] `src/models/american/batch.rs`
  - 関数名変更: `call_price_batch_simd` → `call_price_batch`
  - 関数名変更: `put_price_batch_simd` → `put_price_batch`
  - コメント修正: "SIMD optimization" → "parallel processing"
- [ ] `src/models/american/mod.rs`
  - エクスポート修正: 新しい関数名でre-export

#### 2.3 Distributionsのクリーンアップ
- [ ] `src/math/distributions.rs`
  - `norm_cdf_simd` 関数削除
  - `norm_cdf_simd_scalar` 関数削除
  - 関連するTODOコメント削除

#### 2.4 その他のコメント修正
- [ ] `src/models/black_scholes.rs`
  - "将来のSIMD最適化対応" コメント削除

### Phase 3: テストとベンチマークの修正（30分）

#### 3.1 ベンチマーク修正
- [ ] `benches/american_benchmark.rs`
  - `use quantforge::models::american::call_price_batch_simd;` を
    `use quantforge::models::american::call_price_batch;` に変更
  - 関数呼び出しを新しい名前に変更（2箇所）

#### 3.2 Cargo.toml修正
- [ ] `[features]` セクションから `simd = []` 削除

### Phase 4: 品質チェック（30分）

```bash
# コンパイル確認
cargo build --release

# テスト実行
cargo test --all

# リンタ
cargo clippy -- -D warnings
cargo fmt --check

# ベンチマーク動作確認（パフォーマンス劣化がないことを確認）
cargo bench --bench american_benchmark

# ドキュメントビルド確認
cargo doc --no-deps

# Python側の確認
uv run maturin develop --release
uv run pytest tests/
```

## 命名定義セクション

### 4.1 使用する既存命名
```yaml
existing_names:
  - name: "call_price_batch"
    meaning: "バッチ処理用のコール価格計算"
    source: "既存のBlackScholesモデルと統一"
  - name: "put_price_batch"
    meaning: "バッチ処理用のプット価格計算"
    source: "既存のBlackScholesモデルと統一"
```

### 4.2 新規提案命名
なし（削除のみ、新規追加なし）

### 4.3 命名の一貫性チェックリスト
- [x] 既存モデルとの整合性確認（BlackScholesと統一）
- [x] naming_conventions.mdとの一致確認
- [x] ドキュメントでの使用方法定義
- [x] APIパラメータは省略形を使用（変更なし）
- [x] エラーメッセージでもAPI名を使用（変更なし）

## リスクと対策

| リスク | 影響度 | 対策 |
|--------|--------|------|
| パフォーマンス期待値のギャップ | 低 | ベンチマークで実性能を明記 |
| 将来のSIMD実装時の手戻り | 低 | 必要になったら新規実装（現コードは使えない） |
| ドキュメント修正漏れ | 中 | grepで全検索して確認 |
| ベンチマーク動作不良 | 低 | 事前にベンチマーク動作確認 |

## チェックリスト

### 実装前
- [x] 削除対象ファイルの確認
- [x] 影響範囲の調査完了
- [x] ドキュメント修正箇所の特定

### 実装中
- [ ] 段階的な削除とテスト実行
- [ ] コミット前の`cargo fmt`
- [ ] ベンチマーク動作確認

### 実装後
- [ ] 全品質ゲート通過
- [ ] パフォーマンス劣化なしを確認
- [ ] ドキュメント整合性確認
- [ ] 計画のarchive移動

## 成果物

### 削除されるもの
- `src/simd/mod.rs`（210行）
- SIMD関連のドキュメント記述（約50箇所）
- 誤解を招く関数名（`*_simd`）

### 改善されるもの
- ドキュメントの正確性（虚偽記載の除去）
- APIの明確性（名前と実装の一致）
- コードベースの簡潔性（未使用コードの削除）
- 技術的負債の解消（Critical Rules準拠）

## 期待される効果

1. **技術的負債ゼロ**: 中途半端な実装の完全除去
2. **ドキュメント信頼性向上**: 実装と一致する正確な記述
3. **保守性向上**: unsafeコードと複雑な条件分岐の削除
4. **明確な実装**: 「Rust + Rayon並列化」という正直な実装

## 備考

- 将来的にSIMDが本当に必要になった場合は、Intel MKL、SLEEF等の成熟したライブラリの利用を検討
- 現在のRayon並列化で十分な性能を達成している（100万件で38ms）
- 金融計算に必要な精度（1e-3）を維持することが最優先
- このプランは**破壊的変更**だが、後方互換性は不要（ユーザーゼロの前提）