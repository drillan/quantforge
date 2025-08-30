"""ベンチマーク基底クラスと共通機能."""

import platform
import time
from abc import ABC, abstractmethod
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, TypeVar

import numpy as np
import psutil
from numpy.typing import NDArray

T = TypeVar("T")


@dataclass
class TimingResult:
    """ベンチマーク測定結果."""

    median: float
    mean: float
    std: float
    min: float
    max: float
    samples: int

    @classmethod
    def from_times(cls, times: list[float]) -> "TimingResult":
        """時間測定リストから結果を生成."""
        arr = np.array(times)
        return cls(
            median=float(np.median(arr)),
            mean=float(np.mean(arr)),
            std=float(np.std(arr)),
            min=float(np.min(arr)),
            max=float(np.max(arr)),
            samples=len(times),
        )


class BenchmarkBase(ABC):
    """ベンチマーク実行の基底クラス."""

    def __init__(
        self,
        warmup_runs: int = 100,
        measure_runs: int = 1000,
        timeout: float | None = None,
    ):
        """初期化.

        Args:
            warmup_runs: ウォームアップ実行回数
            measure_runs: 測定実行回数
            timeout: タイムアウト秒数（None=無制限）
        """
        self.warmup_runs = warmup_runs
        self.measure_runs = measure_runs
        self.timeout = timeout
        self._start_time: float | None = None

    def get_system_info(self) -> dict[str, Any]:
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

    def time_function(
        self,
        func: Callable[[], T],
        warmup_runs: int | None = None,
        measure_runs: int | None = None,
    ) -> TimingResult:
        """関数の実行時間を測定.

        Args:
            func: 測定対象の関数
            warmup_runs: ウォームアップ回数（Noneなら初期値）
            measure_runs: 測定回数（Noneなら初期値）

        Returns:
            測定結果
        """
        warmup = warmup_runs or self.warmup_runs
        measure = measure_runs or self.measure_runs

        # ウォームアップ
        for _ in range(warmup):
            func()

        # 測定
        times = []
        for _ in range(measure):
            if self._check_timeout():
                break

            start = time.perf_counter()
            func()
            elapsed = time.perf_counter() - start
            times.append(elapsed)

        return TimingResult.from_times(times)

    def time_batch_function(
        self,
        func: Callable[[NDArray[np.float64]], NDArray[np.float64]],
        data: NDArray[np.float64],
        warmup_runs: int = 10,
        measure_runs: int = 100,
    ) -> TimingResult:
        """バッチ処理関数の実行時間を測定.

        Args:
            func: 測定対象の関数
            data: 入力データ
            warmup_runs: ウォームアップ回数
            measure_runs: 測定回数

        Returns:
            測定結果
        """
        # ウォームアップ
        for _ in range(warmup_runs):
            func(data)

        # 測定
        times = []
        for _ in range(measure_runs):
            if self._check_timeout():
                break

            start = time.perf_counter()
            func(data)
            elapsed = time.perf_counter() - start
            times.append(elapsed)

        return TimingResult.from_times(times)

    def start_benchmark(self) -> None:
        """ベンチマーク開始時刻を記録."""
        self._start_time = time.time()

    def _check_timeout(self) -> bool:
        """タイムアウトチェック."""
        if self.timeout is None or self._start_time is None:
            return False
        return (time.time() - self._start_time) > self.timeout

    @abstractmethod
    def run(self) -> dict[str, Any]:
        """ベンチマークを実行.

        Returns:
            実行結果の辞書
        """
        ...
