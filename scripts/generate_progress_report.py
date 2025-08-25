#!/usr/bin/env python3
"""進捗状況をツリー形式で可視化するレポート生成ツール."""

import sys
from pathlib import Path
from typing import Any

import yaml

# ステータスに対応する絵文字
STATUS_EMOJI = {
    "not_started": "⭕",  # 未着手
    "partial": "🟡",  # 部分実装
    "implemented": "🟢",  # 実装完了
    "tested": "✅",  # テスト済み
    "documented_only": "📝",  # ドキュメントのみ
}

# ステータスの重み（進捗計算用）
STATUS_WEIGHT = {
    "not_started": 0,
    "partial": 50,
    "implemented": 75,
    "tested": 100,
    "documented_only": None,  # 進捗計算から除外
}


def calculate_progress(items: list[dict[str, Any]]) -> tuple[int, int, int]:
    """アイテムリストから進捗を計算.

    Args:
        items: 見出し情報のリスト

    Returns:
        (完了数, 部分実装数, 未着手数)のタプル
    """
    completed = 0
    in_progress = 0
    not_started = 0

    for item in items:
        status = item.get("status", "not_started")

        if status in ["tested", "implemented"]:
            completed += 1
        elif status == "partial":
            in_progress += 1
        elif status == "not_started":
            not_started += 1

        # 子要素も再帰的に計算
        if "items" in item:
            c, p, n = calculate_progress(item["items"])
            completed += c
            in_progress += p
            not_started += n

    return completed, in_progress, not_started


def calculate_percentage(items: list[dict[str, Any]]) -> float:
    """進捗率を計算.

    Args:
        items: 見出し情報のリスト

    Returns:
        進捗率（0-100）
    """
    total_weight = 0
    total_items = 0

    def count_items(items_list: list[dict[str, Any]]) -> None:
        nonlocal total_weight, total_items

        for item in items_list:
            status = item.get("status", "not_started")
            weight = STATUS_WEIGHT.get(status)

            # documented_onlyは進捗計算から除外
            if weight is not None:
                total_weight += weight
                total_items += 1

            # 子要素も再帰的に計算
            if "items" in item:
                count_items(item["items"])

    count_items(items)

    if total_items == 0:
        return 0.0

    return total_weight / total_items


def format_tree(items: list[dict[str, Any]], indent: int = 0) -> str:
    """ツリー形式で進捗を表示.

    Args:
        items: 見出し情報のリスト
        indent: インデントレベル

    Returns:
        フォーマットされた文字列
    """
    output = []

    for item in items:
        # インデントとプレフィックス
        prefix = "  " * indent + "- "

        # ステータス絵文字
        status = item.get("status", "not_started")
        emoji = STATUS_EMOJI.get(status, "❓")

        # タイトルと絵文字
        line = f"{prefix}{item['title']}: {emoji}"

        # 追加情報
        if item.get("location"):
            line += f" [{item['location']}]"

        # 子要素がある場合は進捗率を表示
        if "items" in item:
            percentage = calculate_percentage(item["items"])
            if percentage > 0:
                line += f" ({percentage:.0f}%)"

        output.append(line)

        # 子要素を再帰的に処理
        if "items" in item:
            child_output = format_tree(item["items"], indent + 1)
            if child_output:
                output.append(child_output)

    return "\n".join(output)


