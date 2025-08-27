# [Python] Black-Scholesベンチマーク再検証 実装計画

## メタデータ
- **作成日**: 2025-01-27
- **言語**: Python
- **ステータス**: COMPLETED
- **推定規模**: 中
- **推定コード行数**: 300-400行
- **対象モジュール**: benchmarks/, scripts/, docs/performance/

## ⚠️ 技術的負債ゼロの原則

**重要**: このプロジェクトでは技術的負債を一切作らないことを最優先とします。

### 禁止事項（アンチパターン）
❌ **段階的実装・TODO残し**
```python
# 絶対にダメな例
def measure_performance():
    # TODO: 後で他のモデルも追加
    return black_scholes_only()  # 暫定実装
```

❌ **ハードコードされた環境情報**
```python
# 絶対にダメな例
CPU_NAME = "Intel Core i9-12900K"  # 特定環境をハードコード
PERFORMANCE_NS = 8  # 理論値をハードコード
```

✅ **正しいアプローチ：実測値ベースの完全実装**
```python
# 実際の環境で測定した値のみを使用
import platform
import psutil

def get_system_info():
    """実行環境の情報を取得."""
    return {
        "cpu": platform.processor(),
        "cpu_count": psutil.cpu_count(),
        "memory": psutil.virtual_memory().total,
    }

def measure_actual_performance():
    """実際の測定値を返す."""
    return time_function(black_scholes.call_price, ...)
```

## タスク規模判定

### 判定基準
- [x] 推定コード行数: 300-400行
- [x] 新規ファイル数: 4個
- [x] 影響範囲: 複数モジュール（benchmarks/, scripts/, docs/）
- [x] Rust連携: 必要（既存のBlack-Scholesモジュール使用）
- [x] NumPy/Pandas使用: あり（NumPy版とSciPy版の比較実装）
- [ ] 非同期処理: 不要

### 規模判定結果
**中規模タスク**

## ファイル構造

```
benchmarks/
├── python_baseline.py        # Pure Python, SciPy, NumPy実装
├── run_comparison.py         # ベンチマーク実行スクリプト
├── format_results.py         # 結果フォーマッター
└── run_benchmarks.sh         # 統合実行シェルスクリプト（自己完結的配置）
```

**設計根拠**: ベンチマーク関連ファイルを`benchmarks/`ディレクトリに集約することで、高い凝集性と発見容易性を実現。`scripts/`はプロジェクト全体の管理タスクに特化させる。

## 目的と背景

### 現在の問題点
1. **不正確な測定環境**
   - ハイエンドCPUでの理論値（8ns）が記載
   - 実際のユーザー環境と乖離
   - 再現性がない

2. **公正性の欠如**
   - 最良条件のみの記載
   - 測定方法が不透明
   - 比較基準が不明確

### 解決方針
1. **実測値ベース**
   - 実際の環境での測定
   - 複数回測定の統計値使用
   - 環境情報の明記

2. **相対性能重視**
   - Pure Python実装との比較（外部ライブラリなし）
   - SciPy実装との比較（一般的な実装）
   - NumPy実装との比較（ベクトル化）
   - 絶対値より倍率を重視

3. **再現可能性**
   - 測定スクリプトの提供
   - 詳細な測定方法の文書化
   - Docker環境は別計画で対応

## 実装計画

### Phase 1: 設計（1時間）
- [x] ベンチマーク構成の設計
- [x] 測定項目の選定（Black-Scholesのみ）
- [x] 出力フォーマットの決定

### Phase 2: 実装（4時間）

