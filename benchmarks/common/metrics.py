"""ベンチマークメトリクス計算."""


import numpy as np
from numpy.typing import NDArray


def calculate_speedup(
    baseline_time: float,
    current_time: float,
    precision: int = 2,
) -> float:
    """高速化率を計算.

    Args:
        baseline_time: 基準となる実行時間
        current_time: 比較する実行時間
        precision: 小数点以下の桁数

    Returns:
        高速化率（baseline_time / current_time）
    """
    if current_time <= 0:
        raise ValueError("Current time must be positive")
    if baseline_time <= 0:
        raise ValueError("Baseline time must be positive")

    speedup = baseline_time / current_time
    return round(speedup, precision)


def calculate_throughput(
    operations: int | float,
    time_seconds: float,
    unit: str = "ops",
) -> float:
    """スループットを計算.

    Args:
        operations: 操作数
        time_seconds: 実行時間（秒）
        unit: 単位（デフォルトは"ops"）

    Returns:
        秒あたりの操作数
    """
    if time_seconds <= 0:
        raise ValueError("Time must be positive")
    if operations <= 0:
        raise ValueError("Operations must be positive")

    return operations / time_seconds


def calculate_efficiency(
    speedup: float,
    num_cores: int,
    precision: int = 2,
) -> float:
    """並列化効率を計算.

    Args:
        speedup: 実測の高速化率
        num_cores: 使用コア数
        precision: 小数点以下の桁数

    Returns:
        並列化効率（0-1の値、1が理想的）
    """
    if num_cores <= 0:
        raise ValueError("Number of cores must be positive")

    efficiency = speedup / num_cores
    return round(min(efficiency, 1.0), precision)


def calculate_relative_error(
    expected: float | NDArray[np.float64],
    actual: float | NDArray[np.float64],
    epsilon: float = 1e-10,
) -> float | NDArray[np.float64]:
    """相対誤差を計算.

    Args:
        expected: 期待値
        actual: 実測値
        epsilon: ゼロ除算回避用の小さな値

    Returns:
        相対誤差
    """
    expected_arr = np.asarray(expected)
    actual_arr = np.asarray(actual)

    abs_expected = np.abs(expected_arr)
    # ゼロ除算を回避
    denominator = np.where(abs_expected > epsilon, abs_expected, epsilon)

    return np.abs(actual_arr - expected_arr) / denominator


def calculate_percentile_times(
    times: list[float],
    percentiles: list[float] | None = None,
) -> dict[str, float]:
    """パーセンタイル時間を計算.

    Args:
        times: 実行時間のリスト
        percentiles: 計算するパーセンタイル（デフォルト: [50, 90, 95, 99]）

    Returns:
        パーセンタイルごとの時間
    """
    if not times:
        raise ValueError("Times list cannot be empty")

    if percentiles is None:
        percentiles = [50, 90, 95, 99]

    arr = np.array(times)
    results = {}

    for p in percentiles:
        if not 0 <= p <= 100:
            raise ValueError(f"Percentile must be between 0 and 100, got {p}")
        results[f"p{int(p)}"] = float(np.percentile(arr, p))

    return results


def calculate_statistics(times: list[float]) -> dict[str, float]:
    """時間測定の統計情報を計算.

    Args:
        times: 実行時間のリスト

    Returns:
        統計情報の辞書
    """
    if not times:
        raise ValueError("Times list cannot be empty")

    arr = np.array(times)

    return {
        "mean": float(np.mean(arr)),
        "median": float(np.median(arr)),
        "std": float(np.std(arr)),
        "min": float(np.min(arr)),
        "max": float(np.max(arr)),
        "cv": float(np.std(arr) / np.mean(arr)) if np.mean(arr) > 0 else 0,  # 変動係数
    }


def is_statistically_significant(
    sample1: list[float],
    sample2: list[float],
    alpha: float = 0.05,
) -> tuple[bool, float]:
    """2つのサンプルが統計的に有意な差があるか検定.

    Mann-Whitney U検定を使用（正規分布を仮定しない）。

    Args:
        sample1: サンプル1
        sample2: サンプル2
        alpha: 有意水準

    Returns:
        (有意差があるか, p値)
    """
    try:
        from scipy import stats
    except ImportError:
        # SciPyが利用できない場合は簡易的な判定
        mean1 = np.mean(sample1)
        mean2 = np.mean(sample2)
        std1 = np.std(sample1)
        std2 = np.std(sample2)

        # 簡易的な判定（平均値の差が標準偏差の2倍以上）
        diff = abs(mean1 - mean2)
        threshold = 2 * max(std1, std2)
        return diff > threshold, 0.0

    # Mann-Whitney U検定
    statistic, p_value = stats.mannwhitneyu(sample1, sample2, alternative="two-sided")
    return p_value < alpha, float(p_value)


def estimate_optimal_batch_size(
    batch_sizes: list[int],
    times: list[float],
) -> int:
    """最適なバッチサイズを推定.

    スループットが最大となるバッチサイズを見つける。

    Args:
        batch_sizes: バッチサイズのリスト
        times: 各バッチサイズでの実行時間

    Returns:
        最適なバッチサイズ
    """
    if len(batch_sizes) != len(times):
        raise ValueError("Batch sizes and times must have the same length")
    if not batch_sizes:
        raise ValueError("Batch sizes cannot be empty")

    # スループットを計算
    throughputs = [size / time for size, time in zip(batch_sizes, times, strict=False)]

    # 最大スループットのインデックス
    max_idx = np.argmax(throughputs)
    return batch_sizes[max_idx]
