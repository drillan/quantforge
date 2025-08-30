# 検証スクリプト仕様

## 概要
リアーキテクチャの各フェーズで使用する検証スクリプトの仕様と期待される出力を定義します。

## Phase 0: 準備フェーズ

### `scripts/measure_api_coverage.py`
```python
#!/usr/bin/env python3
"""API カバレッジ測定スクリプト"""

import ast
import json
from pathlib import Path
from typing import Set, Dict

def get_public_apis() -> Set[str]:
    """公開APIのリストを取得"""
    # quantforgeモジュールから公開APIを抽出
    pass

def get_golden_master_apis() -> Set[str]:
    """ゴールデンマスターに含まれるAPIを取得"""
    with open('tests/golden/comprehensive_suite.json') as f:
        data = json.load(f)
    # テストケースからAPIを抽出
    pass

def calculate_coverage() -> float:
    """カバレッジを計算"""
    public = get_public_apis()
    tested = get_golden_master_apis()
    return len(tested & public) / len(public) * 100

if __name__ == '__main__':
    coverage = calculate_coverage()
    print(f"API Coverage: {coverage:.2f}%")
    
    # 完了条件: 95%以上
    if coverage >= 95:
        print("✅ Coverage requirement met")
        exit(0)
    else:
        print(f"❌ Coverage too low (required: 95%, actual: {coverage:.2f}%)")
        exit(1)
```

**期待される出力**:
```
API Coverage: 96.50%
✅ Coverage requirement met
```

## Phase 1: Core層構築

### `scripts/check_pyo3_dependencies.py`
```python
#!/usr/bin/env python3
"""PyO3依存チェックスクリプト"""

import subprocess
import sys

def check_core_dependencies():
    """CoreクレートのPyO3依存をチェック"""
    result = subprocess.run(
        ["cargo", "tree", "-p", "quantforge-core", "--no-default-features"],
        capture_output=True,
        text=True,
        cwd="core"
    )
    
    if "pyo3" in result.stdout:
        print("❌ PyO3 dependency found in core crate!")
        print(result.stdout)
        return False
    
    print("✅ No PyO3 dependency in core crate")
    return True

if __name__ == '__main__':
    if check_core_dependencies():
        exit(0)
    else:
        exit(1)
```

**期待される出力**:
```
✅ No PyO3 dependency in core crate
```

### `scripts/validate_workspace.sh`
```bash
#!/bin/bash
# ワークスペース構成の検証

echo "=== Validating Rust Workspace ==="

# ワークスペースのチェック
if ! cargo check --workspace 2>/dev/null; then
    echo "❌ Workspace check failed"
    exit 1
fi

echo "✅ Workspace configuration valid"

# 各クレートのビルド確認
echo "=== Building crates ==="
cargo build --package quantforge-core --release
if [ $? -eq 0 ]; then
    echo "✅ Core crate builds successfully"
else
    echo "❌ Core crate build failed"
    exit 1
fi

cargo build --package quantforge-python --release
if [ $? -eq 0 ]; then
    echo "✅ Python bindings crate builds successfully"
else
    echo "❌ Python bindings build failed"
    exit 1
fi

echo "=== All checks passed ==="
```

## Phase 2: Bindings層構築

### `scripts/check_api_compatibility.py`
```python
#!/usr/bin/env python3
"""API互換性チェックスクリプト"""

import inspect
import json
from typing import Dict, Set, List

def get_old_api_signatures() -> Dict[str, str]:
    """旧APIのシグネチャを取得"""
    # バックアップから旧API定義を読み込み
    with open('backup/api_signatures.json') as f:
        return json.load(f)

def get_new_api_signatures() -> Dict[str, str]:
    """新APIのシグネチャを取得"""
    import quantforge
    signatures = {}
    
    for name in dir(quantforge.models):
        if not name.startswith('_'):
            obj = getattr(quantforge.models, name)
            if callable(obj):
                sig = str(inspect.signature(obj))
                signatures[name] = sig
    
    return signatures

def compare_apis() -> tuple[bool, List[str]]:
    """API比較"""
    old = get_old_api_signatures()
    new = get_new_api_signatures()
    
    issues = []
    
    # 欠落しているAPI
    missing = set(old.keys()) - set(new.keys())
    if missing:
        issues.append(f"Missing APIs: {missing}")
    
    # シグネチャ変更
    for name in set(old.keys()) & set(new.keys()):
        if old[name] != new[name]:
            issues.append(f"Signature changed: {name}")
            issues.append(f"  Old: {old[name]}")
            issues.append(f"  New: {new[name]}")
    
    return len(issues) == 0, issues

if __name__ == '__main__':
    compatible, issues = compare_apis()
    
    if compatible:
        print("✅ API is 100% compatible")
        exit(0)
    else:
        print("❌ API compatibility issues found:")
        for issue in issues:
            print(f"  {issue}")
        exit(1)
```