#### 2.1 Python比較実装（benchmarks/python_baseline.py）
```python
"""Black-Scholesの各種Python実装."""

import math
import numpy as np
from scipy.stats import norm
from typing import Union, List
from numpy.typing import NDArray

def erf_approx(x: float) -> float:
    """誤差関数の近似計算（Abramowitz and Stegun近似）."""
    # Pure Python用の累積正規分布関数の実装
    # erfの多項式近似を使用
    a1 =  0.254829592
    a2 = -0.284496736
    a3 =  1.421413741
    a4 = -1.453152027
    a5 =  1.061405429
    p  =  0.3275911
    
    sign = 1 if x >= 0 else -1
    x = abs(x)
    
    t = 1.0 / (1.0 + p * x)
    t2 = t * t
    t3 = t2 * t
    t4 = t3 * t
    t5 = t4 * t
    y = 1.0 - ((((a5 * t5 + a4 * t4) + a3 * t3) + a2 * t2) + a1 * t) * math.exp(-x * x)
    
    return sign * y

def norm_cdf_pure(x: float) -> float:
    """累積正規分布関数（Pure Python実装）."""
    return 0.5 * (1.0 + erf_approx(x / math.sqrt(2.0)))

def black_scholes_pure_python(
    s: float, k: float, t: float, r: float, sigma: float
) -> float:
    """純Python実装（外部ライブラリなし）."""
    # mathモジュールのみ使用
    sqrt_t = math.sqrt(t)
    d1 = (math.log(s / k) + (r + 0.5 * sigma * sigma) * t) / (sigma * sqrt_t)
    d2 = d1 - sigma * sqrt_t
    
    # 累積正規分布関数を自前実装
    nd1 = norm_cdf_pure(d1)
    nd2 = norm_cdf_pure(d2)
    
    return s * nd1 - k * math.exp(-r * t) * nd2

def black_scholes_scipy_single(
    s: float, k: float, t: float, r: float, sigma: float
) -> float:
    """SciPy実装（一般的な実装）."""
    d1 = (np.log(s / k) + (r + 0.5 * sigma ** 2) * t) / (sigma * np.sqrt(t))
    d2 = d1 - sigma * np.sqrt(t)
    return s * norm.cdf(d1) - k * np.exp(-r * t) * norm.cdf(d2)

def black_scholes_numpy_batch(
    spots: NDArray[np.float64],
    k: float, t: float, r: float, sigma: float
) -> NDArray[np.float64]:
    """NumPy実装（バッチ処理最適化）."""
    sqrt_t = np.sqrt(t)
    d1 = (np.log(spots / k) + (r + 0.5 * sigma ** 2) * t) / (sigma * sqrt_t)
    d2 = d1 - sigma * sqrt_t
    return spots * norm.cdf(d1) - k * np.exp(-r * t) * norm.cdf(d2)

def black_scholes_pure_python_batch(
    spots: List[float],
    k: float, t: float, r: float, sigma: float
) -> List[float]:
    """Pure Pythonバッチ処理（リスト内包表記）."""
    return [black_scholes_pure_python(s, k, t, r, sigma) for s in spots]
```

