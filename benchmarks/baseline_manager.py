"""ベンチマークベースライン管理システム."""

import json
import statistics
import subprocess
import time
from pathlib import Path
from typing import Any


class BaselineManager:
    """パフォーマンスベースラインの管理."""

    def __init__(self, baseline_path: Path = Path("benchmarks/results/baseline.json")):
        self.baseline_path = baseline_path
        self.baseline_data: dict[str, Any] | None = None
        self.load_baseline()

    def load_baseline(self) -> None:
        """既存のベースラインを読み込む."""
        if self.baseline_path.exists():
            with open(self.baseline_path) as f:
                self.baseline_data = json.load(f)

    def collect_measurements(self, num_runs: int = 5, warmup_runs: int = 2) -> dict[str, Any]:
        """複数回ベンチマークを実行して測定値を収集.

        Args:
            num_runs: 測定回数
            warmup_runs: ウォームアップ回数

        Returns:
            統計情報を含む測定結果
        """
        print(f"ウォームアップ実行中 ({warmup_runs}回)...")
        for _ in range(warmup_runs):
            subprocess.run(
                ["uv", "run", "python", "-m", "benchmarks.runners.comparison"], capture_output=True, text=True
            )
            time.sleep(1)  # システム安定化のため

        measurements: dict[str, dict[str, list[float]]] = {
            "single": {"quantforge": [], "pure_python": [], "numpy_scipy": []},
            "batch_1m": {"quantforge": [], "numpy_batch": []},
        }

        print(f"測定実行中 ({num_runs}回)...")
        for i in range(num_runs):
            print(f"  実行 {i + 1}/{num_runs}")

            # ベンチマーク実行
            subprocess.run(
                ["uv", "run", "python", "-m", "benchmarks.runners.comparison"], capture_output=True, text=True
            )

            # 結果読み込み
            with open("benchmarks/results/latest.json") as f:
                data = json.load(f)

            # 単一計算の測定値を収集
            measurements["single"]["quantforge"].append(data["single"]["quantforge"])
            measurements["single"]["pure_python"].append(data["single"]["pure_python"])
            measurements["single"]["numpy_scipy"].append(data["single"]["numpy_scipy"])

            # 100万件バッチの測定値を収集
            for batch in data["batch"]:
                if batch["size"] == 1000000:
                    measurements["batch_1m"]["quantforge"].append(batch["quantforge"])
                    measurements["batch_1m"]["numpy_batch"].append(batch["numpy_batch"])
                    break

            time.sleep(2)  # システム安定化のため

        return measurements

    def calculate_baseline(self, measurements: dict[str, Any], buffer_factor: float = 1.2) -> dict[str, Any]:
        """測定値からベースラインを計算.

        Args:
            measurements: 収集した測定値
            buffer_factor: バッファ係数（1.2 = 20%のマージン）

        Returns:
            ベースライン値
        """
        baseline: dict[str, Any] = {
            "metadata": {
                "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                "num_measurements": len(measurements["single"]["quantforge"]),
                "buffer_factor": buffer_factor,
            },
            "thresholds": {},
        }

        # 各測定値に対してベースラインを計算
        for category, metrics in measurements.items():
            baseline["thresholds"][category] = {}

            for metric_name, values in metrics.items():
                if values:
                    mean = statistics.mean(values)
                    stdev = statistics.stdev(values) if len(values) > 1 else 0
                    median = statistics.median(values)
                    p95 = sorted(values)[int(len(values) * 0.95)] if len(values) > 1 else values[0]

                    baseline["thresholds"][category][metric_name] = {
                        "mean": mean,
                        "median": median,
                        "stdev": stdev,
                        "p95": p95,
                        "min": min(values),
                        "max": max(values),
                        "threshold_mean": mean * buffer_factor,
                        "threshold_p95": p95 * buffer_factor,
                        "raw_values": values,  # デバッグ用
                    }

        # 速度比も記録
        qf_single = baseline["thresholds"]["single"]["quantforge"]["mean"]
        py_single = baseline["thresholds"]["single"]["pure_python"]["mean"]
        np_single = baseline["thresholds"]["single"]["numpy_scipy"]["mean"]

        baseline["speedup_ratios"] = {
            "single_vs_pure_python": py_single / qf_single,
            "single_vs_numpy_scipy": np_single / qf_single,
        }

        if "batch_1m" in baseline["thresholds"]:
            qf_batch = baseline["thresholds"]["batch_1m"]["quantforge"]["mean"]
            np_batch = baseline["thresholds"]["batch_1m"]["numpy_batch"]["mean"]
            baseline["speedup_ratios"]["batch_1m_vs_numpy"] = np_batch / qf_batch

        return baseline

    def save_baseline(self, baseline: dict[str, Any]) -> None:
        """ベースラインをファイルに保存."""
        self.baseline_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.baseline_path, "w") as f:
            json.dump(baseline, f, indent=2)
        print(f"ベースライン保存: {self.baseline_path}")

    def check_regression(self, current_value: float, metric_path: str) -> tuple[bool, str]:
        """現在の値がベースラインから退行していないかチェック.

        Args:
            current_value: 現在の測定値
            metric_path: メトリクスのパス（例: "single.quantforge"）

        Returns:
            (退行なし, メッセージ)
        """
        if not self.baseline_data:
            return True, "ベースラインが存在しません"

        category, metric = metric_path.split(".")

        if category not in self.baseline_data["thresholds"]:
            return True, f"カテゴリ '{category}' がベースラインに存在しません"

        if metric not in self.baseline_data["thresholds"][category]:
            return True, f"メトリクス '{metric}' がベースラインに存在しません"

        baseline_info = self.baseline_data["thresholds"][category][metric]
        threshold = baseline_info["threshold_mean"]
        baseline_mean = baseline_info["mean"]

        if current_value <= threshold:
            improvement = (baseline_mean - current_value) / baseline_mean * 100
            if improvement > 0:
                return True, (
                    f"✅ ベースライン内 (現在: {current_value:.6f}, "
                    f"ベースライン: {baseline_mean:.6f}, {improvement:.1f}%改善)"
                )
            else:
                return True, f"✅ ベースライン内 (現在: {current_value:.6f}, 閾値: {threshold:.6f})"
        else:
            regression = (current_value - baseline_mean) / baseline_mean * 100
            return False, (
                f"❌ 退行検出! (現在: {current_value:.6f}, ベースライン: {baseline_mean:.6f}, {regression:.1f}%劣化)"
            )