**期待される出力**:
```
✅ API is 100% compatible
```

## Phase 3: テスト・統合

### `scripts/validate_golden_master.py`
```python
#!/usr/bin/env python3
"""ゴールデンマスター検証スクリプト"""

import json
from pathlib import Path
import numpy as np
from quantforge import models

def validate_all_cases():
    """全テストケースを検証"""
    with open('tests/golden/comprehensive_suite.json') as f:
        test_suite = json.load(f)
    
    total = len(test_suite['test_cases'])
    passed = 0
    failed_cases = []
    
    for case in test_suite['test_cases']:
        try:
            actual = execute_test_case(case)
            expected = case['expected']
            tolerance = case.get('tolerance', 1e-10)
            
            if abs(actual - expected) <= tolerance:
                passed += 1
            else:
                failed_cases.append({
                    'id': case['id'],
                    'expected': expected,
                    'actual': actual,
                    'diff': abs(actual - expected)
                })
        except Exception as e:
            failed_cases.append({
                'id': case['id'],
                'error': str(e)
            })
    
    success_rate = passed / total * 100
    
    print(f"=== Golden Master Validation ===")
    print(f"Total Cases: {total}")
    print(f"Passed: {passed}")
    print(f"Failed: {total - passed}")
    print(f"Success Rate: {success_rate:.2f}%")
    
    if failed_cases:
        print("\nFailed Cases:")
        for case in failed_cases[:5]:  # 最初の5件のみ表示
            print(f"  - {case}")
    
    return success_rate == 100.0

def execute_test_case(case):
    """テストケースを実行"""
    case_type = case['type']
    inputs = case['inputs']
    
    if case_type == 'black_scholes_call':
        return models.call_price(**inputs)
    elif case_type == 'black_scholes_put':
        return models.put_price(**inputs)
    # 他のケースも同様に実装
    
    raise ValueError(f"Unknown case type: {case_type}")

if __name__ == '__main__':
    if validate_all_cases():
        exit(0)
    else:
        exit(1)
```

**期待される出力**:
```
=== Golden Master Validation ===
Total Cases: 1250
Passed: 1250
Failed: 0
Success Rate: 100.00%
```

### `scripts/compare_performance.py`
```python
#!/usr/bin/env python3
"""パフォーマンス比較スクリプト"""

import json
import time
import numpy as np
from quantforge import models

def load_baseline():
    """ベースラインデータを読み込み"""
    with open('benchmarks/baseline.json') as f:
        return json.load(f)

def measure_current_performance():
    """現在のパフォーマンスを測定"""
    results = {}
    
    # 単一計算
    iterations = 100000
    start = time.perf_counter()
    for _ in range(iterations):
        _ = models.call_price(100, 100, 1, 0.05, 0.2)
    elapsed = time.perf_counter() - start
    results['single_call_ns'] = elapsed / iterations * 1e9
    
    # バッチ処理（1M）
    spots = np.random.uniform(50, 150, 1_000_000)
    start = time.perf_counter()
    _ = models.call_price_batch(spots, 100, 1, 0.05, 0.2)
    elapsed = time.perf_counter() - start
    results['batch_1m_ms'] = elapsed * 1000
    
    return results

def compare_with_baseline():
    """ベースラインと比較"""
    baseline = load_baseline()
    current = measure_current_performance()
    
    print("=== Performance Comparison ===")
    print("Metric            | Baseline  | Current   | Change")
    print("------------------|-----------|-----------|--------")
    
    all_within_tolerance = True
    
    for metric in baseline:
        if metric in current:
            base_val = baseline[metric]
            curr_val = current[metric]
            change = (curr_val - base_val) / base_val * 100
            
            status = "✅" if abs(change) <= 5 else "❌"
            all_within_tolerance &= (abs(change) <= 5)
            
            print(f"{metric:17} | {base_val:9.2f} | {curr_val:9.2f} | {change:+6.1f}% {status}")
    
    return all_within_tolerance

if __name__ == '__main__':
    if compare_with_baseline():
        print("\n✅ All metrics within tolerance (±5%)")
        exit(0)
    else:
        print("\n❌ Some metrics outside tolerance")
        exit(1)
```

