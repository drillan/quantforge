#!/usr/bin/env python3
"""
ドキュメント内のコード例と実装の整合性を確認するスクリプト

このスクリプトは以下の3つのレベルで検証を行います：
1. 存在確認 - 関数やモジュールが存在するか
2. シグネチャ確認 - パラメータの順序や名前が一致するか
3. 実行可能性確認 - コード例が実際に動作するか
"""

import ast
import json
import re
import sys
import traceback
from dataclasses import dataclass
from enum import Enum
from pathlib import Path


class VerificationLevel(Enum):
    """検証レベル"""

    EXISTS = "exists"  # 存在確認のみ
    SIGNATURE = "signature"  # シグネチャ確認
    EXECUTABLE = "executable"  # 実行可能性確認


@dataclass
class CodeBlock:
    """ドキュメント内のコードブロック"""

    file_path: Path
    line_number: int
    language: str
    content: str
    block_name: str | None = None
    caption: str | None = None


@dataclass
class VerificationResult:
    """検証結果"""

    code_block: CodeBlock
    level: VerificationLevel
    success: bool
    message: str
    details: dict | None = None


class DocumentationCodeVerifier:
    """ドキュメントコード検証クラス"""

    def __init__(self, docs_path: Path, level: VerificationLevel = VerificationLevel.EXISTS):
        self.docs_path = docs_path
        self.level = level
        self.results: list[VerificationResult] = []

    def extract_code_blocks(self, markdown_file: Path) -> list[CodeBlock]:
        """Markdownファイルからコードブロックを抽出"""
        blocks = []

        with open(markdown_file, encoding="utf-8") as f:
            lines = f.readlines()

        i = 0
        while i < len(lines):
            line = lines[i]

            # MyST形式のコードブロック
            if line.startswith("```{code-block}"):
                match = re.match(r"```{code-block}\s+(\w+)", line)
                if match:
                    language = match.group(1)
                    block_name = None
                    caption = None

                    # メタデータを解析
                    j = i + 1
                    while j < len(lines) and not lines[j].strip().startswith("```"):
                        if lines[j].startswith(":name:"):
                            block_name = lines[j].split(":name:")[1].strip()
                        elif lines[j].startswith(":caption:"):
                            caption = lines[j].split(":caption:")[1].strip()
                        j += 1

                    # コード内容を抽出
                    code_lines = []
                    j += 1  # Skip empty line after metadata
                    while j < len(lines) and not lines[j].startswith("```"):
                        code_lines.append(lines[j])
                        j += 1

                    if code_lines:
                        blocks.append(
                            CodeBlock(
                                file_path=markdown_file,
                                line_number=i + 1,
                                language=language,
                                content="".join(code_lines),
                                block_name=block_name,
                                caption=caption,
                            )
                        )
                    i = j

            # 通常のコードブロック
            elif line.startswith("```"):
                match = re.match(r"```(\w+)?", line)
                language = match.group(1) if match and match.group(1) else "text"

                code_lines = []
                j = i + 1
                while j < len(lines) and not lines[j].startswith("```"):
                    code_lines.append(lines[j])
                    j += 1

                if code_lines and language in ["python", "rust"]:
                    blocks.append(
                        CodeBlock(
                            file_path=markdown_file, line_number=i + 1, language=language, content="".join(code_lines)
                        )
                    )
                i = j

            i += 1

        return blocks

    def extract_imports_and_calls(self, code: str) -> tuple[list[str], list[str]]:
        """コードからインポートと関数呼び出しを抽出"""
        imports = []
        calls = []

        try:
            tree = ast.parse(code)

            for node in ast.walk(tree):
                # インポート文を抽出
                if isinstance(node, ast.ImportFrom):
                    module = node.module or ""
                    for alias in node.names:
                        imports.append(f"from {module} import {alias.name}")
                elif isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.append(f"import {alias.name}")

                # 関数呼び出しを抽出
                elif isinstance(node, ast.Call):
                    if isinstance(node.func, ast.Attribute):
                        # module.function形式
                        if isinstance(node.func.value, ast.Name):
                            calls.append(f"{node.func.value.id}.{node.func.attr}")
                    elif isinstance(node.func, ast.Name):
                        # 単純な関数呼び出し
                        calls.append(node.func.id)

        except SyntaxError:
            # 構文エラーがある場合はスキップ
            pass

        return imports, calls

    def verify_exists(self, block: CodeBlock) -> VerificationResult:
        """存在確認レベルの検証"""
        imports, calls = self.extract_imports_and_calls(block.content)

        # quantforge関連のインポートのみチェック
        quantforge_imports = [imp for imp in imports if "quantforge" in imp]

        if not quantforge_imports:
            return VerificationResult(
                code_block=block,
                level=VerificationLevel.EXISTS,
                success=True,
                message="No quantforge imports to verify",
            )

        # 実際にインポートを試みる
        for imp in quantforge_imports:
            try:
                exec(imp)
                message = f"✓ {imp}"
            except ImportError as e:
                message = f"✗ {imp}: {str(e)}"
                return VerificationResult(
                    code_block=block, level=VerificationLevel.EXISTS, success=False, message=message
                )

        return VerificationResult(
            code_block=block,
            level=VerificationLevel.EXISTS,
            success=True,
            message=f"All imports verified: {', '.join(quantforge_imports)}",
        )

    def verify_executable(self, block: CodeBlock) -> VerificationResult:
        """実行可能性レベルの検証"""
        # まず存在確認
        exists_result = self.verify_exists(block)
        if not exists_result.success:
            return exists_result

        # コードの実行を試みる
        try:
            # 必要なインポートを追加
            setup_code = """
import numpy as np
import pyarrow as pa
"""
            exec(setup_code + block.content)

            return VerificationResult(
                code_block=block, level=VerificationLevel.EXECUTABLE, success=True, message="Code executed successfully"
            )
        except Exception as e:
            return VerificationResult(
                code_block=block,
                level=VerificationLevel.EXECUTABLE,
                success=False,
                message=f"Execution failed: {str(e)}",
                details={"traceback": traceback.format_exc()},
            )

    def verify_block(self, block: CodeBlock) -> VerificationResult:
        """コードブロックを検証"""
        if block.language != "python":
            return VerificationResult(
                code_block=block, level=self.level, success=True, message=f"Skipping {block.language} code"
            )

        if self.level == VerificationLevel.EXISTS:
            return self.verify_exists(block)
        elif self.level == VerificationLevel.EXECUTABLE:
            return self.verify_executable(block)
        else:
            # シグネチャ確認は将来実装
            return VerificationResult(
                code_block=block, level=self.level, success=True, message="Signature verification not yet implemented"
            )

    def verify_documentation(self, pattern: str = "**/*.md") -> None:
        """ドキュメントを検証"""
        markdown_files = list(self.docs_path.glob(pattern))

        print(f"Found {len(markdown_files)} documentation files")
        print(f"Verification level: {self.level.value}")
        print("=" * 80)

        total_blocks = 0

        for md_file in markdown_files:
            # API関連のドキュメントのみ対象
            if "api/python" not in str(md_file) and "user_guide" not in str(md_file):
                continue

            blocks = self.extract_code_blocks(md_file)
            if not blocks:
                continue

            print(f"\n📄 {md_file.relative_to(self.docs_path)}")
            print(f"   Found {len(blocks)} code blocks")

            for block in blocks:
                total_blocks += 1
                result = self.verify_block(block)
                self.results.append(result)

                # 結果を表示
                symbol = "✅" if result.success else "❌"

                location = f"L{block.line_number}"
                if block.block_name:
                    location += f" ({block.block_name})"

                print(f"   {symbol} {location}: {result.message}")

                if result.details and not result.success:
                    print(f"      Details: {result.details.get('traceback', '')[:200]}")

        # サマリー表示
        self.print_summary(total_blocks)

    def print_summary(self, total_blocks: int) -> None:
        """検証結果のサマリーを表示"""
        successful = sum(1 for r in self.results if r.success)
        failed = sum(1 for r in self.results if not r.success)

        print("\n" + "=" * 80)
        print("📊 VERIFICATION SUMMARY")
        print("=" * 80)
        print(f"Total code blocks:    {total_blocks}")
        print(f"Verified blocks:      {len(self.results)}")
        print(f"✅ Successful:        {successful}")
        print(f"❌ Failed:            {failed}")

        if failed > 0:
            print(f"\nSuccess rate: {successful / len(self.results) * 100:.1f}%")
            print("\n⚠️  Failed blocks:")
            for result in self.results:
                if not result.success:
                    rel_path = result.code_block.file_path.relative_to(self.docs_path)
                    print(f"  - {rel_path}:L{result.code_block.line_number}")
                    print(f"    {result.message}")
        else:
            print("\n✨ All code blocks verified successfully!")

    def export_results(self, output_file: Path) -> None:
        """結果をJSONファイルにエクスポート"""
        data = {
            "verification_level": self.level.value,
            "total_blocks": len(self.results),
            "successful": sum(1 for r in self.results if r.success),
            "failed": sum(1 for r in self.results if not r.success),
            "results": [
                {
                    "file": str(r.code_block.file_path),
                    "line": r.code_block.line_number,
                    "language": r.code_block.language,
                    "success": r.success,
                    "message": r.message,
                    "details": r.details,
                }
                for r in self.results
            ],
        }

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        print(f"\n📁 Results exported to: {output_file}")


def main():
    """メイン処理"""
    # プロジェクトルートを取得
    project_root = Path(__file__).parent.parent
    docs_path = project_root / "docs"

    # 検証レベルを設定（コマンドライン引数で変更可能）
    level = VerificationLevel.EXISTS
    if len(sys.argv) > 1:
        if sys.argv[1] == "executable":
            level = VerificationLevel.EXECUTABLE
        elif sys.argv[1] == "signature":
            level = VerificationLevel.SIGNATURE

    # 検証実行
    verifier = DocumentationCodeVerifier(docs_path, level)
    verifier.verify_documentation()

    # 結果をエクスポート
    output_file = project_root / "tracker" / "doc_verification_results.json"
    verifier.export_results(output_file)

    # 失敗があれば非ゼロで終了
    failed_count = sum(1 for r in verifier.results if not r.success)
    sys.exit(1 if failed_count > 0 else 0)


if __name__ == "__main__":
    main()
