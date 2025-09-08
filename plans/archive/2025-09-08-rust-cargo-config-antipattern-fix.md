# [Rust] Cargo設定アンチパターン修正とパフォーマンス検証 実装計画

## メタデータ
- **作成日**: 2025-09-08
- **言語**: Rust
- **ステータス**: DRAFT
- **推定規模**: 中
- **推定コード行数**: 50-100（設定変更中心）
- **対象モジュール**: .cargo/config.toml, Cargo.toml

## タスク規模判定

### 判定基準
- [x] 推定コード行数: 50-100 行（主に設定ファイル）
- [x] 新規ファイル数: 0 個
- [x] 影響範囲: 全体（ビルド設定）
- [x] PyO3バインディング: 影響あり（再ビルド必要）
- [x] SIMD最適化: 削除対象（アンチパターン）
- [x] 並列化: 不要（既存実装維持）

### 規模判定結果
**中規模タスク**（影響範囲が広いため）

## 背景と問題点

### 検出されたアンチパターン違反
1. **SIMD関連設定の使用**
   - `.cargo/config.toml`にAVX2/FMA/NEON設定が存在
   - プロジェクトルール（.claude/antipatterns/simd-optimization-trap.md）違反
   - 2025-08-27にSIMD実装を完全削除した経緯を無視

2. **日本語コミットメッセージ**
   - コミット`ccdde00`が日本語（修正済み）

### 現在の問題設定
```toml
# 削除対象
[target.x86_64-unknown-linux-gnu]
rustflags = ["-C", "target-feature=+avx2,+fma"]

[target.x86_64-apple-darwin]  
rustflags = ["-C", "target-feature=+avx2,+fma"]

[target.aarch64-apple-darwin]
rustflags = ["-C", "target-feature=+neon"]
```

## 品質管理ツール（Rust）

### 適用ツール
| ツール | 適用 | 実行コマンド |
|--------|------|-------------|
| cargo test | ✅ | `cargo test --all --release` |
| cargo clippy | ✅ | `cargo clippy -- -D warnings` |
| cargo fmt | ✅ | `cargo fmt --check` |
| cargo bench | ✅ | `cargo bench` |
| pytest | ✅ | `uv run pytest tests/performance/` |

## 実装フェーズ

### Phase 1: ベースライン測定（30分）
- [ ] 現在の設定でのパフォーマンス測定
  ```bash
  cargo bench --bench benchmark -- --save-baseline with-simd
  uv run pytest tests/performance/test_all_benchmarks.py -v --benchmark-json=baseline.json
  ```
- [ ] 重要メトリクス記録
  - 単一計算時間
  - 100/1000/10000件バッチ処理時間
  - メモリ使用量

### Phase 2: 設定修正（30分）
- [ ] `.cargo/config.toml`修正
  ```toml
  [build]
  rustflags = [
      "-C", "target-cpu=native",
      "-C", "prefer-dynamic=no",
  ]
  # target固有設定をすべて削除
  ```
- [ ] クリーンビルドと再インストール
  ```bash
  cargo clean
  cargo build --release
  uv run maturin develop --release
  ```

### Phase 3: 性能影響測定（30分）
- [ ] 修正後のベンチマーク実行
  ```bash
  cargo bench --bench benchmark -- --baseline with-simd
  uv run pytest tests/performance/test_all_benchmarks.py -v --benchmark-json=after.json
  ```
- [ ] 性能差分の分析
  - 各メトリクスでの変化率計算
  - 10,000件バッチでの影響重点確認

### Phase 4: 代替最適化検討（必要な場合: 1-2時間）

#### 判定基準
| 性能低下率 | 対応 |
|-----------|------|
| < 5% | そのまま進める |
| 5-15% | 代替最適化を検討 |
| > 15% | 代替最適化必須 |

#### 代替案A: コンパイラ最適化調整
```toml
[build]
rustflags = [
    "-C", "target-cpu=native",
    "-C", "prefer-dynamic=no",
    "-C", "inline-threshold=275",
    "-C", "llvm-args=-unroll-threshold=500",
]
```

#### 代替案B: コード最適化
- micro_batch.rsで8要素アンローリング
- 並列化閾値の再調整（PARALLEL_THRESHOLD_SMALL）

### Phase 5: 品質確認（30分）
- [ ] 全テスト合格確認
  ```bash
  cargo test --release --all
  uv run pytest tests/ -v
  ```
- [ ] 数値精度検証（PRACTICAL_TOLERANCE内）
- [ ] クロスプラットフォーム動作確認

## 命名定義

### 使用する既存命名
```yaml
existing_names:
  - name: "PARALLEL_THRESHOLD_SMALL"
    meaning: "小規模バッチの並列化閾値"
    source: "core/src/constants.rs"
  - name: "MICRO_BATCH_THRESHOLD"
    meaning: "マイクロバッチ最適化の閾値"
    source: "core/src/constants.rs"
```

### 新規提案命名
なし（設定変更のみ）

## リスクと対策

| リスク | 影響度 | 対策 |
|--------|--------|------|
| 性能低下 | 高 | ベンチマークで定量測定、代替最適化準備 |
| プラットフォーム依存 | 中 | target-cpu=nativeは維持、CI環境考慮 |
| ビルド時間増加 | 低 | LTO設定は維持、影響最小限 |

## 成功基準

- [ ] アンチパターン違反の完全解消
- [ ] 性能低下15%以内
- [ ] 全テスト合格（Rust 38件、Python 577件）
- [ ] ドキュメント更新完了

## チェックリスト

### 実装前
- [ ] 現在の性能ベースライン測定
- [ ] アンチパターンドキュメント確認
- [ ] 代替最適化案の準備

### 実装中
- [ ] 設定変更の段階的適用
- [ ] 各段階でのベンチマーク実施
- [ ] テスト継続実行

### 実装後
- [ ] パフォーマンスレポート作成
- [ ] アンチパターン除去確認
- [ ] 計画のarchive移動
- [ ] mainブランチへのマージ準備

## 成果物

- [ ] 修正済み`.cargo/config.toml`
- [ ] パフォーマンス影響レポート
- [ ] 代替最適化実装（必要な場合）
- [ ] 更新されたドキュメント

## 備考

- 過去のSIMD最適化失敗の歴史を踏まえた修正
- コンパイラの自動ベクトル化は`target-cpu=native`で十分
- パフォーマンスより保守性とクロスプラットフォーム性を優先