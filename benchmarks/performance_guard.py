"""パフォーマンスガード - CI/CD統合用の退行検出システム."""

import json
import sys
from pathlib import Path

from baseline_manager import BaselineManager


class PerformanceGuard:
    """パフォーマンス退行を検出し、品質を保証."""

    def __init__(self) -> None:
        self.manager = BaselineManager()
        self.violations: list[str] = []
        self.warnings: list[str] = []

    def check_all_metrics(self) -> bool:
        """全メトリクスをチェックして退行を検出.

        Returns:
            True: 退行なし、False: 退行検出
        """
        # 最新の測定結果を読み込み
        latest_path = Path("benchmarks/results/latest.json")
        if not latest_path.exists():
            print("❌ 最新の測定結果が見つかりません")
            return False

        with open(latest_path) as f:
            latest = json.load(f)

        # ベースラインが存在しない場合は警告のみ
        if not self.manager.baseline_data:
            self.warnings.append("⚠️ ベースラインが存在しません。`--update-baseline`で作成してください")
            return True

        # チェック項目の定義
        checks = [
            # 単一計算
            ("single.quantforge", latest["single"]["quantforge"], "単一計算(QuantForge)"),
            ("single.pure_python", latest["single"]["pure_python"], "単一計算(Pure Python)"),
            ("single.numpy_scipy", latest["single"]["numpy_scipy"], "単一計算(NumPy+SciPy)"),
        ]

        # バッチ処理のチェック項目を追加
        for batch in latest["batch"]:
            size = batch["size"]
            if size in [100, 1000, 10000, 100000, 1000000]:
                category = f"batch_{size}"

                # QuantForgeの性能チェック
                if "quantforge" in batch:
                    checks.append((f"{category}.quantforge", batch["quantforge"], f"{size:,}件バッチ(QuantForge)"))

                # NumPyとの比較（1万件以上）
                if size >= 10000 and "numpy_batch" in batch:
                    checks.append((f"{category}.numpy_batch", batch["numpy_batch"], f"{size:,}件バッチ(NumPy)"))

        # 各メトリクスをチェック
        all_passed = True
        for metric_path, current_value, description in checks:
            passed, message = self.check_metric(metric_path, current_value, description)
            if not passed:
                all_passed = False

        return all_passed

    def check_metric(self, metric_path: str, current_value: float, description: str) -> tuple[bool, str]:
        """個別メトリクスのチェック.

        Args:
            metric_path: メトリクスパス（例: "single.quantforge"）
            current_value: 現在の測定値
            description: 人間が読める説明

        Returns:
            (合格, メッセージ)
        """
        category, metric = metric_path.split(".")

        # ベースラインデータの取得
        if category not in self.manager.baseline_data["thresholds"]:
            # 新しいメトリクス（ベースラインにない）
            self.warnings.append(f"⚠️ {description}: 新規メトリクス（ベースライン未設定）")
            return True, "新規メトリクス"

        if metric not in self.manager.baseline_data["thresholds"][category]:
            self.warnings.append(f"⚠️ {description}: 新規メトリクス（ベースライン未設定）")
            return True, "新規メトリクス"

        baseline_info = self.manager.baseline_data["thresholds"][category][metric]
        baseline_mean = baseline_info["mean"]
        threshold = baseline_info["threshold_mean"]

        # 性能評価
        if current_value <= threshold:
            # 閾値内
            if current_value < baseline_mean:
                # 改善
                improvement = (baseline_mean - current_value) / baseline_mean * 100
                message = f"✅ {description}: {improvement:.1f}%改善"
                print(message)
            else:
                # わずかな劣化（許容範囲内）
                degradation = (current_value - baseline_mean) / baseline_mean * 100
                message = f"✅ {description}: 許容範囲内（{degradation:.1f}%）"
                print(message)
            return True, message
        else:
            # 閾値超過 - 退行
            degradation = (current_value - baseline_mean) / baseline_mean * 100
            message = f"❌ {description}: {degradation:.1f}%劣化（閾値超過）"
            self.violations.append(message)
            print(message)
            return False, message

    def generate_report(self) -> str:
        """詳細レポートを生成."""
        report = [""]
        report.append("=" * 60)
        report.append("パフォーマンスガード レポート")
        report.append("=" * 60)

        if self.violations:
            report.append("\n【退行検出】")
            for violation in self.violations:
                report.append(f"  {violation}")

        if self.warnings:
            report.append("\n【警告】")
            for warning in self.warnings:
                report.append(f"  {warning}")

        if not self.violations and not self.warnings:
            report.append("\n✅ すべてのチェックに合格しました")

        # 速度比の確認
        if self.manager.baseline_data and "speedup_ratios" in self.manager.baseline_data:
            report.append("\n【ベースライン速度比】")
            for key, value in self.manager.baseline_data["speedup_ratios"].items():
                report.append(f"  {key}: {value:.2f}x")

        report.append("=" * 60)
        return "\n".join(report)


def main() -> None:
    """メインエントリポイント."""
    import argparse

    parser = argparse.ArgumentParser(description="パフォーマンス退行検出")
    parser.add_argument("--strict", action="store_true", help="警告もエラーとして扱う")
    parser.add_argument("--update-baseline", action="store_true", help="ベースラインを更新")

    args = parser.parse_args()

    if args.update_baseline:
        # ベースライン更新モード
        from baseline_manager import main as baseline_main

        sys.argv = ["baseline_manager.py", "--update", "--runs", "5", "--buffer", "1.2"]
        baseline_main()
        return

    # パフォーマンスチェック
    guard = PerformanceGuard()
    passed = guard.check_all_metrics()

    # レポート出力
    print(guard.generate_report())

    # 終了コードの決定
    if not passed:
        sys.exit(1)  # 退行検出
    elif args.strict and guard.warnings:
        sys.exit(2)  # 警告（strictモード）
    else:
        sys.exit(0)  # 成功


if __name__ == "__main__":
    main()
