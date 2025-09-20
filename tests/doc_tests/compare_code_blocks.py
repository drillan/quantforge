#!/usr/bin/env python3
"""日本語版と英語版のドキュメント間でコードブロックの差分を調査。"""

import re
import sys
from collections import defaultdict
from dataclasses import dataclass
from difflib import unified_diff
from pathlib import Path

# パスを追加
sys.path.insert(0, str(Path(__file__).parent))

from tests.doc_tests.code_extractor import CodeBlock, DocCodeExtractor


@dataclass
class CodeComparison:
    """コードブロック比較結果。"""

    ja_block: CodeBlock | None
    en_block: CodeBlock | None
    is_identical: bool
    difference_type: str  # 'identical', 'comment_only', 'code_diff', 'missing_ja', 'missing_en'
    diff_lines: list[str]


class DocumentCodeComparator:
    """ドキュメント間のコードブロック比較ツール。"""

    def __init__(self):
        """初期化。"""
        self.extractor = DocCodeExtractor()

    def normalize_code(self, code: str) -> str:
        """コードを正規化（コメントや空行の差を除去）。

        Args:
            code: 正規化するコード

        Returns:
            正規化されたコード
        """
        lines = code.split("\n")
        normalized_lines = []

        for line in lines:
            # 空行をスキップ
            if not line.strip():
                continue

            # 日本語コメントを除去
            line_without_jp_comment = re.sub(r"#.*[ひらがなカタカナ漢字].*$", "", line)
            # 英語コメントを除去
            line_without_comment = re.sub(r"#.*$", "", line_without_jp_comment)

            # 空白を正規化
            normalized = line_without_comment.strip()
            if normalized:
                normalized_lines.append(normalized)

        return "\n".join(normalized_lines)

    def extract_comparable_pairs(self, ja_dir: Path, en_dir: Path) -> dict[str, tuple[Path, Path]]:
        """比較可能なファイルペアを抽出。

        Args:
            ja_dir: 日本語版ディレクトリ
            en_dir: 英語版ディレクトリ

        Returns:
            {相対パス: (日本語ファイル, 英語ファイル)} の辞書
        """
        ja_files: dict[str, Path] = {}
        en_files: dict[str, Path] = {}

        # 日本語ファイルを収集
        for filepath in ja_dir.rglob("*.md"):
            rel_path = filepath.relative_to(ja_dir)
            ja_files[str(rel_path)] = filepath

        # 英語ファイルを収集
        for filepath in en_dir.rglob("*.md"):
            rel_path = filepath.relative_to(en_dir)
            en_files[str(rel_path)] = filepath

        # 共通するファイルのペアを作成
        pairs: dict[str, tuple[Path, Path]] = {}
        for rel_path_str in ja_files:
            if rel_path_str in en_files:
                pairs[rel_path_str] = (ja_files[rel_path_str], en_files[rel_path_str])

        return pairs

    def compare_code_blocks(self, ja_blocks: list[CodeBlock], en_blocks: list[CodeBlock]) -> list[CodeComparison]:
        """2つのファイルのコードブロックを比較。

        Args:
            ja_blocks: 日本語版のコードブロック
            en_blocks: 英語版のコードブロック

        Returns:
            比較結果のリスト
        """
        comparisons = []

        # 位置ベースで比較（同じ順序で出現すると仮定）
        max_len = max(len(ja_blocks), len(en_blocks))

        for i in range(max_len):
            ja_block = ja_blocks[i] if i < len(ja_blocks) else None
            en_block = en_blocks[i] if i < len(en_blocks) else None

            if ja_block is None:
                comparison = CodeComparison(
                    ja_block=None, en_block=en_block, is_identical=False, difference_type="missing_ja", diff_lines=[]
                )
            elif en_block is None:
                comparison = CodeComparison(
                    ja_block=ja_block, en_block=None, is_identical=False, difference_type="missing_en", diff_lines=[]
                )
            else:
                # 両方存在する場合の比較
                comparison = self._compare_single_blocks(ja_block, en_block)

            comparisons.append(comparison)

        return comparisons

    def _compare_single_blocks(self, ja_block: CodeBlock, en_block: CodeBlock) -> CodeComparison:
        """単一のコードブロック同士を比較。

        Args:
            ja_block: 日本語版ブロック
            en_block: 英語版ブロック

        Returns:
            比較結果
        """
        # 完全一致チェック
        if ja_block.code == en_block.code:
            return CodeComparison(
                ja_block=ja_block, en_block=en_block, is_identical=True, difference_type="identical", diff_lines=[]
            )

        # 正規化後の比較
        ja_normalized = self.normalize_code(ja_block.code)
        en_normalized = self.normalize_code(en_block.code)

        if ja_normalized == en_normalized:
            return CodeComparison(
                ja_block=ja_block, en_block=en_block, is_identical=True, difference_type="comment_only", diff_lines=[]
            )

        # 差分がある場合
        diff_lines = list(
            unified_diff(
                ja_block.code.splitlines(keepends=True),
                en_block.code.splitlines(keepends=True),
                fromfile=f"ja/{ja_block.filename}:{ja_block.line_number}",
                tofile=f"en/{en_block.filename}:{en_block.line_number}",
                lineterm="",
            )
        )

        return CodeComparison(
            ja_block=ja_block, en_block=en_block, is_identical=False, difference_type="code_diff", diff_lines=diff_lines
        )

    def analyze_differences(self, doc_root: Path) -> dict[str, list[CodeComparison]]:
        """ドキュメント全体の差分を分析。

        Args:
            doc_root: docsディレクトリのルート

        Returns:
            {ファイル名: 比較結果リスト} の辞書
        """
        ja_dir = doc_root / "ja"
        en_dir = doc_root / "en"

        if not ja_dir.exists() or not en_dir.exists():
            raise ValueError("日本語版または英語版ディレクトリが見つかりません")

        # 比較可能なファイルペアを取得
        file_pairs = self.extract_comparable_pairs(ja_dir, en_dir)

        results = {}

        for rel_path, (ja_file, en_file) in file_pairs.items():
            # 各ファイルからコードブロックを抽出
            ja_blocks = self.extractor.extract_from_file(ja_file)
            en_blocks = self.extractor.extract_from_file(en_file)

            # 比較実行
            comparisons = self.compare_code_blocks(ja_blocks, en_blocks)

            # 差分があるもののみ記録
            significant_comparisons = [
                comp for comp in comparisons if comp.difference_type in ["code_diff", "missing_ja", "missing_en"]
            ]

            if significant_comparisons:
                results[rel_path] = significant_comparisons

        return results


