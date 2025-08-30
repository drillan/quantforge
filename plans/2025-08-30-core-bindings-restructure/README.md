# QuantForge Core + Bindings リアーキテクチャ実装計画

## メタデータ
- **作成日**: 2025-08-30
- **言語**: Both (Rust + Python)
- **ステータス**: DRAFT
- **推定規模**: 大規模（完全リアーキテクチャ）
- **推定期間**: 7営業日
- **影響範囲**: プロジェクト全体

## 背景と目的

### 現状の問題点
1. **場当たり的な構造**
   - `benches/`: Rust単体ベンチマーク（Cargo慣習）
   - `benchmarks/`: Python APIベンチマーク（独自命名）
   - `src/`: RustコードとPyO3が混在
   - `python/`: 最小限のPythonラッパー

2. **技術的制約**
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
│       └── quantforge/     # Pythonパッケージ
│           ├── __init__.py
│           ├── py.typed
│           └── *.pyi      # 型スタブ
│
├── tests/                  # Python統合テストスイート
│   ├── unit/              # 単体テスト
│   ├── integration/       # 統合テスト
│   │   └── golden/        # ゴールデンマスターテスト
│   └── performance/       # パフォーマンステスト
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

### Phase 0: 準備 [1日]
- 要件定義とアーキテクチャ設計
- ゴールデンマスターテストの拡充
- 現状の完全な動作記録

### Phase 1: Core層構築 [2日]
- PyO3依存の除去
- 純粋Rust実装の抽出
- Core層テストの作成

### Phase 2: Bindings層構築 [2日]
- PyO3ラッパー実装
- Python APIの再構築
- エラー変換層の実装

### Phase 3: テスト移行 [1日]
- テストの責任分離
- ベンチマークの統合
- 統合テストの整備

### Phase 4: 検証と完成 [1日]
- ゴールデンマスター検証
- パフォーマンス測定
- ドキュメント更新

## 成功基準

### 必須要件
- [ ] 全ゴールデンマスターテスト合格
- [ ] パフォーマンス劣化なし（±5%以内）
- [ ] Core層のPyO3依存ゼロ
- [ ] 既存APIの互換性維持

### 品質基準
- [ ] テストカバレッジ 90%以上
- [ ] ベンチマーク全項目でベースライン達成
- [ ] ドキュメント完全性 100%

## リスクと対策

| リスク | 影響度 | 発生確率 | 対策 |
|--------|--------|----------|------|
| PyO3分離の複雑性 | 高 | 中 | 段階的な抽出とテスト |
| パフォーマンス劣化 | 高 | 低 | 継続的なベンチマーク |
| API互換性の破壊 | 中 | 低 | ゴールデンマスター検証 |
| 工期遅延 | 中 | 中 | バッファ日程の確保 |

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