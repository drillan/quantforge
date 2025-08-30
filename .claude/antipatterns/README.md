# QuantForge アンチパターン集

過去の失敗から学んだ「やってはいけないこと」のカタログ。
AIアシスタントは必ずこれを参照し、同じ間違いを繰り返さないこと。

## ⛔ 禁止パターン一覧

| パターン | ファイル | 失敗日 | 教訓 |
|---------|----------|--------|------|
| SIMD最適化の提案 | [simd-optimization-trap.md](./simd-optimization-trap.md) | 2025-08-27 | マルチプラットフォーム地獄、Rustエコシステム未成熟 |
| 段階的実装 | [stage-implementation.md](./stage-implementation.md) | 複数回 | C004違反、技術的負債の蓄積 |
| 早すぎる最適化 | [premature-optimization.md](./premature-optimization.md) | 継続中 | 測定前の推測は時間の無駄 |

## 🚨 AIへの警告

### パフォーマンス問題に遭遇したら

#### ❌ やってはいけないこと
1. **SIMD最適化を提案しない**
   - 過去に210行のコードを削除済み
   - 「AVX2で4倍高速」などと言わない
   
2. **段階的改善を提案しない**
   - 「とりあえず動くものを...」禁止
   - 「後で最適化...」禁止

3. **推測で最適化しない**
   - プロファイリング前の最適化提案禁止
   - 「おそらく〜が遅い」という推測禁止

#### ✅ 必ずやること
1. **プロファイリングを最初に実施**
   ```bash
   cargo install flamegraph
   cargo flamegraph --bench benchmarks
   ```

2. **並列化閾値の調整を検討**
   - `PARALLEL_THRESHOLD_SMALL`: 現在1,000 → 実測に基づき調整
   - 現在の問題: 10,000件でNumPyより遅い

3. **キャッシュ最適化を検討**
   - データレイアウトの改善
   - チャンクサイズの調整

4. **コンパイラヒントの活用**
   ```rust
   #[inline(always)]
   #[cold]  // まれな分岐
   ```

## 📚 各アンチパターンの詳細

### 1. SIMD最適化の罠
**症状**: 「パフォーマンスが遅い」→「SIMD使えば速くなる」

**現実**: 
- x86_64、ARM、Apple M1/M2、WebAssemblyで全て異なる実装が必要
- Rustの`std::simd`は5年以上nightly
- 結果: 210行の未使用コードを生成して削除

**詳細**: [simd-optimization-trap.md](./simd-optimization-trap.md)

### 2. 段階的実装の誘惑
**症状**: 「複雑だから段階的に...」

**現実**:
- Critical Rule C004違反（理想実装ファースト）
- Critical Rule C014違反（妥協実装絶対禁止）
- 技術的負債が雪だるま式に増加

**詳細**: [stage-implementation.md](./stage-implementation.md)

### 3. 早すぎる最適化
**症状**: 「ここが遅そうだから最適化しよう」

**現実**:
- 実際のボトルネックは別の場所
- 時間の無駄 + コード複雑化
- Donald Knuth: "早すぎる最適化は諸悪の根源"

**詳細**: [premature-optimization.md](./premature-optimization.md)

## 🔄 更新履歴

| 日付 | 追加内容 | 理由 |
|------|----------|------|
| 2025-08-30 | 初版作成 | SIMD最適化の繰り返し提案を防ぐため |

## 📌 必読資料

- Critical Rules: @.claude/critical-rules.xml
- 開発原則: @.claude/development-principles.md
- 過去の失敗: plans/archive/2025-08-27-rust-remove-simd-implementation.md