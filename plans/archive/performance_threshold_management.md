# パフォーマンス閾値管理システム

## 概要

QuantForgeのパフォーマンステストにおける閾値管理を、固定値から動的なベースライン管理へ移行するシステム。

## 問題と解決策

### 従来の問題
- **固定閾値の限界**: 100ms閾値では、50ms→80ms（60%劣化）を検出できない
- **環境依存**: 開発環境とCI環境で性能が異なる
- **改善の無視**: 性能が10倍改善しても、古い閾値のまま

### 解決策：ハイブリッドアプローチ
1. **ベースライン管理**: 実測値に基づく動的閾値
2. **フォールバック**: ベースライン不在時は固定閾値
3. **段階的移行**: 環境変数で制御可能

## システム構成

### コンポーネント

```
benchmarks/
├── baseline_manager.py       # ベースライン収集・管理
├── performance_guard.py      # CI/CD用の退行検出
└── results/
    ├── baseline.json         # ベースラインデータ
    └── latest.json          # 最新測定結果

tests/performance/
├── adaptive_thresholds.py   # 適応型閾値システム
├── test_benchmarks.py       # 既存テスト（固定閾値）
├── test_benchmarks_adaptive.py  # 新テスト（適応型）
└── test_benchmarks_integrated.py # 統合例
```

## 使用方法

### 1. ベースライン作成

```bash
# 5回測定して20%バッファでベースライン作成
uv run python benchmarks/baseline_manager.py --update --runs 5 --buffer 1.2
```

出力例：
```
=== ベースライン統計 ===
single:
  quantforge:
    平均: 1.397002e-06 (±0.000000e+00)
    閾値: 1.676402e-06  # 平均の120%

batch_1m:
  quantforge:
    平均: 1.057806e-02 (±3.668246e-04)
    閾値: 1.269367e-02  # 平均の120%
```

### 2. 性能チェック

```bash
# 現在の性能をベースラインと比較
uv run python benchmarks/performance_guard.py
```

結果：
```
✅ 単一計算(QuantForge): 3.0%改善
✅ 100万件バッチ(QuantForge): 許容範囲内（5.2%）
```

### 3. テストでの使用

#### 環境変数制御
```bash
# 適応型閾値を使用
USE_BASELINE_THRESHOLDS=true pytest tests/performance/

# 固定閾値を使用（デフォルト）
USE_BASELINE_THRESHOLDS=false pytest tests/performance/

# 厳格モード（より厳しい閾値）
STRICT_PERFORMANCE_TESTS=true pytest tests/performance/
```

## 閾値の決定ロジック

```python
if ベースライン存在 and USE_BASELINE_THRESHOLDS:
    if STRICT_MODE:
        閾値 = min(ベースライン×1.2, fallback閾値)
    else:
        閾値 = min(ベースライン×1.2, 絶対上限)
else:
    if STRICT_MODE:
        閾値 = fallback閾値（厳しい）
    else:
        閾値 = 絶対上限（緩い）
```

### 具体例

| テスト | ベースライン平均 | 動的閾値（+20%） | Fallback | 絶対上限 |
|--------|-----------------|-----------------|----------|----------|
| 単一計算 | 1.40μs | 1.68μs | 2μs | 10μs |
| 100万件 | 10.58ms | 12.70ms | 20ms | 100ms |
| 10万件 | 1.13ms | 1.36ms | 3ms | 20ms |

## CI/CD統合

### GitHub Actions例

```yaml
name: Performance Check

on: [push, pull_request]

jobs:
  performance:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.12'
      
      - name: Install dependencies
        run: |
          pip install uv
          uv sync
      
      - name: Download baseline
        uses: actions/download-artifact@v3
        with:
          name: performance-baseline
          path: benchmarks/results/
        continue-on-error: true
      
      - name: Run benchmarks
        run: |
          uv run python -m benchmarks.runners.comparison
      
      - name: Check performance
        run: |
          uv run python benchmarks/performance_guard.py
        env:
          USE_BASELINE_THRESHOLDS: 'true'
      
      - name: Update baseline (main branch only)
        if: github.ref == 'refs/heads/main' && success()
        run: |
          uv run python benchmarks/baseline_manager.py --update
      
      - name: Upload baseline
        if: github.ref == 'refs/heads/main'
        uses: actions/upload-artifact@v3
        with:
          name: performance-baseline
          path: benchmarks/results/baseline.json
```

## 移行計画

### Phase 1: 並行運用（現在）
- 既存テスト（test_benchmarks.py）は固定閾値を維持
- 新テスト（test_benchmarks_adaptive.py）で適応型を検証
- CI/CDでは警告のみ

### Phase 2: 段階的移行
- 環境変数で適応型を有効化
- CIで適応型をデフォルトに
- 固定閾値はフォールバックとして維持

### Phase 3: 完全移行
- すべてのテストで適応型を使用
- 固定閾値は絶対上限としてのみ使用
- ベースラインの定期更新を自動化

## 利点

1. **退行検出の精度向上**
   - 50ms→80ms（60%劣化）を確実に検出
   - 誤検知の削減（20%バッファ）

2. **継続的改善の追跡**
   - 性能改善を自動的に新基準に
   - 履歴データの蓄積

3. **環境適応**
   - CI環境用の独立したベースライン
   - 開発環境での柔軟な閾値

## 注意事項

- ベースライン更新は慎重に（意図的な性能劣化を防ぐ）
- 異常値の除外（統計的処理済み）
- 定期的なベースラインの見直し（月1回推奨）

## コマンドリファレンス

```bash
# ベースライン管理
uv run python benchmarks/baseline_manager.py --update  # 更新
uv run python benchmarks/baseline_manager.py --check   # チェック

# パフォーマンスガード
uv run python benchmarks/performance_guard.py          # 通常チェック
uv run python benchmarks/performance_guard.py --strict # 厳格モード

# テスト実行
USE_BASELINE_THRESHOLDS=true pytest tests/performance/ # 適応型
STRICT_PERFORMANCE_TESTS=true pytest tests/performance/ # 厳格モード
```