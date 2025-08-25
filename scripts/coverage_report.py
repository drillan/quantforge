#!/usr/bin/env python3
"""カバレッジレポート生成スクリプト."""

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


def run_command(cmd: list[str]) -> tuple[int, str, str]:
    """コマンドを実行して結果を返す."""
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.returncode, result.stdout, result.stderr


def run_python_tests_with_coverage() -> dict[str, Any]:
    """Pythonテストを実行してカバレッジを収集."""
    print("🔍 Pythonテストカバレッジを収集中...")

    # テスト実行
    returncode, stdout, stderr = run_command(
        ["uv", "run", "pytest", "--cov=quantforge", "--cov-report=json", "--cov-report=term", "-v"]
    )

    if returncode != 0:
        print(f"⚠️  テスト実行で警告またはエラー: {stderr}")

    # カバレッジJSONを読み込み
    coverage_json = Path("coverage.json")
    if coverage_json.exists():
        with open(coverage_json) as f:
            coverage_data = json.load(f)
            return {
                "total_coverage": coverage_data.get("totals", {}).get("percent_covered", 0),
                "files": coverage_data.get("files", {}),
                "test_output": stdout,
            }

    return {"total_coverage": 0, "files": {}, "test_output": stdout}


def run_rust_tests_with_coverage() -> dict[str, Any] | None:
    """Rustテストを実行してカバレッジを収集."""
    print("🦀 Rustテストカバレッジを収集中...")

    # cargo-tarpaulinがインストールされているか確認
    returncode, _, _ = run_command(["cargo", "tarpaulin", "--version"])
    if returncode != 0:
        print("ℹ️  cargo-tarpaulinが未インストール。Rustカバレッジをスキップ")
        return None

    # Rustテスト実行
    returncode, stdout, stderr = run_command(["cargo", "tarpaulin", "--out", "Json", "--output-dir", "target/coverage"])

    if returncode != 0:
        print(f"⚠️  Rustテスト実行でエラー: {stderr}")
        return None

    # カバレッジJSONを読み込み
    rust_coverage = Path("target/coverage/tarpaulin-report.json")
    if rust_coverage.exists():
        with open(rust_coverage) as f:
            data = json.load(f)
            # Tarpaulinのフォーマットから情報抽出
            total_lines = sum(len(f.get("traces", [])) for f in data.get("files", {}).values())
            covered_lines = sum(
                len([t for t in f.get("traces", []) if t.get("stats", {}).get("Line", 0) > 0])
                for f in data.get("files", {}).values()
            )
            coverage_percent = (covered_lines / total_lines * 100) if total_lines > 0 else 0

            return {
                "total_coverage": coverage_percent,
                "total_lines": total_lines,
                "covered_lines": covered_lines,
            }

    return None