**期待される出力**:
```
=== Performance Comparison ===
Metric            | Baseline  | Current   | Change
------------------|-----------|-----------|--------
single_call_ns    |     45.20 |     44.80 |   -0.9% ✅
batch_1m_ms       |     85.30 |     83.50 |   -2.1% ✅

✅ All metrics within tolerance (±5%)
```

## Phase 4: 検証と完成

### `scripts/final_validation.py`
```python
#!/usr/bin/env python3
"""最終検証スクリプト"""

import subprocess
import sys
from pathlib import Path

class FinalValidator:
    def __init__(self):
        self.checks = []
    
    def run_check(self, name: str, command: list) -> bool:
        """チェックを実行"""
        try:
            result = subprocess.run(command, capture_output=True, text=True)
            success = result.returncode == 0
            self.checks.append((name, success))
            return success
        except Exception as e:
            self.checks.append((name, False))
            return False
    
    def validate_all(self):
        """すべての検証を実行"""
        print("=== Final Validation ===\n")
        
        # ビルドチェック
        self.run_check(
            "Core Build",
            ["cargo", "build", "--package", "quantforge-core", "--release"]
        )
        
        self.run_check(
            "Python Build", 
            ["maturin", "build", "--release"]
        )
        
        # テストチェック
        self.run_check(
            "Core Tests",
            ["cargo", "test", "--package", "quantforge-core", "--all"]
        )
        
        self.run_check(
            "Python Tests",
            ["pytest", "tests/", "-q"]
        )
        
        # API互換性
        self.run_check(
            "API Compatibility",
            ["python", "scripts/check_api_compatibility.py"]
        )
        
        # ゴールデンマスター
        self.run_check(
            "Golden Master",
            ["python", "scripts/validate_golden_master.py"]
        )
        
        # パフォーマンス
        self.run_check(
            "Performance",
            ["python", "scripts/compare_performance.py"]
        )
        
        # レポート生成
        self.generate_report()
    
    def generate_report(self):
        """レポート生成"""
        print("\n=== Validation Report ===")
        
        for check, passed in self.checks:
            status = "✅" if passed else "❌"
            print(f"{status} {check}")
        
        all_passed = all(passed for _, passed in self.checks)
        
        if all_passed:
            print("\n✅ All validations passed! Ready for merge.")
            exit(0)
        else:
            print("\n❌ Some validations failed. Review required.")
            exit(1)

if __name__ == '__main__':
    validator = FinalValidator()
    validator.validate_all()
```

**期待される出力**:
```
=== Final Validation ===

=== Validation Report ===
✅ Core Build
✅ Python Build
✅ Core Tests
✅ Python Tests
✅ API Compatibility
✅ Golden Master
✅ Performance

✅ All validations passed! Ready for merge.
```

## 使用方法

各フェーズの完了時に対応する検証スクリプトを実行：

```bash
# Phase 0完了時
python scripts/measure_api_coverage.py

# Phase 1完了時
python scripts/check_pyo3_dependencies.py
./scripts/validate_workspace.sh

# Phase 2完了時
python scripts/check_api_compatibility.py

# Phase 3完了時
python scripts/validate_golden_master.py
python scripts/compare_performance.py

# Phase 4完了時
python scripts/final_validation.py
```

すべてのスクリプトが成功（exit code 0）することが、各フェーズの完了条件です。