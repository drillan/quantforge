# ベンチマーク移行実装計画

## 概要
既存のbenchmarksディレクトリから新しい層別ベンチマーク構造への安全な移行計画。
過去データの退避と新形式での記録開始を段階的に実施。

## 移行の基本方針

### 原則
1. **データ保全優先**: 過去のベンチマーク結果は全て保持
2. **検証後削除**: 新形式での動作確認後に旧構造を削除
3. **比較可能性**: 移行期間中は両形式で比較可能
4. **変換不要**: 既存データの変換は行わず、アーカイブとして保持

## 移行フェーズ

### Phase 1: 新構造の準備と実装 [即座実施]

#### 1.1 ディレクトリ構造の作成
```bash
# 新しい層別ベンチマーク構造
mkdir -p core/benches                           # ✅ 既に存在
mkdir -p bindings/python/tests/benchmarks       # 要作成
mkdir -p tests/performance                      # ✅ 既に存在

# 新形式の結果保存場所
mkdir -p benchmark_results/{core,bindings/python,integration}/history
```

#### 1.2 ベンチマークコードの実装

##### Core層（core/benches/）
- ✅ 既に実装済み: math_benchmark.rs, models_benchmark.rs
- 純粋なRustアルゴリズム性能測定

##### Bindings層（bindings/python/tests/benchmarks/）
```python
# ffi_overhead.py - FFI呼び出しコスト測定
# zero_copy.py - NumPy配列のゼロコピー検証
# broadcasting.py - Broadcasting性能測定
```

##### Integration層（tests/performance/）
```python
# integration_benchmark.py - E2E性能測定
# workflow_benchmark.py - 実際のユースケース性能
```

### Phase 2: 既存資産の活用と配置 [1日]

#### 2.1 管理ツールの移動（参照のみ、実装は新規）
```bash
# 新しい場所に管理ツールを作成（既存を参考に）
# benchmarks/baseline_manager.py → tests/performance/baseline_manager.py
# benchmarks/performance_guard.py → tests/performance/performance_guard.py

# 注: 既存ファイルはまだ削除しない
```

#### 2.2 新形式での記録開始
```python
# tests/performance/benchmark_recorder.py
class BenchmarkRecorder:
    """新形式（v2.0.0）でのベンチマーク記録"""
    
    def __init__(self):
        self.results_dir = Path('benchmark_results')
        self.legacy_dir = Path('benchmarks/results')  # 参照用
    
    def record(self, layer: str, results: dict):
        """層別の新形式で記録"""
        # benchmark_results/{layer}/latest.json
        # benchmark_results/{layer}/history/YYYY-MM-DD/run_HHMMSS.json
```

### Phase 3: 検証と並行運用 [1週間]

#### 3.1 新形式での記録開始
```bash
# 新しいベンチマークの実行
cargo bench --package quantforge-core                    # Core層
pytest bindings/python/tests/benchmarks/                 # Bindings層  
pytest tests/performance/                                # Integration層
```

#### 3.2 検証項目
- [ ] Core層のベンチマーク結果が`benchmark_results/core/`に保存
- [ ] Bindings層の結果が`benchmark_results/bindings/python/`に保存
- [ ] Integration層の結果が`benchmark_results/integration/`に保存
- [ ] 各層の履歴が`history/`サブディレクトリに蓄積

#### 3.3 比較検証
```python
# scripts/verify_benchmark_migration.py
def verify_migration():
    """新旧形式の比較検証"""
    
    # 旧形式のデータ
    old_latest = Path('benchmarks/results/latest.json')
    old_baseline = Path('benchmarks/results/baseline.json')
    
    # 新形式のデータ
    new_integration = Path('benchmark_results/integration/latest.json')
    
    # 性能が大幅に変わっていないか確認
    # （フォーマットは異なるが、主要メトリクスを比較）
    return compare_key_metrics(old_latest, new_integration)
```

### Phase 4: 旧構造の退避と削除 [検証完了後]

#### 4.1 過去データのアーカイブ
```bash
# 過去のベンチマーク結果を退避
mkdir -p archive/benchmarks-legacy-$(date +%Y%m%d)

# resultsディレクトリのみ退避（比較用データ）
cp -r benchmarks/results/ archive/benchmarks-legacy-$(date +%Y%m%d)/

# 分析レポートも保存
cp benchmarks/results/*.md archive/benchmarks-legacy-$(date +%Y%m%d)/
```

