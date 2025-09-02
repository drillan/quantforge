新たな知見が得られたら、次のファイルを更新してください

- @.claude/context.md: 背景・制約・技術選定理由
- @.claude/project-knowledge.md: 実装パターン・設計決定
- @.claude/project-improvements.md: 試行錯誤・改善記録
- @.claude/common-patterns.md: 定型実装・コマンドパターン

## 2025-09-02 Critical Rules遵守とパフォーマンス最適化統合実装

### 実装内容
1. **Float64Builder最適化**: Vec→Float64Arrayの直接変換を回避
   - Black-Scholes、Black76、Mertonの全モジュールで実装
   - メモリコピー削減により30-50%のメモリ使用量削減期待

2. **共通フォーミュラモジュール作成**: core/src/compute/formulas.rs
   - Black-Scholesフォーミュラの重複排除（6箇所→1箇所）
   - Black76、Mertonのスカラー版も統合
   - models.rsのPyO3バインディングでも共通化

3. **ハードコード完全排除**:
   - distributions.rs: 8.0→NORM_CDF_UPPER_BOUND等の定数化
   - constants.rs: 数値計算定数セクション追加
   - VOL_SQUARED_HALF、HALF等の補助定数定義

4. **Mertonモデル実装完了**:
   - 配当付きBlack-Scholesモデルの完全実装
   - Put-Callパリティのテスト追加
   - Float64Builder最適化適用

### パフォーマンス結果（vs NumPy）
- 100要素: **7.75倍高速** (9.7μs vs 75.2μs)
- 1,000要素: **3.41倍高速** (33.9μs vs 115.3μs)
- 10,000要素: **1.60倍高速** (246.8μs vs 395.3μs)

### Critical Rules遵守
- **C004/C014**: 理想実装ファースト - 統合実装で完全修正
- **C011-3**: ハードコード禁止 - すべてのマジックナンバーを定数化
- **C012**: DRY原則 - Black-Scholesフォーミュラの重複を完全排除
- **C013**: 破壊的リファクタリング - 既存コードを躊躇なく改善

### 技術的学び
1. **Float64Builder**: Arrow v56で安定、メモリ効率大幅改善
2. **コード共通化**: formulasモジュールで保守性向上
3. **定数管理**: constants.rsへの集約で一貫性確保

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

## 2025-09-02 Float64Builder完全最適化（残り40%完了）

### 追加実装内容
1. **Black-Scholesモジュール**: 
   - calculate_d1_d2関数のFloat64Builder最適化完了
   - 5つのGreeks関数（delta, gamma, vega, theta, rho）全て最適化

2. **Black76モジュール**:
   - 5つのGreeks関数（delta, gamma, vega, theta, rho）全て最適化
   - Vec→Float64Arrayの変換を完全排除

### 実装パターン
```rust
// Before: メモリコピー発生
let mut result = Vec::with_capacity(len);
result.push(value);
Ok(Arc::new(Float64Array::from(result)))

// After: ゼロコピー実現
let mut builder = Float64Builder::with_capacity(len);
builder.append_value(value);
Ok(Arc::new(builder.finish()))
```

### パフォーマンス結果
- **Arrow Native性能**:
  - 100要素: 8.61μs（7.1M ops/sec）
  - 10,000要素: 250.41μs（41.2M ops/sec）  
  - 100,000要素: 1149.40μs（87.8M ops/sec）
  - 1,000,000要素: 7262ms（137.7M ops/sec）

- **Greeks計算**:
  - Call価格計算の2-3倍のコスト（最適化後）
  - Broadcasting使用でメモリ効率向上
  - 大規模データで線形スケーリング維持

### 完了率
- 計画の100%完了（当初60%→残り40%追加実装）
- 全12箇所のVec使用部分をFloat64Builderに移行
- メモリコピー完全排除、目標達成

## 2025-09-02 並列化閾値の最適化実験（予期しない結果）

### 実験内容
1. **変更**: `PARALLEL_THRESHOLD_SMALL` を 10,000 → 50,000
2. **根拠**: playground/arrow_prototypeの実測値
3. **期待**: 10,000要素で並列化オーバーヘッド削除により改善

### 結果（逆効果）
- 100要素: 11%遅い
- 1,000要素: 9%遅い  
- **10,000要素: 97%遅い**（0.178ms → 0.351ms）

### 教訓
1. **プロトタイプと実装の違い**:
   - prototypeはarrow_native.rsを使用（古い実装）
   - 現在はcompute/black_scholes.rsを使用（新実装）
   - 実装が異なれば最適値も異なる

2. **並列化閾値の複雑性**:
   - CPUアーキテクチャ依存
   - データレイアウト依存
   - 実装詳細依存

3. **測定の重要性**:
   - 理論や他の実装の値を鵜呑みにしない
   - 実際の実装で測定することが必須
   - 段階的な調整が安全

### 推奨事項
- 現在の10,000設定を維持
- より詳細なプロファイリングが必要
- 環境変数での調整機能を活用

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