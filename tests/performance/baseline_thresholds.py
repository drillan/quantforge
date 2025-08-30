"""ベースライン駆動パフォーマンス閾値システム.

破壊的変更：後方互換性なし、ベースライン必須。
"""

import json
from pathlib import Path
from typing import Any


class BaselineThresholds:
    """ベースライン駆動の閾値管理（理想実装）."""

    # 定数（ハードコード禁止原則）
    BASELINE_FILE = Path("benchmarks/results/baseline.json")
    BUFFER_FACTOR = 1.2  # 20%マージン

    def __init__(self) -> None:
        """初期化. ベースラインが無ければエラー."""
        self.baseline_data = self._load_baseline_or_fail()

    def _load_baseline_or_fail(self) -> dict[str, Any]:
        """ベースラインを読み込む. 無ければエラー."""
        if not self.BASELINE_FILE.exists():
            raise RuntimeError(
                f"ベースラインが存在しません: {self.BASELINE_FILE}\n"
                "実行: uv run python benchmarks/baseline_manager.py --update"
            )

        try:
            with open(self.BASELINE_FILE) as f:
                data: dict[str, Any] = json.load(f)
                return data
        except (OSError, json.JSONDecodeError) as e:
            raise RuntimeError(f"ベースライン読み込みエラー: {e}") from e

    def get_threshold(self, metric_category: str, metric_name: str) -> tuple[float, float]:
        """閾値を取得.

        Args:
            metric_category: カテゴリ（"single", "batch_1m"等）
            metric_name: メトリクス名（"quantforge", "numpy_batch"等）

        Returns:
            (ベースライン平均, 閾値)
        """
        try:
            metrics = self.baseline_data["thresholds"][metric_category][metric_name]
            baseline_mean = metrics["mean"]
            threshold = baseline_mean * self.BUFFER_FACTOR
            return baseline_mean, threshold
        except KeyError as e:
            raise RuntimeError(
                f"ベースラインにメトリクスが存在しません: {metric_category}.{metric_name}\nベースライン更新が必要: {e}"
            ) from e

    def assert_performance(
        self, metric_category: str, metric_name: str, measured_time: float, test_name: str = ""
    ) -> None:
        """パフォーマンスアサーション.

        Args:
            metric_category: カテゴリ
            metric_name: メトリクス名
            measured_time: 測定時間
            test_name: テスト名（エラーメッセージ用）
        """
        baseline_mean, threshold = self.get_threshold(metric_category, metric_name)

        if measured_time > threshold:
            degradation = (measured_time - baseline_mean) / baseline_mean * 100
            raise AssertionError(
                f"{test_name}: 性能劣化検出！\n"
                f"  測定値: {measured_time:.6f}秒\n"
                f"  ベースライン: {baseline_mean:.6f}秒\n"
                f"  劣化率: {degradation:.1f}%\n"
                f"  許容閾値: {threshold:.6f}秒（+20%）"
            )

        # 改善の場合はログ出力（オプション）
        if measured_time < baseline_mean:
            improvement = (baseline_mean - measured_time) / baseline_mean * 100
            print(f"  ✅ {test_name}: {improvement:.1f}%改善")


# グローバルインスタンス（シングルトン）
_instance = None


def get_thresholds() -> BaselineThresholds:
    """シングルトンインスタンスを取得."""
    global _instance
    if _instance is None:
        _instance = BaselineThresholds()
    return _instance