def main() -> None:
    """ベースライン更新のメインエントリポイント."""
    import argparse

    parser = argparse.ArgumentParser(description="パフォーマンスベースライン管理")
    parser.add_argument("--update", action="store_true", help="ベースラインを更新")
    parser.add_argument("--check", action="store_true", help="現在の性能をチェック")
    parser.add_argument("--runs", type=int, default=5, help="測定回数（デフォルト: 5）")
    parser.add_argument("--buffer", type=float, default=1.2, help="バッファ係数（デフォルト: 1.2 = 20%）")

    args = parser.parse_args()

    manager = BaselineManager()

    if args.update:
        print(f"ベースライン更新を開始します（{args.runs}回測定、バッファ係数: {args.buffer}）")
        measurements = manager.collect_measurements(num_runs=args.runs)
        baseline = manager.calculate_baseline(measurements, buffer_factor=args.buffer)

        # 統計情報を表示
        print("\n=== ベースライン統計 ===")
        for category, metrics in baseline["thresholds"].items():
            print(f"\n{category}:")
            for metric, stats in metrics.items():
                print(f"  {metric}:")
                print(f"    平均: {stats['mean']:.6e} (±{stats['stdev']:.6e})")
                print(f"    P95: {stats['p95']:.6e}")
                print(f"    閾値: {stats['threshold_mean']:.6e}")

        print("\n速度比:")
        for key, value in baseline["speedup_ratios"].items():
            print(f"  {key}: {value:.2f}x")

        manager.save_baseline(baseline)

    elif args.check:
        # 現在の性能をチェック
        print("現在の性能をチェック中...")
        subprocess.run(["uv", "run", "python", "-m", "benchmarks.runners.comparison"], check=True)

        with open("benchmarks/results/latest.json") as f:
            latest = json.load(f)

        print("\n=== 退行チェック ===")

        # 単一計算のチェック
        ok, msg = manager.check_regression(latest["single"]["quantforge"], "single.quantforge")
        print(f"単一計算 (QuantForge): {msg}")

        # バッチ処理のチェック
        for batch in latest["batch"]:
            if batch["size"] == 1000000:
                ok, msg = manager.check_regression(batch["quantforge"], "batch_1m.quantforge")
                print(f"100万件バッチ (QuantForge): {msg}")
                break

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
