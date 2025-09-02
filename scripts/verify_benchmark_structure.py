#!/usr/bin/env python3
"""新しいベンチマーク構造の検証スクリプト"""

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


def check_directory_structure() -> dict[str, bool]:
    """ディレクトリ構造の確認"""
    checks = {
        "core_benches": Path("core/benches").exists(),
        "bindings_benchmarks": Path("bindings/python/tests/benchmarks").exists(),
        "performance_tests": Path("tests/performance").exists(),
        "results_dir": Path("benchmark_results").exists(),
        "core_results": Path("benchmark_results/core").exists(),
        "bindings_results": Path("benchmark_results/bindings/python").exists(),
        "integration_results": Path("benchmark_results/integration").exists(),
    }

    # historyディレクトリの確認
    for layer in ["core", "bindings/python", "integration"]:
        history_key = f"{layer.replace('/', '_')}_history"
        checks[history_key] = Path(f"benchmark_results/{layer}/history").exists()

    return checks


def check_new_format_data() -> dict[str, Any]:
    """新形式データの存在確認"""
    results = {"has_data": False, "layers": {}, "format_version": None}

    layers = ["core", "bindings/python", "integration"]

    for layer in layers:
        latest_path = Path(f"benchmark_results/{layer}/latest.json")
        if latest_path.exists():
            results["has_data"] = True
            try:
                with open(latest_path) as f:
                    data = json.load(f)
                    results["layers"][layer] = {
                        "exists": True,
                        "version": data.get("version", "unknown"),
                        "layer": data.get("layer", "unknown"),
                        "timestamp": data.get("metadata", {}).get("timestamp", "unknown"),
                    }
                    if not results["format_version"]:
                        results["format_version"] = data.get("version")
            except Exception as e:
                results["layers"][layer] = {"exists": True, "error": str(e)}
        else:
            results["layers"][layer] = {"exists": False}

    return results


def check_old_structure() -> dict[str, Any]:
    """旧構造の確認"""
    old_benchmarks = Path("benchmarks")

    result = {"exists": old_benchmarks.exists(), "has_results": False, "result_files": [], "total_size": 0}

    if old_benchmarks.exists():
        results_dir = old_benchmarks / "results"
        if results_dir.exists():
            result["has_results"] = True
            result["result_files"] = [f.name for f in results_dir.glob("*.json")][:10]  # 最初の10ファイルのみ

            # サイズ計算
            for f in results_dir.rglob("*"):
                if f.is_file():
                    result["total_size"] += f.stat().st_size

    return result


def check_benchmark_code() -> dict[str, Any]:
    """ベンチマークコードの存在確認"""
    checks = {}

    # Core層のベンチマーク
    core_benches = Path("core/benches")
    if core_benches.exists():
        rust_files = list(core_benches.glob("*.rs"))
        checks["core"] = {"exists": True, "files": [f.name for f in rust_files], "count": len(rust_files)}
    else:
        checks["core"] = {"exists": False}

    # Bindings層のベンチマーク
    bindings_bench = Path("bindings/python/tests/benchmarks")
    if bindings_bench.exists():
        py_files = list(bindings_bench.glob("*.py"))
        checks["bindings"] = {
            "exists": True,
            "files": [f.name for f in py_files if f.name != "__init__.py"],
            "count": len([f for f in py_files if f.name != "__init__.py"]),
        }
    else:
        checks["bindings"] = {"exists": False}

    # Integration層のベンチマーク
    integration_bench = Path("tests/performance")
    if integration_bench.exists():
        py_files = list(integration_bench.glob("*.py"))
        checks["integration"] = {"exists": True, "files": [f.name for f in py_files], "count": len(py_files)}
    else:
        checks["integration"] = {"exists": False}

    return checks


def format_size(size_bytes: int) -> str:
    """バイトサイズを人間が読みやすい形式に変換"""
    for unit in ["B", "KB", "MB", "GB"]:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} TB"


