# 変更履歴

```{include} ../CHANGELOG.md
```

## 日本語での補足説明

### バージョン 0.0.2 (2025-08-27)
- プロジェクトメタデータの充実（PyPI/TestPyPIでの表示改善）
- CI/CDでのインポートエラー修正
- バージョン管理の一元化（Cargo.tomlを単一の真実の情報源として使用）

### バージョン 0.0.1 (2025-08-27)
- TestPyPIへの初回リリース
- 主要な価格モデルの実装：
  - Black-Scholesオプション価格モデル
  - Black76先物オプション価格モデル
  - アメリカンオプション（Bjerksund-Stensland 2002近似）
  - Mertonモデル（配当付き資産）
- グリークス計算（デルタ、ガンマ、シータ、ベガ、ロー）
- Newton-Raphson法によるインプライドボラティリティ計算
- NumPy配列のバッチ処理サポート
- マルチプラットフォーム対応（Linux、Windows、macOS）

## 技術的詳細

- **パフォーマンス**: Rust + PyO3実装により、純Pythonと比較して500-1000倍の高速化を実現
- **メモリ効率**: NumPy配列処理のゼロコピー設計
- **並列化**: Rayonによるバッチ処理の自動並列化
- **精度**: エラー率 < 1e-15の高精度計算

## リリースサイクル

- **Alpha**: 開発中、不安定
- **Beta**: 機能完成、テスト中  
- **RC**: リリース候補
- **Stable**: 本番環境対応

---

**フィードバック**: [GitHub Issues](https://github.com/drillan/quantforge/issues)  
**貢献**: [Contributing Guide](development/contributing.md)