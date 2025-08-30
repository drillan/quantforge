# パフォーマンス閾値システムの完全置換計画

## ステータス
- **作成日**: 2025-08-30
- **ステータス**: COMPLETED
- **完了日**: 2025-08-30
- **タイプ**: 破壊的変更（推奨）

## 原則の確認

このプロジェクトは：
- **既存ユーザー: ゼロ** → 後方互換性は不要
- **技術的負債: ゼロ** → 理想実装のみ
- **段階的実装: 禁止** → 即座に完全置換
- **破壊的変更: 推奨** → Break Everything Better

## 問題

現在の固定閾値システム：
```python
# 問題のあるコード
assert benchmark.stats["mean"] < 10e-6  # ハードコード違反
assert benchmark.stats["mean"] < 0.10   # 89.5msの劣化まで検出不可
```

実測値: 10.58ms
固定閾値: 100ms
**検出不可能な劣化: 89.42ms（約9倍）**

## 解決策：完全置換

### ❌ 削除するもの（即座に）

1. `tests/performance/test_benchmarks.py` の固定閾値
2. `tests/performance/test_benchmarks_adaptive.py` （段階的移行用）
3. `tests/performance/test_benchmarks_integrated.py` （互換性レイヤー）
4. 環境変数制御（USE_BASELINE_THRESHOLDS等）

### ✅ 唯一の実装

```python
# tests/performance/test_benchmarks.py を完全書き換え

class TestPerformanceBenchmarks:
    """パフォーマンステスト（ベースライン駆動）."""
    
    def test_single_calculation_performance(self, benchmark):
        # ... 測定 ...
        
        # 理想実装：ベースラインベース
        baseline = load_baseline_or_fail()  # ベースライン必須
        threshold = baseline["single"]["quantforge"]["mean"] * 1.2
        
        assert measured < threshold, f"性能劣化: {measured/baseline:.1%}"
```

## 実装手順（即座に実行）

1. **ベースライン作成を必須化**
   ```bash
   # CI/CDの前提条件
   if [ ! -f benchmarks/results/baseline.json ]; then
       echo "ERROR: ベースラインが存在しません"
       exit 1
   fi
   ```

2. **test_benchmarks.py を完全置換**
   - 固定閾値を全削除
   - ベースライン駆動に変更
   - フォールバック無し（理想実装のみ）

3. **不要なファイルを削除**
   - adaptive版、integrated版は技術的負債
   - 環境変数制御も削除

## 命名定義

既存命名を使用：
- `baseline`: ベースラインデータ
- `threshold`: 閾値（baseline × buffer_factor）
- `buffer_factor`: 1.2（20%マージン）

## 成功基準

- [ ] 固定閾値が完全に削除される
- [ ] ベースライン無しではテスト実行不可
- [ ] 20%の性能劣化を確実に検出
- [ ] 段階的移行コードが存在しない

## 禁止事項

- 「後方互換性のため」という理由での旧コード保持
- 「段階的に」という実装
- 環境変数での切り替え
- フォールバック処理

## 結論

**破壊的変更を恐れず、理想実装のみを追求する。**