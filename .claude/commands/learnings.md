新たな知見が得られたら、次のファイルを更新してください

- @.claude/context.md: 背景・制約・技術選定理由
- @.claude/project-knowledge.md: 実装パターン・設計決定
- @.claude/project-improvements.md: 試行錯誤・改善記録
- @.claude/common-patterns.md: 定型実装・コマンドパターン

## 2025-09-02 ベンチマーク記録システム実装

### 実装内容
1. **バージョン自動化**: lib.rsでenv!("CARGO_PKG_VERSION")使用
2. **パス堅牢化**: Path(__file__).parent.parent.parent使用
3. **Arrow Nativeベンチマーク**: PyArrowで直接ベンチマーク追加

### 成果
- バージョン0.0.6で正しく記録
- Arrow Native性能測定実現（10,000要素で269.8μs）
- 絶対パスによる安定記録

### 注意点
- Black76, Merton, Americanモデルは未実装のためエラー
- mypy型チェックは一部エラー残存（機能には影響なし）