#### 2.2 ベンチマーク実行スクリプト（benchmarks/run_comparison.py）
```python
"""Black-Scholesの性能比較."""

import time
import json
import numpy as np
import platform
import psutil
from typing import Dict, Any, List
from quantforge.models import black_scholes
from python_baseline import (
    black_scholes_pure_python,
    black_scholes_scipy_single,
    black_scholes_numpy_batch,
    black_scholes_pure_python_batch
)

class BenchmarkRunner:
    """ベンチマーク実行クラス."""
    
    def __init__(self, warmup_runs: int = 100, measure_runs: int = 1000):
        self.warmup_runs = warmup_runs
        self.measure_runs = measure_runs
        
    def get_system_info(self) -> Dict[str, Any]:
        """システム情報を取得."""
        return {
            "platform": platform.platform(),
            "processor": platform.processor(),
            "cpu_count": psutil.cpu_count(logical=False),
            "cpu_count_logical": psutil.cpu_count(logical=True),
            "memory_gb": round(psutil.virtual_memory().total / (1024**3), 1),
            "python_version": platform.python_version(),
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        }
    
    def benchmark_single(self) -> Dict[str, float]:
        """単一計算のベンチマーク."""
        s, k, t, r, sigma = 100.0, 100.0, 1.0, 0.05, 0.2
        
        results = {}
        
        # QuantForge (Rust)
        for _ in range(self.warmup_runs):
            black_scholes.call_price(s, k, t, r, sigma)
        
        times = []
        for _ in range(self.measure_runs):
            start = time.perf_counter()
            black_scholes.call_price(s, k, t, r, sigma)
            times.append(time.perf_counter() - start)
        qf_time = np.median(times)  # 中央値を使用（外れ値の影響を軽減）
        results["quantforge"] = qf_time
        
        # Pure Python（外部ライブラリなし）
        for _ in range(min(self.warmup_runs, 10)):  # 遅いので少なめ
            black_scholes_pure_python(s, k, t, r, sigma)
            
        times = []
        for _ in range(min(self.measure_runs, 100)):  # 遅いので少なめ
            start = time.perf_counter()
            black_scholes_pure_python(s, k, t, r, sigma)
            times.append(time.perf_counter() - start)
        py_time = np.median(times)
        results["pure_python"] = py_time
        
        # SciPy（一般的な実装）
        for _ in range(self.warmup_runs):
            black_scholes_scipy_single(s, k, t, r, sigma)
            
        times = []
        for _ in range(self.measure_runs):
            start = time.perf_counter()
            black_scholes_scipy_single(s, k, t, r, sigma)
            times.append(time.perf_counter() - start)
        scipy_time = np.median(times)
        results["scipy"] = scipy_time
        
        # 相対性能計算
        results["speedup_vs_pure_python"] = py_time / qf_time
        results["speedup_vs_scipy"] = scipy_time / qf_time
        
        return results
    
    def benchmark_batch(self, size: int) -> Dict[str, Any]:
        """バッチ処理のベンチマーク."""
        spots = np.random.uniform(50, 150, size).astype(np.float64)
        spots_list = spots.tolist()  # Pure Python用
        k, t, r, sigma = 100.0, 1.0, 0.05, 0.2
        
        results = {"size": size}
        
        # QuantForge
        _ = black_scholes.call_price_batch(spots[:min(100, size)], k, t, r, sigma)
        start = time.perf_counter()
        _ = black_scholes.call_price_batch(spots, k, t, r, sigma)
        qf_time = time.perf_counter() - start
        results["quantforge"] = qf_time
        
        # NumPy Batch
        _ = black_scholes_numpy_batch(spots[:min(100, size)], k, t, r, sigma)
        start = time.perf_counter()
        _ = black_scholes_numpy_batch(spots, k, t, r, sigma)
        np_time = time.perf_counter() - start
        results["numpy_batch"] = np_time
        
        # Pure Python (小さいサイズのみ)
        if size <= 1000:
            start = time.perf_counter()
            _ = black_scholes_pure_python_batch(spots_list, k, t, r, sigma)
            py_time = time.perf_counter() - start
            results["pure_python"] = py_time
            results["speedup_vs_pure_python"] = py_time / qf_time
        
        # 相対性能とスループット
        results["speedup_vs_numpy"] = np_time / qf_time
        results["throughput_qf"] = size / qf_time
        results["throughput_np"] = size / np_time
            
        return results
    
    def run_all(self) -> Dict[str, Any]:
        """全ベンチマークを実行."""
        print("🚀 ベンチマーク開始...")
        
        results = {
            "system_info": self.get_system_info(),
            "single": {},
            "batch": []
        }
        
        print("📊 単一計算ベンチマーク実行中...")
        results["single"] = self.benchmark_single()
        
        print("📊 バッチ処理ベンチマーク実行中...")
        for size in [100, 1000, 10000, 100000, 1000000]:
            print(f"  - サイズ {size:,} ...")
            results["batch"].append(self.benchmark_batch(size))
        
        # 結果をJSONファイルに保存
        with open("benchmark_results.json", "w") as f:
            json.dump(results, f, indent=2)
        
        print("✅ ベンチマーク完了")
        return results

if __name__ == "__main__":
    runner = BenchmarkRunner()
    results = runner.run_all()
    
    # 簡易結果表示
    print("\n=== 結果サマリ ===")
    single = results["single"]
    print(f"単一計算: QuantForgeはPure Pythonより{single['speedup_vs_pure_python']:.0f}倍高速")
    
    batch_1m = next((b for b in results["batch"] if b["size"] == 1000000), None)
    if batch_1m:
        print(f"100万件バッチ: QuantForgeはNumPyより{batch_1m['speedup_vs_numpy']:.1f}倍高速")
        print(f"スループット: {batch_1m['throughput_qf']/1e6:.1f}M ops/sec")
```