def generate_summary(data: dict[str, Any]) -> str:
    """全体サマリーを生成.

    Args:
        data: 進捗データ

    Returns:
        サマリー文字列
    """
    metadata = data.get("metadata", {})

    # 全体統計を計算
    total_completed = 0
    total_in_progress = 0
    total_not_started = 0

    for doc_items in data.get("documents", {}).values():
        c, p, n = calculate_progress(doc_items)
        total_completed += c
        total_in_progress += p
        total_not_started += n

    total = total_completed + total_in_progress + total_not_started

    completion_rate = 0 if total == 0 else total_completed / total * 100

    summary = [
        "# QuantForge 実装進捗状況",
        "",
        f"最終更新: {metadata.get('last_updated', 'N/A')}",
        "",
        "## 📊 全体進捗",
        f"- 完了: {total_completed}項目 ({total_completed / max(total, 1) * 100:.1f}%)",
        f"- 実装中: {total_in_progress}項目 ({total_in_progress / max(total, 1) * 100:.1f}%)",
        f"- 未着手: {total_not_started}項目 ({total_not_started / max(total, 1) * 100:.1f}%)",
        f"- **完了率: {completion_rate:.1f}%**",
        "",
    ]

    return "\n".join(summary)


def generate_phase_summary(data: dict[str, Any]) -> str:
    """フェーズ別サマリーを生成.

    Args:
        data: 進捗データ

    Returns:
        フェーズサマリー文字列
    """
    phases = data.get("phases", {})

    if not phases:
        return ""

    output = ["## 📅 フェーズ別進捗", ""]

    for phase_id, phase_info in phases.items():
        name = phase_info.get("name", phase_id)
        weeks = phase_info.get("weeks", "N/A")
        status = phase_info.get("status", "not_started")
        emoji = STATUS_EMOJI.get(status, "❓")

        output.append(f"### {emoji} {name} (Week {weeks})")

        items = phase_info.get("items", [])
        if items:
            for item in items:
                output.append(f"  - {item}")

        output.append("")

    return "\n".join(output)


def generate_priority_list(data: dict[str, Any]) -> str:
    """優先度別タスクリストを生成.

    Args:
        data: 進捗データ

    Returns:
        優先度リスト文字列
    """
    priorities = data.get("priorities", {})

    if not priorities:
        return ""

    output = ["## 🎯 優先タスク", ""]

    for priority_level, tasks in priorities.items():
        output.append(f"### {priority_level.capitalize()} Priority")
        for task in tasks:
            output.append(f"- {task}")
        output.append("")

    return "\n".join(output)


def main() -> None:
    """メインエントリーポイント."""
    if len(sys.argv) < 2:
        print("Usage: python generate_progress_report.py <tracker.yaml>", file=sys.stderr)
        print("Example: python generate_progress_report.py tracker.yaml", file=sys.stderr)
        sys.exit(1)

    tracker_file = Path(sys.argv[1])

    if not tracker_file.exists():
        print(f"Error: File {tracker_file} does not exist", file=sys.stderr)
        sys.exit(1)

    # YAMLファイルを読み込み
    try:
        with open(tracker_file, encoding="utf-8") as f:
            data = yaml.safe_load(f)
    except Exception as e:
        print(f"Error loading YAML: {e}", file=sys.stderr)
        sys.exit(1)

    # レポート生成
    output = []

    # サマリー
    output.append(generate_summary(data))

    # フェーズ別進捗
    phase_summary = generate_phase_summary(data)
    if phase_summary:
        output.append(phase_summary)

    # 優先タスク
    priority_list = generate_priority_list(data)
    if priority_list:
        output.append(priority_list)

    # ドキュメント別詳細
    output.append("## 📁 ドキュメント別詳細")
    output.append("")

    documents = data.get("documents", {})
    for doc_path, items in documents.items():
        output.append(f"### {doc_path}")

        # 進捗率を計算
        percentage = calculate_percentage(items)
        c, p, n = calculate_progress(items)

        output.append(f"進捗: {percentage:.0f}% (完了: {c}, 実装中: {p}, 未着手: {n})")
        output.append("")

        # ツリー形式で表示
        tree = format_tree(items)
        output.append(tree)
        output.append("")

    # ステータス記号の凡例
    output.append("## 📖 ステータス記号")
    output.append("")
    for status, emoji in STATUS_EMOJI.items():
        status_label = status.replace("_", " ").title()
        output.append(f"- {emoji} : {status_label}")

    # 出力
    print("\n".join(output))


if __name__ == "__main__":
    main()