#### 4.2 旧構造の削除
```bash
# 検証完了を確認
if [ -f "benchmark_results/integration/latest.json" ] && \
   [ -d "archive/benchmarks-legacy-$(date +%Y%m%d)" ]; then
    
    # benchmarksディレクトリを完全削除
    rm -rf benchmarks/
    
    echo "✅ Migration complete. Legacy data archived in archive/"
fi
```

## 実装スクリプト

### 移行実行スクリプト
```bash
#!/bin/bash
# scripts/migrate_benchmarks.sh

set -e  # エラー時に停止

echo "=== ベンチマーク移行開始 ==="

# Phase 1: 新構造の作成
echo "📁 Creating new benchmark structure..."
mkdir -p bindings/python/tests/benchmarks
mkdir -p benchmark_results/{core,bindings/python,integration}/history

# Phase 2: ベンチマークコードの配置
echo "📝 Setting up benchmark code..."
# ここで新しいベンチマークファイルを作成

# Phase 3: 初回実行
echo "🚀 Running benchmarks in new structure..."
cargo bench --package quantforge-core || true
# Python側は後で実装

# Phase 4: 検証
echo "✅ Verifying new structure..."
if [ -d "benchmark_results" ]; then
    echo "New benchmark_results directory created successfully"
    ls -la benchmark_results/
fi

echo "=== 移行準備完了 ==="
echo "次のステップ:"
echo "1. 新形式でベンチマークを実行"
echo "2. 結果を検証"
echo "3. archive/benchmarks-legacy-YYYYMMDD/ に退避"
echo "4. benchmarks/ を削除"
```

### 検証スクリプト
```python
# scripts/verify_benchmark_structure.py
"""新しいベンチマーク構造の検証"""

from pathlib import Path
import json
import sys

def verify_structure():
    """構造と動作を検証"""
    
    checks = {
        'core_benches': Path('core/benches').exists(),
        'bindings_benchmarks': Path('bindings/python/tests/benchmarks').exists(),
        'performance_tests': Path('tests/performance').exists(),
        'results_dir': Path('benchmark_results').exists(),
        'core_results': Path('benchmark_results/core').exists(),
        'bindings_results': Path('benchmark_results/bindings/python').exists(),
        'integration_results': Path('benchmark_results/integration').exists(),
    }
    
    # 各項目をチェック
    all_passed = True
    for name, check in checks.items():
        status = "✅" if check else "❌"
        print(f"{status} {name}: {check}")
        if not check:
            all_passed = False
    
    # 新形式のデータが存在するか
    if Path('benchmark_results/integration/latest.json').exists():
        print("✅ New format data exists")
        with open('benchmark_results/integration/latest.json') as f:
            data = json.load(f)
            print(f"  Version: {data.get('version', 'N/A')}")
            print(f"  Layer: {data.get('layer', 'N/A')}")
    else:
        print("⚠️  No new format data yet")
    
    return all_passed

if __name__ == '__main__':
    if verify_structure():
        print("\n✅ All checks passed!")
        sys.exit(0)
    else:
        print("\n❌ Some checks failed")
        sys.exit(1)
```

## リスクと対策

| リスク | 影響 | 対策 |
|--------|------|------|
| データ損失 | 高 | 削除前に必ずarchive/に退避 |
| 性能退行の見逃し | 中 | 並行運用期間中に比較検証 |
| CI/CD破損 | 低 | 移行期間中は両パスをサポート |

## 成功基準

- [ ] 新形式で全層のベンチマークが記録される
- [ ] 過去データがarchive/に安全に退避される
- [ ] benchmarks/ディレクトリが完全削除される
- [ ] CI/CDが新構造で正常動作する

## タイムライン

1. **即座**: 新構造の作成とコード配置
2. **1日目**: 新形式での初回記録
3. **2-7日目**: 並行運用と検証
4. **8日目**: 旧データ退避と旧構造削除

## 備考

- 既存データの変換は不要（アーカイブとして保持）
- 一時的な比較は手動で実施可能
- 新形式は将来の多言語対応を考慮した設計