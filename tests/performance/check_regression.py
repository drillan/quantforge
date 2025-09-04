#!/usr/bin/env python3
"""パフォーマンス退行検出スクリプト.

GitHub ActionsのCI環境でベースラインと最新結果を比較し、
パフォーマンス退行がある場合はビルドを失敗させます。
"""

import json
import re
import sys
from pathlib import Path
from typing import Dict, List


class RegressionChecker:
    """パフォーマンス退行をチェック."""
    
    def __init__(self, threshold: float = 1.2):
        """初期化.
        
        Args:
            threshold: 許容する劣化率（1.2 = 20%の劣化まで許容）
        """
        self.threshold = threshold
        self.violations: List[str] = []
        self.warnings: List[str] = []
        
    def load_json(self, path: Path) -> Dict:
        """JSONファイルを読み込む."""
        if not path.exists():
            print(f"❌ ファイルが見つかりません: {path}")
            sys.exit(1)
            
        with open(path) as f:
            return json.load(f)
    
    def extract_benchmark_times(self, benchmarks: List[Dict]) -> Dict[str, Dict[str, float]]:
        """ベンチマーク結果から実行時間を抽出（generate_benchmark_report.pyと同じ形式）."""
        results: Dict[str, Dict[str, float]] = {}
        
        for bench in benchmarks:
            name = bench["name"]
            mean_time = bench["stats"].get("mean", 0)
            
            # テスト名をパースしてカテゴライズ
            if "test_quantforge_single" in name:
                results.setdefault("single", {})["quantforge"] = mean_time
            elif "test_pure_python_single" in name:
                results.setdefault("single", {})["pure_python"] = mean_time
            elif "test_numpy_scipy_single" in name:
                results.setdefault("single", {})["numpy_scipy"] = mean_time
            elif "test_quantforge_batch" in name:
                size = self._extract_size(name)
                key = f"batch_{size}"
                results.setdefault(key, {})["quantforge"] = mean_time
            elif "test_pure_python_batch" in name:
                size = self._extract_size(name)
                key = f"batch_{size}"
                results.setdefault(key, {})["pure_python"] = mean_time
            elif "test_numpy_scipy_batch" in name:
                size = self._extract_size(name)
                key = f"batch_{size}"
                results.setdefault(key, {})["numpy_scipy"] = mean_time
        
        return results
    
    def _extract_size(self, name: str) -> int:
        """テスト名からバッチサイズを抽出."""
        match = re.search(r"\[(\d+)\]", name)
        if match:
            return int(match.group(1))
        return 0
    
    def format_time(self, time_seconds: float) -> str:
        """時間を適切な単位でフォーマット."""
        if time_seconds < 1e-6:
            return f"{time_seconds * 1e9:.2f} ns"
        elif time_seconds < 1e-3:
            return f"{time_seconds * 1e6:.2f} μs"
        elif time_seconds < 1:
            return f"{time_seconds * 1e3:.2f} ms"
        else:
            return f"{time_seconds:.2f} s"
    
    def compare_metrics(self, baseline_times: Dict, latest_times: Dict) -> None:
        """メトリクスを比較して退行を検出."""
        # 単一計算の比較
        if "single" in baseline_times and "single" in latest_times:
            for impl in ["quantforge", "pure_python", "numpy_scipy"]:
                if impl in baseline_times["single"] and impl in latest_times["single"]:
                    base_time = baseline_times["single"][impl]
                    latest_time = latest_times["single"][impl]
                    
                    if latest_time > base_time * self.threshold:
                        ratio = latest_time / base_time
                        self.violations.append(
                            f"単一計算 ({impl}): {self.format_time(base_time)} → "
                            f"{self.format_time(latest_time)} ({ratio:.2f}x slower)"
                        )
                    elif latest_time > base_time * 1.1:  # 10%の劣化は警告
                        ratio = latest_time / base_time
                        self.warnings.append(
                            f"単一計算 ({impl}): {self.format_time(base_time)} → "
                            f"{self.format_time(latest_time)} ({ratio:.2f}x slower)"
                        )
        
        # バッチ処理の比較
        for key in baseline_times:
            if key.startswith("batch_") and key in latest_times:
                for impl in ["quantforge", "pure_python", "numpy_scipy"]:
                    if impl in baseline_times[key] and impl in latest_times[key]:
                        base_time = baseline_times[key][impl]
                        latest_time = latest_times[key][impl]
                        size = key.replace("batch_", "")
                        
                        if latest_time > base_time * self.threshold:
                            ratio = latest_time / base_time
                            self.violations.append(
                                f"バッチ処理 {size}件 ({impl}): {self.format_time(base_time)} → "
                                f"{self.format_time(latest_time)} ({ratio:.2f}x slower)"
                            )
                        elif latest_time > base_time * 1.1:  # 10%の劣化は警告
                            ratio = latest_time / base_time
                            self.warnings.append(
                                f"バッチ処理 {size}件 ({impl}): {self.format_time(base_time)} → "
                                f"{self.format_time(latest_time)} ({ratio:.2f}x slower)"
                            )
    
    def check_regression(self, baseline_path: Path, latest_path: Path) -> bool:
        """退行チェックを実行.
        
        Returns:
            True: 退行なし、False: 退行検出
        """
        # ファイル読み込み
        baseline = self.load_json(baseline_path)
        latest = self.load_json(latest_path)
        
        # ベンチマーク結果を抽出
        baseline_times = self.extract_benchmark_times(baseline.get("benchmarks", []))
        latest_times = self.extract_benchmark_times(latest.get("benchmarks", []))
        
        # 比較
        self.compare_metrics(baseline_times, latest_times)
        
        # 結果を出力
        print("=" * 60)
        print("🔍 パフォーマンス退行チェック")
        print("=" * 60)
        
        if self.warnings:
            print("\n⚠️ 警告（10%以上の劣化）:")
            for warning in self.warnings:
                print(f"  - {warning}")
        
        if self.violations:
            print("\n❌ 退行検出（20%以上の劣化）:")
            for violation in self.violations:
                print(f"  - {violation}")
            print("\n退行が検出されました。パフォーマンスを確認してください。")
            return False
        
        if not self.warnings and not self.violations:
            print("\n✅ パフォーマンス退行なし")
        
        return True


def main():
    """メイン処理."""
    import argparse
    
    parser = argparse.ArgumentParser(description="パフォーマンス退行検出")
    parser.add_argument(
        "--baseline",
        type=Path,
        default=Path("tests/performance/baseline.json"),
        help="ベースラインファイルのパス"
    )
    parser.add_argument(
        "--latest", 
        type=Path,
        default=Path("benchmark_results/latest.json"),
        help="最新結果ファイルのパス"
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=1.2,
        help="許容する劣化率（1.2 = 20%%の劣化まで許容）"
    )
    
    args = parser.parse_args()
    
    # ベースラインが存在しない場合は警告のみ
    if not args.baseline.exists():
        print("⚠️ ベースラインが存在しません。スキップします。")
        print("  初回実行時は update_baseline.py でベースラインを作成してください。")
        sys.exit(0)
    
    checker = RegressionChecker(threshold=args.threshold)
    success = checker.check_regression(args.baseline, args.latest)
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()