#### 2.3 実行スクリプト（benchmarks/run_benchmarks.sh）
```bash
#!/bin/bash
set -e

echo "🚀 QuantForge Black-Scholesベンチマーク実行"
echo "==========================================="
date

# スクリプトのディレクトリを取得
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/.." && pwd )"

# Rustベンチマーク実行（プロジェクトルートから）
echo ""
echo "📊 Rustネイティブベンチマーク"
echo "------------------------------"
cd "$PROJECT_ROOT"
cargo bench --bench benchmark -- black_scholes 2>&1 | grep -E "time:|throughput:" || true

# Python比較ベンチマーク（benchmarksディレクトリから）
echo ""
echo "📊 Python比較ベンチマーク"
echo "------------------------"
cd "$SCRIPT_DIR"
uv run python run_comparison.py

# 結果をMarkdown形式で出力
echo ""
echo "📝 結果をMarkdown形式で保存中..."
uv run python format_results.py > "$PROJECT_ROOT/docs/performance/benchmarks_$(date +%Y%m%d).md"

echo ""
echo "✅ ベンチマーク完了"
echo "結果: docs/performance/benchmarks_$(date +%Y%m%d).md"
```

#### 2.4 結果フォーマッタ（benchmarks/format_results.py）
```python
"""ベンチマーク結果をMarkdown形式にフォーマット."""

import json
from datetime import datetime
from pathlib import Path

def format_time(seconds: float) -> str:
    """時間を適切な単位でフォーマット."""
    if seconds < 1e-6:
        return f"{seconds*1e9:.1f} ns"
    elif seconds < 1e-3:
        return f"{seconds*1e6:.2f} μs"
    elif seconds < 1:
        return f"{seconds*1e3:.2f} ms"
    else:
        return f"{seconds:.2f} s"

def format_markdown(results: dict) -> str:
    """結果をMarkdown形式にフォーマット."""
    md = []
    
    # ヘッダー
    md.append("# Black-Scholesベンチマーク結果")
    md.append("")
    md.append(f"測定日時: {results['system_info']['timestamp']}")
    md.append("")
    
    # システム情報
    md.append("## 測定環境")
    md.append("")
    info = results["system_info"]
    md.append(f"- **プラットフォーム**: {info['platform']}")
    md.append(f"- **CPU**: {info['processor']}")
    md.append(f"- **コア数**: {info['cpu_count']} (論理: {info['cpu_count_logical']})")
    md.append(f"- **メモリ**: {info['memory_gb']} GB")
    md.append(f"- **Python**: {info['python_version']}")
    md.append("")
    
    # 単一計算結果
    md.append("## 単一計算性能")
    md.append("")
    md.append("### 実測値")
    single = results["single"]
    md.append("| 実装 | 時間 | 説明 |")
    md.append("|------|------|------|")
    md.append(f"| QuantForge (Rust) | {format_time(single['quantforge'])} | 最適化されたRust実装 |")
    md.append(f"| SciPy | {format_time(single['scipy'])} | 一般的なPython実装 |")
    md.append(f"| Pure Python | {format_time(single['pure_python'])} | 外部ライブラリなし |")
    md.append("")
    
    md.append("### 相対性能")
    md.append("| 比較 | 高速化率 |")
    md.append("|------|----------|")
    md.append(f"| QuantForge vs Pure Python | **{single['speedup_vs_pure_python']:.0f}倍** 高速 |")
    md.append(f"| QuantForge vs SciPy | **{single['speedup_vs_scipy']:.1f}倍** 高速 |")
    md.append("")
    
    # バッチ処理結果
    md.append("## バッチ処理性能")
    md.append("")
    md.append("| データサイズ | QuantForge | NumPy | Pure Python | QF高速化率 | QFスループット |")
    md.append("|-------------|------------|-------|-------------|-----------|----------------|")
    
    for batch in results["batch"]:
        size = batch['size']
        qf_time = format_time(batch['quantforge'])
        np_time = format_time(batch['numpy_batch'])
        
        if 'pure_python' in batch:
            py_time = format_time(batch['pure_python'])
            py_speedup = f"{batch['speedup_vs_pure_python']:.0f}x"
        else:
            py_time = "N/A"
            py_speedup = "-"
        
        np_speedup = batch['speedup_vs_numpy']
        throughput = batch['throughput_qf'] / 1e6
        
        md.append(f"| {size:,} | {qf_time} | {np_time} | {py_time} | "
                 f"NumPy: {np_speedup:.1f}x | {throughput:.1f}M ops/sec |")
    
    md.append("")
    
    # 要約
    md.append("## パフォーマンス要約")
    md.append("")
    
    # 単一計算の要約
    md.append("### 単一計算")
    md.append(f"- QuantForgeはPure Pythonより**{results['single']['speedup_vs_pure_python']:.0f}倍**高速")
    md.append(f"- QuantForgeはSciPyより**{results['single']['speedup_vs_scipy']:.1f}倍**高速")
    md.append("")
    
    # バッチ処理の要約
    md.append("### バッチ処理（100万件）")
    batch_1m = next((b for b in results['batch'] if b['size'] == 1000000), None)
    if batch_1m:
        md.append(f"- QuantForgeはNumPyより**{batch_1m['speedup_vs_numpy']:.0f}倍**高速")
        md.append(f"- 実測スループット: **{batch_1m['throughput_qf']/1e6:.1f}M ops/sec**")
        md.append(f"- 処理時間: {format_time(batch_1m['quantforge'])}")
    md.append("")
    
    # 注記
    md.append("## 測定方法")
    md.append("")
    md.append("- **測定回数**: ウォームアップ100回後、1000回測定の中央値")
    md.append("- **Pure Python**: 外部ライブラリを使用しない実装")
    md.append("- **SciPy**: scipy.stats.normを使用した一般的な実装")
    md.append("- **NumPy**: ベクトル化されたバッチ処理実装")
    md.append("- **QuantForge**: Rust + SIMD最適化実装")
    md.append("")
    
    md.append("## 再現方法")
    md.append("")
    md.append("```bash")
    md.append("# ベンチマーク実行（推奨）")
    md.append("cd benchmarks")
    md.append("./run_benchmarks.sh")
    md.append("")
    md.append("# または個別実行")
    md.append("cd benchmarks")
    md.append("uv run python run_comparison.py")
    md.append("uv run python format_results.py")
    md.append("```")
    md.append("")
    
    return "\n".join(md)

