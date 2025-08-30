"""ベンチマーク結果を構造化データとして保存."""

import json
from datetime import datetime
from pathlib import Path
from typing import Any

# プロジェクトルートからの相対パスでresultsディレクトリを定義
# このファイルは benchmarks/analysis/save.py にあるので、2階層上がプロジェクトルート
BASE_DIR = Path(__file__).resolve().parent.parent.parent
RESULTS_DIR = BASE_DIR / "benchmarks" / "results"


def save_benchmark_result(results: dict[str, Any]) -> None:
    """ベンチマーク結果をJSON Lines形式で保存."""
    # resultsディレクトリを作成
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    # タイムスタンプを追加
    results["timestamp"] = datetime.now().isoformat()

    # JSON Linesファイルに追記
    history_file = RESULTS_DIR / "history.jsonl"
    with open(history_file, "a") as f:
        json.dump(results, f, ensure_ascii=False)
        f.write("\n")

    # 最新結果を別ファイルに保存（クイックアクセス用）
    latest_file = RESULTS_DIR / "latest.json"
    with open(latest_file, "w") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"✅ Results saved to {history_file}")


def load_history() -> list[dict[str, Any]]:
    """履歴データを読み込み."""
    history_file = RESULTS_DIR / "history.jsonl"
    if not history_file.exists():
        return []

    results = []
    with open(history_file) as f:
        for line in f:
            if line.strip():
                results.append(json.loads(line))
    return results


def export_to_csv(output_file: str | None = None) -> None:
    """履歴をCSV形式でエクスポート."""
    import csv

    if output_file is None:
        output_file = str(RESULTS_DIR / "history.csv")

    history = load_history()
    if not history:
        print("No history found")
        return

    # CSVヘッダーを構築
    fieldnames = [
        "timestamp",
        "cpu",
        "cpu_count",
        "memory_gb",
        "single_quantforge_us",
        "single_scipy_us",
        "single_pure_python_us",
        "batch_1m_quantforge_ms",
        "batch_1m_numpy_ms",
        "throughput_mops",
    ]

    with open(output_file, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for result in history:
            row = {
                "timestamp": result.get("timestamp", ""),
                "cpu": result.get("system_info", {}).get("processor", ""),
                "cpu_count": result.get("system_info", {}).get("cpu_count", ""),
                "memory_gb": result.get("system_info", {}).get("memory_gb", ""),
                "single_quantforge_us": result.get("single", {}).get("quantforge", 0) * 1e6,
                "single_scipy_us": result.get("single", {}).get("scipy", 0) * 1e6,
                "single_pure_python_us": result.get("single", {}).get("pure_python", 0) * 1e6,
            }

            # 100万件バッチのデータを探す
            for batch in result.get("batch", []):
                if batch.get("size") == 1000000:
                    row["batch_1m_quantforge_ms"] = batch.get("quantforge", 0) * 1000
                    row["batch_1m_numpy_ms"] = batch.get("numpy_batch", 0) * 1000
                    row["throughput_mops"] = batch.get("throughput_qf", 0) / 1e6
                    break

            writer.writerow(row)

    print(f"✅ Exported to {output_file}")


if __name__ == "__main__":
    # 既存のresults.jsonを履歴に追加
    if Path("benchmark_results.json").exists():
        with open("benchmark_results.json") as f:
            results = json.load(f)
        save_benchmark_result(results)

    # CSV出力テスト
    export_to_csv()
