#!/usr/bin/env python3
"""ドキュメントから見出し構造を抽出してYAML形式で出力."""

import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml


def extract_headings(markdown_file: Path) -> list[dict[str, Any]]:
    """Markdownファイルから見出しを階層的に抽出.

    Args:
        markdown_file: Markdownファイルのパス

    Returns:
        見出し情報のリスト
    """
    headings: list[dict[str, Any]] = []

    try:
        with open(markdown_file, encoding="utf-8") as f:
            lines = f.readlines()
    except Exception as e:
        print(f"Error reading {markdown_file}: {e}", file=sys.stderr)
        return headings

    for line_num, line in enumerate(lines, 1):
        # 見出しを検出
        if line.startswith("#"):
            # レベルを計算（# の数）
            match = re.match(r"^(#+)\s+(.+)$", line)
            if match:
                level = len(match.group(1))
                title = match.group(2).strip()

                # 特殊文字を除去
                title = re.sub(r"[`*_\[\]()]", "", title)

                headings.append(
                    {"title": title, "level": level, "line": line_num, "status": "not_started", "notes": ""}
                )

    return headings


def build_hierarchy(headings: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """フラットな見出しリストを階層構造に変換.

    Args:
        headings: 見出し情報のフラットリスト

    Returns:
        階層化された見出し構造
    """
    if not headings:
        return []

    root = []
    stack: list[dict[str, Any]] = []

    for heading in headings:
        item = {
            "title": heading["title"],
            "level": heading["level"],
            "status": heading["status"],
        }

        # オプションフィールド
        if heading.get("line"):
            item["line"] = heading["line"]
        if heading.get("notes"):
            item["notes"] = heading["notes"]

        # 階層を構築
        while stack and stack[-1]["level"] >= heading["level"]:
            stack.pop()

        if stack:
            if "items" not in stack[-1]:
                stack[-1]["items"] = []
            stack[-1]["items"].append(item)
        else:
            root.append(item)

        stack.append(item)

    return root


def guess_status(title: str, content: str = "") -> str:
    """見出しタイトルから実装ステータスを推測.

    Args:
        title: 見出しタイトル
        content: セクションの内容（オプション）

    Returns:
        推測されたステータス
    """
    title_lower = title.lower()

    # ドキュメントのみのセクション
    doc_only_keywords = [
        "理論",
        "背景",
        "概要",
        "説明",
        "theory",
        "background",
        "overview",
        "仮定",
        "assumptions",
        "境界条件",
        "boundary",
        "変更履歴",
        "changelog",
        "まとめ",
        "summary",
    ]

    for keyword in doc_only_keywords:
        if keyword in title_lower:
            return "documented_only"

    # 数式セクション
    if "方程式" in title or "equation" in title_lower:
        return "documented_only"

    return "not_started"


def process_directory(docs_dir: Path) -> dict[str, Any]:
    """ディレクトリ内のMarkdownファイルを処理.

    Args:
        docs_dir: ドキュメントディレクトリのパス

    Returns:
        全ドキュメントの構造情報
    """
    result = {
        "metadata": {
            "last_updated": datetime.now().strftime("%Y-%m-%d"),
            "total_items": 0,
            "completed": 0,
            "in_progress": 0,
            "not_started": 0,
        },
        "documents": {},
    }

    # 対象ディレクトリ
    target_dirs = ["models", "api", "performance", "development", "user_guide"]

    for dir_name in target_dirs:
        dir_path = docs_dir / dir_name
        if not dir_path.exists():
            continue

        # Markdownファイルを検索
        for md_file in dir_path.rglob("*.md"):
            # index.mdは除外
            if md_file.name == "index.md":
                continue

            # 相対パスを取得
            rel_path = md_file.relative_to(docs_dir.parent)

            # 見出しを抽出
            headings = extract_headings(md_file)
            if headings:
                # ステータスを推測
                for heading in headings:
                    heading["status"] = guess_status(heading["title"])

                # 階層構造を構築
                hierarchy = build_hierarchy(headings)

                # 結果に追加
                result["documents"][str(rel_path)] = hierarchy

                # 統計を更新
                total_items = result["metadata"].get("total_items", 0)
                assert isinstance(total_items, int)
                result["metadata"]["total_items"] = total_items + len(headings)
                for heading in headings:
                    status = heading["status"]
                    if status == "tested" or status == "implemented":
                        completed = result["metadata"].get("completed", 0)
                        assert isinstance(completed, int)
                        result["metadata"]["completed"] = completed + 1
                    elif status == "partial":
                        in_progress = result["metadata"].get("in_progress", 0)
                        assert isinstance(in_progress, int)
                        result["metadata"]["in_progress"] = in_progress + 1
                    elif status == "not_started":
                        not_started = result["metadata"].get("not_started", 0)
                        assert isinstance(not_started, int)
                        result["metadata"]["not_started"] = not_started + 1

    return result


def main() -> None:
    """メインエントリーポイント."""
    if len(sys.argv) < 2:
        print("Usage: python extract_doc_structure.py <docs_directory>", file=sys.stderr)
        print("Example: python extract_doc_structure.py docs/", file=sys.stderr)
        sys.exit(1)

    docs_dir = Path(sys.argv[1])

    if not docs_dir.exists():
        print(f"Error: Directory {docs_dir} does not exist", file=sys.stderr)
        sys.exit(1)

    # ドキュメント構造を抽出
    structure = process_directory(docs_dir)

    # YAML形式で出力
    yaml_output = yaml.dump(structure, default_flow_style=False, allow_unicode=True, sort_keys=False, width=120)

    print(yaml_output)

    # サマリーを標準エラー出力に表示
    metadata = structure["metadata"]
    print("\n=== Summary ===", file=sys.stderr)
    print(f"Total items: {metadata['total_items']}", file=sys.stderr)
    print(f"Completed: {metadata['completed']}", file=sys.stderr)
    print(f"In progress: {metadata['in_progress']}", file=sys.stderr)
    print(f"Not started: {metadata['not_started']}", file=sys.stderr)
    print(f"Documents processed: {len(structure['documents'])}", file=sys.stderr)


if __name__ == "__main__":
    main()
