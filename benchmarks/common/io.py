"""ベンチマーク結果の入出力機能."""

import csv
import json
from datetime import datetime
from pathlib import Path
from typing import Any, cast


class BenchmarkIO:
    """ベンチマーク結果の入出力を管理."""

    def __init__(self, base_dir: Path | None = None):
        """初期化.

        Args:
            base_dir: 結果を保存するベースディレクトリ
        """
        if base_dir is None:
            # デフォルトはプロジェクトルート/benchmarks/results
            base_dir = Path(__file__).resolve().parent.parent.parent / "benchmarks" / "results"
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def save_result(
        self,
        results: dict[str, Any],
        name: str | None = None,
        save_history: bool = True,
    ) -> Path:
        """ベンチマーク結果を保存.

        Args:
            results: 保存する結果
            name: ファイル名（Noneの場合はlatest.json）
            save_history: 履歴も保存するか

        Returns:
            保存したファイルのパス
        """
        # タイムスタンプを追加
        results["timestamp"] = datetime.now().isoformat()

        # 最新結果を保存
        latest_file = self.base_dir / "latest.json" if name is None else self.base_dir / f"{name}.json"

        with open(latest_file, "w") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)

        # 履歴に追記
        if save_history:
            history_file = self.base_dir / "history.jsonl"
            with open(history_file, "a") as f:
                json.dump(results, f, ensure_ascii=False)
                f.write("\n")

        return latest_file

    def load_latest(self, name: str | None = None) -> dict[str, Any]:
        """最新の結果を読み込み.

        Args:
            name: ファイル名（Noneの場合はlatest.json）

        Returns:
            結果の辞書

        Raises:
            FileNotFoundError: ファイルが存在しない場合
        """
        latest_file = self.base_dir / "latest.json" if name is None else self.base_dir / f"{name}.json"

        if not latest_file.exists():
            raise FileNotFoundError(f"Result file not found: {latest_file}")

        with open(latest_file) as f:
            return cast("dict[str, Any]", json.load(f))

    def load_history(self) -> list[dict[str, Any]]:
        """履歴データを読み込み.

        Returns:
            結果のリスト
        """
        history_file = self.base_dir / "history.jsonl"
        if not history_file.exists():
            return []

        results = []
        with open(history_file) as f:
            for line in f:
                if line.strip():
                    results.append(json.loads(line))
        return results

    def export_to_csv(
        self,
        output_file: Path | None = None,
        results: list[dict[str, Any]] | None = None,
    ) -> Path:
        """結果をCSV形式でエクスポート.

        Args:
            output_file: 出力ファイルパス（Noneの場合は自動生成）
            results: エクスポートする結果（Noneの場合は履歴全体）

        Returns:
            出力したファイルのパス
        """
        if output_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = self.base_dir / f"benchmark_results_{timestamp}.csv"
        else:
            output_file = Path(output_file)

        if results is None:
            results = self.load_history()

        if not results:
            raise ValueError("No results to export")

        # CSVのヘッダーを決定
        headers: set[str] = set()
        for result in results:
            headers.update(self._flatten_dict(result).keys())
        headers_list = sorted(headers)

        # CSV書き込み
        with open(output_file, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=headers_list)
            writer.writeheader()

            for result in results:
                flat_result = self._flatten_dict(result)
                writer.writerow(flat_result)

        return output_file

    def compare_results(
        self,
        baseline: dict[str, Any] | None = None,
        current: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """2つの結果を比較.

        Args:
            baseline: 基準となる結果（Noneの場合は前回の結果）
            current: 比較する結果（Noneの場合は最新の結果）

        Returns:
            比較結果の辞書
        """
        if current is None:
            current = self.load_latest()

        if baseline is None:
            history = self.load_history()
            if len(history) < 2:
                raise ValueError("Not enough history for comparison")
            baseline = history[-2]

        comparison: dict[str, Any] = {
            "baseline_timestamp": baseline.get("timestamp"),
            "current_timestamp": current.get("timestamp"),
            "improvements": {},
            "regressions": {},
            "unchanged": {},
        }

        # 単一計算の比較
        if "single" in baseline and "single" in current:
            for key in baseline["single"]:
                if key in current["single"] and not key.startswith("speedup_"):
                    baseline_val = baseline["single"][key]
                    current_val = current["single"][key]
                    change = (baseline_val - current_val) / baseline_val * 100

                    result = {
                        "baseline": baseline_val,
                        "current": current_val,
                        "change_percent": change,
                    }

                    if abs(change) < 1:
                        comparison["unchanged"][f"single_{key}"] = result
                    elif change > 0:
                        comparison["improvements"][f"single_{key}"] = result
                    else:
                        comparison["regressions"][f"single_{key}"] = result

        return comparison

    @staticmethod
    def _flatten_dict(d: dict[str, Any], parent_key: str = "", sep: str = "_") -> dict[str, Any]:
        """辞書をフラット化.

        Args:
            d: フラット化する辞書
            parent_key: 親キー
            sep: セパレータ

        Returns:
            フラット化された辞書
        """
        items: list[tuple[str, Any]] = []
        for k, v in d.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            if isinstance(v, dict):
                items.extend(BenchmarkIO._flatten_dict(v, new_key, sep=sep).items())
            elif isinstance(v, list):
                for i, item in enumerate(v):
                    if isinstance(item, dict):
                        items.extend(BenchmarkIO._flatten_dict(item, f"{new_key}_{i}", sep=sep).items())
                    else:
                        items.append((f"{new_key}_{i}", item))
            else:
                items.append((new_key, v))
        return dict(items)
