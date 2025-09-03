# 並列化閾値最適化計画

- **作成日**: 2025-09-02
- **ステータス**: DRAFT
- **タイプ**: Rust実装（パフォーマンス最適化）
- **影響範囲**: core/src/constants.rs のみ
- **重要度**: HIGH（10-15%のパフォーマンス改善期待）

## 1. 背景と問題定義

### 1.1 発見された問題

ベンチマーク結果の分析により、playground/arrow_prototypeが現在のmainブランチより12%高速であることが判明。主要因は並列化閾値の違い：

```
現在の実装（main/arro3）:
- PARALLEL_THRESHOLD_SMALL = 10,000（core/src/constants.rs）
- 10,000要素から並列化開始

prototype実装:
- PARALLEL_THRESHOLD = 50,000（core/src/arrow_native.rs）
- 50,000要素から並列化開始
```

### 1.2 パフォーマンス測定結果

| データサイズ | main (10,000閾値) | prototype (50,000閾値) | 差 |
|------------|-------------------|------------------------|-----|
| 10,000要素 | 192μs | 140μs | 27%遅い |
| 100,000要素 | 753μs | 617μs | 18%遅い |
| 1,000,000要素 | 6.80ms | 5.50ms | 24%遅い |

### 1.3 原因分析

10,000要素での並列化は以下の理由で逆効果：
- スレッド生成・同期のオーバーヘッド > 並列化の利益
- Rayonのワークスティーリングの初期化コスト
- キャッシュの非効率な利用（スレッド間でのfalse sharing）

## 2. 解決方針

### 2.1 最小限の変更で効果測定

**Phase 1（今回実施）**：
- constants.rsの1行のみ変更
- 他の最適化は一切行わない
- 純粋な閾値変更の効果を測定

**Phase 2（効果確認後）**：
- arrow_native.rsのハードコード削除
- Float64Builder最適化
- マイクロバッチ処理の追加

### 2.2 変更内容

```rust
// core/src/constants.rs（300行目）
// 変更前
pub const PARALLEL_THRESHOLD_SMALL: usize = 10_000;

// 変更後
pub const PARALLEL_THRESHOLD_SMALL: usize = 50_000;
```

### 2.3 根拠

1. **実測データ**: prototypeで50,000が最適と実証済み
2. **理論的根拠**: 並列化オーバーヘッドは約100μs、50,000要素の処理で初めて利益が上回る
3. **環境変数での調整可能**: QUANTFORGE_PARALLEL_THRESHOLDで個別環境に最適化可能

## 3. 実装計画

### 3.1 変更前の準備

```bash
# Rustベンチマークの現在の結果を記録
cargo bench --bench batch_processing -- --save-baseline before

# Pythonベンチマークの現在の結果を記録
uv run pytest tests/performance/ -m benchmark
# 結果は以下に保存される:
# - benchmark_results/latest.json (最新結果)
# - benchmark_results/history.jsonl (履歴に追記)

# 変更前の結果をバックアップ
cp benchmark_results/latest.json benchmark_results/before_threshold_change.json
```

### 3.2 実装（1行のみ）

```rust
// core/src/constants.rs の300行目を変更
pub const PARALLEL_THRESHOLD_SMALL: usize = 50_000;  // 実測に基づく最適値
```

### 3.3 コメントの更新

```rust
/// 並列化閾値: 小規模
///
/// この要素数以下ではシーケンシャル処理が高速。
/// 2025-09-02: 実測に基づき50,000に最適化。
/// - 10,000要素: 並列化オーバーヘッド > 利益
/// - 50,000要素: 並列化が有効になる分岐点
/// playground/arrow_prototypeの実測値に基づく。
pub const PARALLEL_THRESHOLD_SMALL: usize = 50_000;
```

## 4. 命名定義セクション

### 4.1 使用する既存命名

```yaml
existing_names:
  - name: "PARALLEL_THRESHOLD_SMALL"
    meaning: "小規模データの並列化閾値"
    source: "core/src/constants.rs"
  - name: "get_parallel_threshold"
    meaning: "並列化閾値を取得する関数"
    source: "core/src/constants.rs"
```

### 4.2 新規提案命名

なし（既存の命名を維持）

### 4.3 命名の一貫性チェックリスト

- [x] 既存モデルとの整合性確認
- [x] 定数命名規則（UPPER_SNAKE_CASE）遵守
- [x] 説明的な名前を維持
- [x] 環境変数名との一貫性（QUANTFORGE_PARALLEL_THRESHOLD）

## 5. テストと検証

### 5.1 ユニットテスト

```bash
# 既存テストがパスすることを確認
cargo test --lib --release
```

### 5.2 パフォーマンステスト

```bash
# Rustベンチマーク実行
cargo bench --bench batch_processing -- --save-baseline after

# Rust結果の比較
cargo bench --bench batch_processing -- --baseline before

# Pythonベンチマーク実行
uv run pytest tests/performance/ -m benchmark

# 変更後の結果を保存
cp benchmark_results/latest.json benchmark_results/after_threshold_change.json

# Python結果の比較（手動またはスクリプトで）
python -c "
import json
with open('benchmark_results/before_threshold_change.json') as f:
    before = json.load(f)
with open('benchmark_results/after_threshold_change.json') as f:
    after = json.load(f)
    
for size in [100, 1000, 10000, 100000, 1000000]:
    if str(size) in before and str(size) in after:
        b = before[str(size)]['quantforge']['mean']
        a = after[str(size)]['quantforge']['mean']
        improvement = (b - a) / b * 100
        print(f'{size:8d}: {b*1000:8.2f}ms → {a*1000:8.2f}ms ({improvement:+.1f}%)')
"
```

### 5.3 期待される結果

- 10,000要素: 10-15%高速化（並列化オーバーヘッド削除）
- 100,000要素: 5-10%高速化（適切な並列化）
- 1,000,000要素: 変化なし（両方とも並列化）

## 6. リスクと対策

### 6.1 リスク

1. **一部環境での性能劣化**
   - CPUコア数が多い環境では10,000が最適な可能性
   - 対策: 環境変数での調整機能を維持

2. **メモリ使用量の増加**
   - 大きなシーケンシャル処理でメモリ局所性が低下
   - 対策: 50,000は十分小さく、L3キャッシュに収まる

### 6.2 ロールバック計画

問題が発生した場合：
```bash
git revert HEAD
# または環境変数で即座に調整
export QUANTFORGE_PARALLEL_THRESHOLD=10000
```

## 7. 次のステップ

Phase 1の効果確認後：

1. **arrow_native.rsの統一**
   - ハードコードされた50,000を削除
   - get_parallel_threshold()を使用

2. **Float64Builder最適化**
   - 小規模データでVec使用
   - 大規模データでFloat64Builder維持

3. **マイクロバッチ処理**
   - 200要素以下で専用最適化

## 8. 完了条件

- [ ] constants.rsの1行変更完了
- [ ] cargo test --lib --releaseがパス
- [ ] Rustベンチマークで10%以上の改善確認
- [ ] Pythonベンチマークで改善確認（特に10,000要素）
- [ ] benchmark_results/に変更前後の結果を保存
- [ ] コミットメッセージ: "perf: optimize parallel threshold to 50k based on benchmarks"

## 9. 参考資料

- ベンチマーク結果: `/home/driller/work/quantforge-experiments/results/3way_comparison_results.json`
- 分析レポート: `plans/2025-09-02-performance-analysis-prototype-superiority.md`
- 現在の実装: `core/src/constants.rs:300`
- prototypeの実装: `core/src/arrow_native.rs:11`（参考）