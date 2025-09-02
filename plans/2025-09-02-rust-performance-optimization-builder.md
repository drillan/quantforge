# Performance Optimization: Float64Builder Migration Plan

## 問題分析

### 現在のボトルネック
`core/src/compute/black_scholes.rs`での実装：

```rust
// 現在の実装（メモリコピーが発生）
let mut result = Vec::with_capacity(len);  // アロケーション1
result.push(call_price);                   // 値の追加
Ok(Arc::new(Float64Array::from(result)))   // コピー発生
```

### arro3-coreとの差
arro3-coreは`Float64Builder`を使用：
- メモリコピー：1回のみ
- アロケーション：Builder内部で最適化

### パフォーマンス影響
- 10,000要素：3-15%の性能劣化
- メモリ使用量：約2倍（Vec + Array）
- FFIオーバーヘッド：20μs追加

## 改善案

### 1. Float64Builder使用（推奨）

```rust
// 改善案
let mut builder = Float64Builder::with_capacity(len);
builder.append_value(call_price);
Ok(Arc::new(builder.finish()))
```

**メリット**：
- メモリコピー削減（2回→1回）
- 安全（unsafeなし）
- コード変更最小限

**期待効果**：
- パフォーマンス：10-20%改善
- メモリ使用量：約50%削減

### 2. 実装対象ファイル

```
core/src/compute/
├── black_scholes.rs  # call_price, put_price, greeks
├── black76.rs         # call_price, put_price, greeks
└── merton.rs          # call_price, put_price
```

### 3. テスト方針

1. **互換性テスト**：
   - 結果が同一であることを確認
   - すべての既存テストがパス

2. **パフォーマンステスト**：
   ```bash
   pytest tests/performance/ -m benchmark
   ```
   - v0.0.7との比較
   - 10-20%改善を確認

3. **メモリプロファイリング**：
   ```python
   tracemalloc.start()
   # 実行
   current, peak = tracemalloc.get_traced_memory()
   ```

## 実装手順

### Phase 1: black_scholes.rs
1. Float64Builder導入
2. 並列処理対応（append_slice使用）
3. テスト実行

### Phase 2: 他モジュール
1. black76.rs
2. merton.rs
3. american.rs（該当箇所があれば）

### Phase 3: バージョン更新
```toml
[workspace.package]
version = "0.0.8"  # パフォーマンス改善
```

## リスク評価

| リスク | 影響度 | 対策 |
|--------|--------|------|
| Builder APIの変更 | 低 | Arrow v56.0で安定 |
| 並列処理の複雑化 | 中 | append_sliceで対応 |
| テスト失敗 | 低 | 段階的移行 |

## 成功指標

- [ ] すべてのテストがパス
- [ ] 10,000要素で10%以上高速化
- [ ] メモリ使用量30%以上削減
- [ ] arro3-coreとの性能差5%以内

## タイムライン

- 実装：2時間
- テスト：1時間
- ベンチマーク：30分
- 合計：3.5時間

## 結論

Vec → Float64Array変換によるメモリコピーが主要なボトルネック。Float64Builder使用により、安全かつ効率的に10-20%の性能改善が期待できる。