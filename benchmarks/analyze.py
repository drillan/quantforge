"""ベンチマーク履歴の分析ツール."""

import json
from pathlib import Path
from typing import Any, Optional
from datetime import datetime


def analyze_performance_trends() -> dict[str, Any]:
    """パフォーマンストレンドを分析."""
    from save_results import load_history
    
    history = load_history()
    if len(history) < 2:
        return {"error": "Insufficient data for trend analysis"}
    
    # 最新と前回の結果を比較
    latest = history[-1]
    previous = history[-2]
    
    trends = {
        "timestamp": latest["timestamp"],
        "comparisons": {},
        "regressions": [],
        "improvements": []
    }
    
    # 単一計算の比較
    if "single" in latest and "single" in previous:
        for impl in ["quantforge", "scipy", "pure_python"]:
            if impl in latest["single"] and impl in previous["single"]:
                current = latest["single"][impl]
                prev = previous["single"][impl]
                change = ((current - prev) / prev) * 100
                
                trends["comparisons"][f"single_{impl}"] = {
                    "current": current,
                    "previous": prev,
                    "change_percent": change
                }
                
                # 5%以上の性能劣化を検出
                if impl == "quantforge" and change > 5:
                    trends["regressions"].append(f"QuantForge single: {change:.1f}% slower")
                elif impl == "quantforge" and change < -5:
                    trends["improvements"].append(f"QuantForge single: {abs(change):.1f}% faster")
    
    return trends


def generate_summary_table() -> str:
    """最新結果のサマリーテーブルを生成."""
    latest_file = Path("results/latest.json")
    if not latest_file.exists():
        return "No benchmark results found"
    
    with open(latest_file) as f:
        data = json.load(f)
    
    lines = []
    lines.append("## Benchmark Summary\n")
    lines.append(f"Date: {data['system_info']['timestamp']}\n")
    lines.append(f"CPU: {data['system_info']['processor']}\n")
    lines.append("")
    
    # Single calculation results
    if "single" in data:
        lines.append("### Single Calculation")
        lines.append("| Implementation | Time (μs) | Speedup |")
        lines.append("|---------------|-----------|---------|")
        
        qf_time = data["single"]["quantforge"] * 1e6
        for impl, name in [("quantforge", "QuantForge"),
                           ("pure_python", "Pure Python"),
                           ("scipy", "SciPy")]:
            if impl in data["single"]:
                time_us = data["single"][impl] * 1e6
                speedup = time_us / qf_time if impl != "quantforge" else 1.0
                lines.append(f"| {name} | {time_us:.2f} | {speedup:.1f}x |")
    
    lines.append("")
    
    # Batch processing results
    if "batch" in data:
        lines.append("### Batch Processing (1M items)")
        for batch in data["batch"]:
            if batch["size"] == 1000000:
                qf_ms = batch["quantforge"] * 1000
                np_ms = batch["numpy_batch"] * 1000
                throughput = batch["throughput_qf"] / 1e6
                
                lines.append(f"- QuantForge: {qf_ms:.1f} ms")
                lines.append(f"- NumPy: {np_ms:.1f} ms")
                lines.append(f"- Throughput: {throughput:.1f}M ops/sec")
                break
    
    return "\n".join(lines)


def plot_history(output_file: str = "results/performance_history.png") -> None:
    """パフォーマンス履歴をプロット."""
    try:
        import matplotlib.pyplot as plt
        import matplotlib.dates as mdates
    except ImportError:
        print("matplotlib not installed. Skipping plot generation.")
        return
    
    from save_results import load_history
    
    history = load_history()
    if len(history) < 2:
        print("Insufficient data for plotting")
        return
    
    # データを抽出
    timestamps = []
    qf_single = []
    qf_batch = []
    
    for result in history:
        timestamps.append(datetime.fromisoformat(result["timestamp"]))
        qf_single.append(result["single"]["quantforge"] * 1e6)  # μs
        
        for batch in result["batch"]:
            if batch["size"] == 1000000:
                qf_batch.append(batch["quantforge"] * 1000)  # ms
                break
    
    # プロット
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8))
    
    # Single calculation
    ax1.plot(timestamps, qf_single, marker='o', label='QuantForge')
    ax1.set_xlabel('Date')
    ax1.set_ylabel('Time (μs)')
    ax1.set_title('Single Calculation Performance')
    ax1.grid(True, alpha=0.3)
    ax1.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
    plt.setp(ax1.xaxis.get_majorticklabels(), rotation=45)
    
    # Batch processing
    if qf_batch:
        ax2.plot(timestamps[:len(qf_batch)], qf_batch, marker='s', color='green', label='1M Batch')
        ax2.set_xlabel('Date')
        ax2.set_ylabel('Time (ms)')
        ax2.set_title('Batch Processing Performance (1M items)')
        ax2.grid(True, alpha=0.3)
        ax2.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        plt.setp(ax2.xaxis.get_majorticklabels(), rotation=45)
    
    plt.tight_layout()
    plt.savefig(output_file, dpi=150, bbox_inches='tight')
    print(f"✅ Plot saved to {output_file}")


if __name__ == "__main__":
    # 分析実行
    print(generate_summary_table())
    
    trends = analyze_performance_trends()
    if "error" not in trends:
        print("\n## Performance Trends")
        if trends["regressions"]:
            print("⚠️ Regressions detected:")
            for reg in trends["regressions"]:
                print(f"  - {reg}")
        if trends["improvements"]:
            print("✅ Improvements:")
            for imp in trends["improvements"]:
                print(f"  - {imp}")
    
    # プロット生成
    plot_history()