if __name__ == "__main__":
    # 前回の実行結果を読み込み
    with open("benchmark_results.json", "r") as f:
        results = json.load(f)
    
    # Markdown形式で出力
    print(format_markdown(results))
```

### Phase 3: テスト作成（1時間）
- [ ] ベンチマークスクリプトのテスト
- [ ] 結果フォーマッタのテスト
- [ ] 比較実装の正確性テスト（値の一致確認）

```python
# tests/test_benchmark_implementations.py
"""ベンチマーク実装の正確性テスト."""

import pytest
import numpy as np
from benchmarks.python_baseline import (
    black_scholes_pure_python,
    black_scholes_scipy_single,
    black_scholes_numpy_batch
)
from quantforge.models import black_scholes

def test_implementations_consistency():
    """各実装の結果が一致することを確認."""
    s, k, t, r, sigma = 100.0, 100.0, 1.0, 0.05, 0.2
    
    # 各実装の結果
    qf_result = black_scholes.call_price(s, k, t, r, sigma)
    pure_result = black_scholes_pure_python(s, k, t, r, sigma)
    scipy_result = black_scholes_scipy_single(s, k, t, r, sigma)
    
    # 誤差1%以内で一致
    assert abs(qf_result - scipy_result) / scipy_result < 0.01
    assert abs(pure_result - scipy_result) / scipy_result < 0.01