def main():
    """メイン処理。"""
    project_root = Path(__file__).parent.parent.parent
    doc_root = project_root / "docs"

    comparator = DocumentCodeComparator()

    print("=" * 80)
    print("日本語版・英語版ドキュメント コードブロック差分調査")
    print("=" * 80)

    try:
        results = comparator.analyze_differences(doc_root)

        if not results:
            print("\n✅ コメント以外のコードブロック差分は見つかりませんでした。")
            return

        print(f"\n⚠️  {len(results)}個のファイルでコードブロック差分を検出")

        # 統計情報
        total_diffs = 0
        diff_types: defaultdict[str, int] = defaultdict(int)

        for _file_path, comparisons in results.items():
            total_diffs += len(comparisons)
            for comp in comparisons:
                diff_types[comp.difference_type] += 1

        print("\n## 統計情報")
        print(f"差分ファイル数: {len(results)}")
        print(f"総差分数: {total_diffs}")
        print("種類別:")
        for diff_type, count in diff_types.items():
            print(f"  {diff_type}: {count}")

        # 詳細表示
        print("\n## 詳細")

        for file_path, comparisons in results.items():
            print(f"\n### {file_path}")

            for i, comp in enumerate(comparisons, 1):
                if comp.difference_type == "missing_ja":
                    print(f"  {i}. 日本語版にコードブロックが不足")
                    if comp.en_block:
                        print(f"     英語版: line {comp.en_block.line_number}")
                elif comp.difference_type == "missing_en":
                    print(f"  {i}. 英語版にコードブロックが不足")
                    if comp.ja_block:
                        print(f"     日本語版: line {comp.ja_block.line_number}")
                elif comp.difference_type == "code_diff":
                    ja_line = comp.ja_block.line_number if comp.ja_block else "N/A"
                    en_line = comp.en_block.line_number if comp.en_block else "N/A"
                    print(f"  {i}. コード内容に差分")
                    print(f"     日本語版: line {ja_line}")
                    print(f"     英語版: line {en_line}")

                    # 差分の詳細（最初の数行のみ）
                    if comp.diff_lines:
                        print("     差分:")
                        for line in comp.diff_lines[:10]:  # 最初の10行のみ
                            print(f"       {line.rstrip()}")
                        if len(comp.diff_lines) > 10:
                            print(f"       ... ({len(comp.diff_lines) - 10} more lines)")

    except Exception as e:
        print(f"エラー: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