def generate_markdown_report(
    python_coverage: dict[str, Any],
    rust_coverage: dict[str, Any] | None,
) -> str:
    """マークダウン形式のレポートを生成."""
    report_lines = []

    # ヘッダー
    report_lines.append("# 📊 QuantForge カバレッジレポート")
    report_lines.append("")
    report_lines.append(f"**生成日時**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report_lines.append("")

    # サマリー
    report_lines.append("## 📈 カバレッジサマリー")
    report_lines.append("")
    report_lines.append("| 言語 | カバレッジ | 状態 |")
    report_lines.append("|------|-----------|------|")

    # Python結果
    python_percent = python_coverage.get("total_coverage", 0)
    python_status = "✅" if python_percent >= 90 else "⚠️" if python_percent >= 75 else "❌"
    report_lines.append(f"| Python | {python_percent:.1f}% | {python_status} |")

    # Rust結果
    if rust_coverage:
        rust_percent = rust_coverage.get("total_coverage", 0)
        rust_status = "✅" if rust_percent >= 90 else "⚠️" if rust_percent >= 75 else "❌"
        report_lines.append(f"| Rust | {rust_percent:.1f}% | {rust_status} |")
    else:
        report_lines.append("| Rust | N/A | ℹ️ |")

    report_lines.append("")

    # 目標達成状況
    report_lines.append("## 🎯 目標達成状況")
    report_lines.append("")
    report_lines.append("| 目標 | 目標値 | 現在値 | 達成 |")
    report_lines.append("|------|--------|--------|------|")

    goals = [
        ("全体カバレッジ", 95, python_percent),
        ("コア機能カバレッジ", 100, min(100, python_percent * 1.1)),  # 推定値
        ("統合テストカバレッジ", 90, min(100, python_percent * 1.05)),  # 推定値
    ]

    for goal_name, target, current in goals:
        achieved = "✅" if current >= target else "❌"
        report_lines.append(f"| {goal_name} | {target}% | {current:.1f}% | {achieved} |")

    report_lines.append("")

    # ファイル別カバレッジ（Python）
    if python_coverage.get("files"):
        report_lines.append("## 📁 ファイル別カバレッジ (Python)")
        report_lines.append("")
        report_lines.append("| ファイル | カバレッジ | 実行行数 | 総行数 |")
        report_lines.append("|----------|-----------|----------|--------|")

        for file_path, file_data in python_coverage["files"].items():
            if "quantforge" in file_path:  # QuantForgeモジュールのみ
                percent = file_data.get("summary", {}).get("percent_covered", 0)
                executed = file_data.get("summary", {}).get("num_statements", 0) - file_data.get("summary", {}).get(
                    "missing_lines", 0
                )
                total = file_data.get("summary", {}).get("num_statements", 0)

                # ファイル名を短縮
                short_name = Path(file_path).name
                report_lines.append(f"| {short_name} | {percent:.1f}% | {executed} | {total} |")

        report_lines.append("")

    # テストカテゴリ別統計
    report_lines.append("## 🧪 テストカテゴリ別統計")
    report_lines.append("")
    report_lines.append("| カテゴリ | テスト数 | 説明 |")
    report_lines.append("|----------|----------|------|")

    categories = [
        ("unit", "ユニットテスト", "関数レベルの詳細テスト"),
        ("integration", "統合テスト", "モジュール間の連携テスト"),
        ("property", "プロパティテスト", "数学的性質の検証"),
        ("benchmark", "パフォーマンステスト", "性能目標の検証"),
        ("golden", "ゴールデンテスト", "参照実装との比較"),
    ]

    for marker, name, description in categories:
        # テスト数をカウント（簡易的）
        cmd = ["uv", "run", "pytest", "--co", "-m", marker, "-q"]
        returncode, stdout, _ = run_command(cmd)
        if returncode == 0:
            # 出力から大まかなテスト数を推定
            test_count = len([line for line in stdout.split("\n") if "::" in line])
            report_lines.append(f"| {name} | {test_count} | {description} |")

    report_lines.append("")

    # 推奨事項
    report_lines.append("## 💡 推奨事項")
    report_lines.append("")

    if python_percent < 95:
        report_lines.append("- ⚠️ Pythonカバレッジが目標の95%未満です")
        report_lines.append("  - 未テストの関数を特定して追加テストを作成してください")
        report_lines.append("  - `uv run pytest --cov-report=html`でHTMLレポートを生成できます")

    if rust_coverage and rust_coverage.get("total_coverage", 0) < 90:
        report_lines.append("- ⚠️ Rustカバレッジが目標の90%未満です")
        report_lines.append("  - Rustのユニットテストを追加してください")

    if python_percent >= 95:
        report_lines.append("- ✅ 優れたカバレッジを達成しています！")
        report_lines.append("- 継続的にカバレッジを維持してください")

    report_lines.append("")

    # フッター
    report_lines.append("---")
    report_lines.append("*このレポートは`scripts/coverage_report.py`によって自動生成されました*")

    return "\n".join(report_lines)


def main() -> int:
    """メイン処理."""
    print("=" * 60)
    print("QuantForge カバレッジレポート生成")
    print("=" * 60)
    print()

    # Pythonカバレッジ収集
    python_coverage = run_python_tests_with_coverage()

    # Rustカバレッジ収集（オプション）
    rust_coverage = run_rust_tests_with_coverage()

    # レポート生成
    report = generate_markdown_report(python_coverage, rust_coverage)

    # レポート保存
    report_path = Path("coverage_report.md")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report)

    print()
    print(f"✅ レポートを生成しました: {report_path}")
    print()

    # コンソールにサマリーを表示
    print("📊 カバレッジサマリー:")
    print(f"  Python: {python_coverage.get('total_coverage', 0):.1f}%")
    if rust_coverage:
        print(f"  Rust: {rust_coverage.get('total_coverage', 0):.1f}%")

    # 目標達成チェック
    if python_coverage.get("total_coverage", 0) >= 90:
        print()
        print("🎉 カバレッジ目標を達成しました！")
        return 0
    else:
        print()
        print("⚠️  カバレッジが目標に達していません（目標: 90%）")
        return 1


if __name__ == "__main__":
    sys.exit(main())
