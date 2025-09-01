# QuantForge Core + Bindings リアーキテクチャ実装計画

## メタデータ
- **作成日**: 2025-08-30
- **更新日**: 2025-08-30（パフォーマンス最適化完了を反映）
- **言語**: Both (Rust + Python)
- **ステータス**: DRAFT
- **推定規模**: 大規模（完全リアーキテクチャ）
- **推定期間**: 6営業日（既存作業の活用により短縮）
- **影響範囲**: プロジェクト全体

## 背景と目的

### 現状の問題点と既存の改善
1. **構造的課題（一部解決済み）**
   - ✅ `benchmarks/`: Pythonパッケージ化完了（baseline_manager, performance_guard実装済み）
   - ✅ パフォーマンス最適化済み（1M要素でNumPyの1.4倍高速）
   - ✅ ゼロコピー最適化実装（BroadcastIterator、FFIオーバーヘッド40%削減）
   - ❌ `src/`: RustコードとPyO3が依然混在
   - ❌ コア実装とバインディングが密結合のまま
   - ❌ 他言語対応が困難な状態継続

2. **技術的制約（未解決）**
   - コア実装とバインディングが密結合
   - 他言語対応が困難
   - テストの責任範囲が不明確

### 目標
- **Core + Bindings アーキテクチャ**の実現
- 言語非依存のコア実装
- 将来的な多言語対応（Julia, R等）への準備
- 技術的負債ゼロの理想実装

## アーキテクチャ設計

### 目標構造
```
quantforge/
├── Cargo.toml               # [workspace]定義（core, bindings/python）
├── core/                    # 言語非依存のRustコア実装
│   ├── Cargo.toml          # quantforge-coreクレート
│   ├── src/                # 純粋なRust実装（PyO3依存なし）
│   ├── tests/              # Rustユニットテスト
│   └── benches/            # Rust性能測定（criterionベンチマーク）
│
├── bindings/               # 言語バインディング層
│   └── python/            
│       ├── Cargo.toml      # quantforge-pythonクレート（PyO3）
│       ├── pyproject.toml  # Python パッケージ設定
│       ├── src/            # PyO3ラッパー実装
│       ├── tests/
│       │   └── benchmarks/ # FFI層固有のベンチマーク
│       └── quantforge/     # Pythonパッケージ
│           ├── __init__.py
│           ├── py.typed
│           └── *.pyi      # 型スタブ
│
├── tests/                  # Python統合テストスイート
│   ├── unit/              # 単体テスト
│   ├── integration/       # 統合テスト
│   │   └── golden/        # ゴールデンマスターテスト
│   └── performance/       # 統合パフォーマンステスト
│       ├── baseline_manager.py   # ベースライン管理（既存資産移動）
│       └── performance_guard.py  # 回帰検出（既存資産移動）
│
├── benchmark_results/      # ベンチマーク結果（新形式）
│   ├── core/              # Core層の結果
│   │   ├── latest.json
│   │   └── history/
│   ├── bindings/          # Bindings層の結果
│   │   └── python/
│   │       ├── latest.json
│   │       └── history/
│   └── integration/       # 統合層の結果
│       ├── latest.json
│       └── history/
│
├── docs/                   # 統一ドキュメント
└── .github/workflows/      # CI/CDパイプライン（要更新）
```

### 設計原則
1. **完全な分離**: コアとバインディングの明確な境界
2. **ゼロ依存**: コア層はPyO3に依存しない
3. **再利用性**: コア層は任意の言語から利用可能
4. **テスト独立性**: 各層で完結したテスト

## 実装フェーズ

### Phase 0: 準備 [0.5日]
- アーキテクチャ設計の最終確認
- ゴールデンマスターテストの確認（既存の95%カバレッジを活用）
- ワークスペース構成の準備

### Phase 1: Core層構築 [2日]
- PyO3依存の除去
- 純粋Rust実装の抽出
- Core層テストの作成
- 既存最適化（並列化閾値、ループアンローリング）の移植

### Phase 2: Bindings層構築 [2日]
- PyO3ラッパー実装
- Python APIの再構築（既存のゼロコピー最適化を維持）
- エラー変換層の実装
- BroadcastIteratorの統合

### Phase 3: テスト移行 [1日]
- テストの責任分離
- 層別ベンチマーク構造の実装
  - Core層: 純粋アルゴリズム性能（Criterion）
  - Bindings層: FFIオーバーヘッド測定
  - Integration層: エンドツーエンド性能
- 新形式ベンチマーク記録（v2.0.0）への移行
- CI/CDパイプラインの更新

### Phase 4: 検証と完成 [0.5日]
- ゴールデンマスター検証
- パフォーマンス測定（現在の1.4倍性能を維持）
- ドキュメント更新

## 成功基準

### 必須要件
- [ ] 全ゴールデンマスターテスト合格
- [ ] 現在の性能維持（1M要素でNumPyの1.4倍以上）
- [ ] ゼロコピー最適化の維持（FFIオーバーヘッド40%削減維持）
- [ ] Core層のPyO3依存ゼロ
- [ ] 既存APIの互換性維持

### 品質基準
- [ ] テストカバレッジ 95%以上（既存達成済み）
- [ ] 層別パフォーマンス検証
  - Core層: アルゴリズム性能 < 10ns（単一計算）
  - Bindings層: FFIオーバーヘッド < 50ns
  - Integration層: 1M要素処理 > 7M ops/sec
- [ ] 新形式（v2.0.0）でのベンチマーク記録完備
- [ ] ドキュメント完全性 100%

## リスクと対策

| リスク | 影響度 | 発生確率 | 対策 |
|--------|--------|----------|------|
| PyO3分離の複雑性 | 高 | 中 | 段階的な抽出とテスト |
| 既存最適化の退行 | 高 | 中 | performance_guard.pyによる継続的検証 |
| ゼロコピー実装の劣化 | 高 | 低 | BroadcastIterator設計の慎重な移植 |
| API互換性の破壊 | 中 | 低 | ゴールデンマスター検証 |
| 工期遅延 | 低 | 低 | 既存作業活用により短縮済み |

## 成果物

### コード成果物
- `core/`: 完全な言語非依存Rustライブラリ
- `bindings/python/`: PyO3ベースのPythonバインディング
- `tests/golden/`: 拡充されたゴールデンマスター

### ドキュメント成果物
- `docs/architecture/`: アーキテクチャ設計書
- `docs/api/`: 更新されたAPI仕様
- `docs/migration/`: 移行ガイド

## 参考資料
- [Rust API Guidelines](https://rust-lang.github.io/api-guidelines/)
- [PyO3 Best Practices](https://pyo3.rs/main/doc/)
- [Core + Bindings パターン例](https://github.com/polars-rs/polars)

## 備考
- 既存ユーザーなしの前提で破壊的変更を推奨
- 技術的負債ゼロの理想実装を追求
- 将来の多言語対応を見据えた設計