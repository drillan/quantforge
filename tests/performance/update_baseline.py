#!/usr/bin/env python3
"""ベースライン更新スクリプト.

最新のベンチマーク結果をベースラインとして保存します。
GitHub Actionsのmainブランチで使用されることを想定しています。
"""

import json
import re
import shutil
import sys
from pathlib import Path
from typing import Any


class BaselineUpdater:
    """ベースラインを更新."""

    def __init__(self):
        self.benchmark_results_dir = Path("benchmark_results")
        self.performance_dir = Path("tests/performance")

    def load_latest_results(self) -> dict[str, Any]:
        """最新の結果を読み込む."""
        latest_path = self.benchmark_results_dir / "latest.json"

        if not latest_path.exists():
            print(f"❌ 最新の結果が見つかりません: {latest_path}")
            print("  先にベンチマークを実行してください: pytest tests/performance/ -m benchmark")
            sys.exit(1)

        with open(latest_path) as f:
            return json.load(f)

    def validate_results(self, results: dict[str, Any]) -> bool:
        """結果の妥当性を検証."""
        # 必須フィールドのチェック
        required_fields = ["benchmarks", "environment", "timestamp"]
        for field in required_fields:
            if field not in results:
                print(f"❌ 必須フィールドが不足: {field}")
                return False

        # ベンチマーク結果の検証
        benchmarks = results.get("benchmarks", [])
        if len(benchmarks) < 3:  # 最低3つのテスト（単一計算）
            print("❌ ベンチマーク結果が不足")
            return False

        # 必須テストの存在確認
        test_names = [b["name"] for b in benchmarks]
        required_tests = [
            "test_quantforge_single",
            "test_pure_python_single",
            "test_numpy_scipy_single"
        ]

        for test in required_tests:
            if not any(test in name for name in test_names):
                print(f"❌ 必須テストが不足: {test}")
                return False

        return True

    def extract_benchmark_times(self, benchmarks: list[dict]) -> dict[str, dict[str, float]]:
        """ベンチマーク結果から実行時間を抽出."""
        results: dict[str, dict[str, float]] = {}

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

    def update_baseline(self, output_path: Path = None) -> None:
        """ベースラインを更新.

        Args:
            output_path: 出力先パス（デフォルト: tests/performance/baseline.json）
        """
        if output_path is None:
            output_path = self.performance_dir / "baseline.json"

        # 最新結果を読み込み
        latest = self.load_latest_results()

        # 検証
        if not self.validate_results(latest):
            print("❌ 結果の検証に失敗しました")
            sys.exit(1)

        # 既存のベースラインをバックアップ（存在する場合）
        if output_path.exists():
            backup_path = output_path.with_suffix(".json.bak")
            shutil.copy2(output_path, backup_path)
            print(f"📁 既存のベースラインをバックアップ: {backup_path}")

        # 新しいベースラインを保存（latest.jsonをそのまま使用）
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w") as f:
            json.dump(latest, f, indent=2)

        print(f"✅ ベースラインを更新しました: {output_path}")

        # サマリーを表示
        self.print_summary(latest)

    def print_summary(self, results: dict[str, Any]) -> None:
        """結果のサマリーを表示."""
        print("\n" + "=" * 60)
        print("📊 ベースラインサマリー")
        print("=" * 60)

        # 環境情報
        env = results["environment"]
        print("\n環境:")
        print(f"  - プラットフォーム: {env.get('platform', 'N/A')}")
        print(f"  - Python: {env.get('python_version', 'N/A')}")
        print(f"  - CPU: {env.get('cpu_count', 'N/A')}コア")

        # ベンチマーク時間を抽出
        times = self.extract_benchmark_times(results.get("benchmarks", []))

        # 単一計算
        if "single" in times:
            single = times["single"]
            print("\n単一計算:")
            if "quantforge" in single:
                print(f"  - QuantForge: {self.format_time(single['quantforge'])}")
            if "pure_python" in single:
                print(f"  - Pure Python: {self.format_time(single['pure_python'])}")
            if "numpy_scipy" in single:
                print(f"  - NumPy+SciPy: {self.format_time(single['numpy_scipy'])}")

        # バッチ処理（主要なサイズのみ）
        batch_sizes = [100, 1000, 10000, 100000]
        has_batch = False
        for size in batch_sizes:
            key = f"batch_{size}"
            if key in times and "quantforge" in times[key]:
                if not has_batch:
                    print("\nバッチ処理（QuantForge）:")
                    has_batch = True
                qf_time = times[key]["quantforge"]
                print(f"  - {size:7,}件: {self.format_time(qf_time)}")


def main():
    """メイン処理."""
    import argparse

    parser = argparse.ArgumentParser(description="ベースライン更新")
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("tests/performance/baseline.json"),
        help="ベースラインの出力先"
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="更新せずに現在の結果を確認するのみ"
    )

    args = parser.parse_args()

    updater = BaselineUpdater()

    if args.check:
        # 確認のみ
        latest = updater.load_latest_results()
        if updater.validate_results(latest):
            print("✅ 結果は有効です")
            updater.print_summary(latest)
        else:
            print("❌ 結果が無効です")
            sys.exit(1)
    else:
        # ベースライン更新
        updater.update_baseline(args.output)


if __name__ == "__main__":
    main()