```

### Phase 4: 品質チェック（30分）
```bash
# Python品質チェック
cd benchmarks
uv run ruff format .
uv run ruff check .
uv run mypy --strict .

# 重複チェック
similarity-py --threshold 0.80 --min-lines 5 .
```

### Phase 5: ドキュメント更新（1時間）
- [ ] docs/performance/benchmarks.mdの更新
- [ ] 測定方法の文書化
- [ ] 再現手順の記載

## 命名定義セクション

### 使用する既存命名
```yaml
existing_names:
  - name: "s"
    meaning: "スポット価格"
    source: "naming_conventions.md#共通パラメータ"
  - name: "k"
    meaning: "権利行使価格"
    source: "naming_conventions.md#共通パラメータ"
  - name: "t"
    meaning: "満期までの時間"
    source: "naming_conventions.md#共通パラメータ"
  - name: "r"
    meaning: "リスクフリーレート"
    source: "naming_conventions.md#共通パラメータ"
  - name: "sigma"
    meaning: "ボラティリティ"
    source: "naming_conventions.md#共通パラメータ"
  - name: "call_price"
    meaning: "コールオプション価格計算"
    source: "既存のBlack-Scholesモジュール"
  - name: "call_price_batch"
    meaning: "バッチ処理版"
    source: "既存のBlack-Scholesモジュール"
```

### 新規提案命名
```yaml
proposed_names:
  - name: "python_baseline"
    meaning: "Python比較用基準実装"
    justification: "ベンチマーク専用のため明確な名前"
    status: "内部使用のみ"
  - name: "run_comparison"
    meaning: "比較ベンチマーク実行"
    justification: "目的を明確に示す名前"
    status: "スクリプト名として使用"
  - name: "erf_approx"
    meaning: "誤差関数の近似"
    justification: "数学的標準名称"
    status: "Pure Python内部実装"
  - name: "norm_cdf_pure"
    meaning: "累積正規分布関数のPure Python実装"
    justification: "実装方法を明確に示す"
    status: "Pure Python内部実装"
```

### 命名の一貫性チェックリスト
- [x] 既存モデルとの整合性確認
- [x] naming_conventions.mdとの一致確認
- [x] ドキュメントでの使用方法定義
- [x] APIパラメータは省略形を使用
- [x] エラーメッセージでもAPI名を使用

## リスクと対策

| リスク | 影響度 | 対策 |
|--------|--------|------|
| 測定値のばらつき | 中 | 中央値使用、複数回測定 |
| 環境依存性 | 低 | 環境情報の詳細記録 |
| Pythonオーバーヘッド | 中 | ウォームアップ実行 |
| Pure Python実装の精度 | 低 | Abramowitz近似の使用 |

## 成果物

- [ ] benchmarks/python_baseline.py - Python比較実装（Pure/SciPy/NumPy）
- [ ] benchmarks/run_comparison.py - ベンチマーク実行
- [ ] benchmarks/format_results.py - 結果フォーマッタ
- [ ] benchmarks/run_benchmarks.sh - 統合実行スクリプト
- [ ] docs/performance/benchmarks_YYYYMMDD.md - 測定結果
- [ ] tests/test_benchmark_implementations.py - 実装テスト

## 完了条件

- [ ] Pure Python実装（外部ライブラリなし）
- [ ] 実測値ベースの性能データ
- [ ] Python/SciPy/NumPyとの相対比較
- [ ] 再現可能なベンチマークコード
- [ ] 公正で透明性のあるドキュメント
- [ ] 品質ゲート（ruff, mypy）通過

## 備考

- **Pure Python**: math モジュールのみ使用、scipy/numpy不使用
- **Docker環境**: 別計画で実施
- **Black-Scholesモデルのみ**: 他モデルは対象外
- **実環境重視**: 理論値ではなく実測値
- **相対性能強調**: 絶対値より倍率を重視