def print_report(all_checks: dict[str, Any]) -> bool:
    """検証結果のレポート出力"""
    print("\n" + "=" * 60)
    print("ベンチマーク構造検証レポート")
    print("=" * 60)
    print(f"実行日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # ディレクトリ構造
    print("\n📁 ディレクトリ構造:")
    dir_checks = all_checks["directory"]
    all_dirs_ok = True
    for name, exists in dir_checks.items():
        status = "✅" if exists else "❌"
        print(f"  {status} {name}: {exists}")
        if not exists:
            all_dirs_ok = False

    # ベンチマークコード
    print("\n📝 ベンチマークコード:")
    code_checks = all_checks["code"]
    for layer, info in code_checks.items():
        if info["exists"]:
            print(f"  ✅ {layer}: {info['count']} files")
            if info["files"]:
                for fname in info["files"][:3]:  # 最初の3ファイル
                    print(f"      - {fname}")
        else:
            print(f"  ❌ {layer}: Not found")

    # 新形式データ
    print("\n📊 新形式データ (v2.0.0):")
    new_data = all_checks["new_format"]
    if new_data["has_data"]:
        print("  ✅ データ存在: True")
        print(f"  📌 フォーマットバージョン: {new_data['format_version']}")
        for layer, info in new_data["layers"].items():
            if info["exists"]:
                if "error" in info:
                    print(f"  ⚠️  {layer}: エラー - {info['error']}")
                else:
                    print(f"  ✅ {layer}:")
                    print(f"      - Version: {info['version']}")
                    print(f"      - Timestamp: {info['timestamp']}")
            else:
                print(f"  ⚠️  {layer}: データなし")
    else:
        print("  ⚠️  新形式データがまだ記録されていません")

    # 旧構造
    print("\n📦 旧構造 (benchmarks/):")
    old_structure = all_checks["old_structure"]
    if old_structure["exists"]:
        print("  ⚠️  旧構造が存在: benchmarks/")
        if old_structure["has_results"]:
            print(f"  📊 結果ファイル: {len(old_structure['result_files'])} files")
            print(f"  💾 合計サイズ: {format_size(old_structure['total_size'])}")
            if old_structure["result_files"]:
                print("  📄 ファイル例:")
                for fname in old_structure["result_files"][:3]:
                    print(f"      - {fname}")
            print("\n  ⚠️  アーカイブが必要です:")
            print("      scripts/archive_benchmarks.sh を実行してください")
    else:
        print("  ✅ 旧構造は削除済み")

    # 総合判定
    print("\n" + "=" * 60)
    print("総合判定:")

    all_passed = True
    issues = []

    if not all_dirs_ok:
        issues.append("必要なディレクトリが不足")
        all_passed = False

    if "count" in code_checks.get("bindings", {}) and code_checks["bindings"]["count"] == 0:
        issues.append("Bindings層のベンチマークコード未実装")
        all_passed = False
    elif not code_checks.get("bindings", {}).get("exists", False):
        issues.append("Bindings層のベンチマークディレクトリが存在しない")
        all_passed = False

    if "count" in code_checks.get("integration", {}) and code_checks["integration"]["count"] == 0:
        issues.append("Integration層のベンチマークコード未実装")
        all_passed = False
    elif not code_checks.get("integration", {}).get("exists", False):
        issues.append("Integration層のベンチマークディレクトリが存在しない")
        all_passed = False

    if not new_data["has_data"]:
        issues.append("新形式データ未記録")
        all_passed = False

    if old_structure["exists"]:
        issues.append("旧構造の削除が必要")
        all_passed = False

    if all_passed:
        print("✅ すべてのチェックに合格しました！")
    else:
        print("❌ 以下の問題があります:")
        for issue in issues:
            print(f"  - {issue}")

    print("=" * 60)

    return all_passed


def main():
    """メイン処理"""
    all_checks = {
        "directory": check_directory_structure(),
        "code": check_benchmark_code(),
        "new_format": check_new_format_data(),
        "old_structure": check_old_structure(),
    }

    success = print_report(all_checks)

    # 終了コード
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
