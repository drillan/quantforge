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

## 2025-09-02 Arrow Native Broadcasting実装完了

### 実装内容
1. **Broadcasting機能追加**: 
   - `get_scalar_or_array_value`関数でスカラー値の自動拡張実現
   - `validate_broadcast_compatibility`で互換性チェック
   - Black-Scholes, Black76両モデルで完全対応

2. **Greeks計算実装**:
   - Delta, Gamma, Vega, Theta, Rho全て実装
   - Broadcasting対応でスカラー入力も可能
   - Dict[str, Arrow array]形式で返却

3. **Python バインディング拡張**:
   - `arrow_greeks`, `arrow76_greeks`関数追加
   - `arrow76_call_price`, `arrow76_put_price`実装
   - pyo3-arrowによるゼロコピー維持

### パフォーマンス結果
- 10,000要素: 33.8M ops/sec（call price）
- Greeks計算: 価格計算の約4倍のコスト
- Broadcasting vs Full array: ほぼ同等の性能でメモリ効率向上
- 100,000要素でも122M ops/secの高速処理

### 技術的学び
1. **Arrow計算の注意点**: Arrow組み込みのbinary/unary演算はBroadcasting非対応
2. **手動実装の優位性**: ループベースの実装で完全な制御とBroadcasting実現
3. **PyDict作成**: `PyDict::new(py)`を使用（`new_bound`は不要）

### 改善ポイント
- 並列化閾値（10,000）は既に最適化済み
- ゼロコピーによるメモリ効率の維持
- Greeks一括計算で関数呼び出しオーバーヘッド削減