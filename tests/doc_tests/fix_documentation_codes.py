#!/usr/bin/env python3
"""ドキュメント内のPythonコードサンプルを自動修正するスクリプト。"""

import argparse
import re
import shutil
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


@dataclass
class CodeFix:
    """コード修正情報。"""

    pattern: str
    replacement: str
    description: str
    context: str | None = None  # 特定のコンテキストでのみ適用


class DocumentationCodeFixer:
    """ドキュメントコードの自動修正ツール。"""

    # バッチAPIパラメータ名の修正ルール
    BATCH_API_PARAM_FIXES = [
        CodeFix(
            pattern=r"\bk=", replacement="strikes=", description="バッチAPIのstrikeパラメータ修正", context="_batch"
        ),
        CodeFix(pattern=r"\bt=", replacement="times=", description="バッチAPIのtimeパラメータ修正", context="_batch"),
        CodeFix(pattern=r"\br=", replacement="rates=", description="バッチAPIのrateパラメータ修正", context="_batch"),
        CodeFix(
            pattern=r"\bsigma=", replacement="sigmas=", description="バッチAPIのsigmaパラメータ修正", context="_batch"
        ),
        CodeFix(
            pattern=r"\bq=",
            replacement="dividend_yields=",
            description="バッチAPIのdividendパラメータ修正",
            context="_batch",
        ),
    ]

    # Greeks辞書アクセスの修正ルール
    GREEKS_ACCESS_FIXES = [
        CodeFix(pattern=r"greeks\.delta\b", replacement="greeks['delta']", description="Greeks deltaアクセス修正"),
        CodeFix(pattern=r"greeks\.gamma\b", replacement="greeks['gamma']", description="Greeks gammaアクセス修正"),
        CodeFix(pattern=r"greeks\.vega\b", replacement="greeks['vega']", description="Greeks vegaアクセス修正"),
        CodeFix(pattern=r"greeks\.theta\b", replacement="greeks['theta']", description="Greeks thetaアクセス修正"),
        CodeFix(pattern=r"greeks\.rho\b", replacement="greeks['rho']", description="Greeks rhoアクセス修正"),
        CodeFix(
            pattern=r"greeks\.dividend_rho\b",
            replacement="greeks['dividend_rho']",
            description="Greeks dividend_rhoアクセス修正",
        ),
    ]

    # greeks_batch引数混在修正ルール
    GREEKS_BATCH_FIXES = [
        # Black-Scholes系（6引数）
        CodeFix(
            pattern=r"(\w+)\.greeks_batch\(([^,]+),\s*([^,]+),\s*([^,]+),\s*([^,]+),\s*([^,]+),\s*is_calls=([^)]+)\)",
            replacement=(
                r"\1.greeks_batch(\n    spots=\2,\n    strikes=\3,\n    times=\4,\n    "
                r"rates=\5,\n    sigmas=\6,\n    is_calls=\7\n)"
            ),
            description="Black-Scholes greeks_batch引数修正",
            context="black_scholes",
        ),
        # Merton/American系（7引数）
        CodeFix(
            pattern=r"(\w+)\.greeks_batch\(([^,]+),\s*([^,]+),\s*([^,]+),\s*([^,]+),\s*([^,]+),\s*([^,]+),\s*is_calls=([^)]+)\)",
            replacement=(
                r"\1.greeks_batch(\n    spots=\2,\n    strikes=\3,\n    times=\4,\n    rates=\5,\n    "
                r"dividend_yields=\6,\n    sigmas=\7,\n    is_calls=\8\n)"
            ),
            description="Merton/American greeks_batch引数修正",
            context="merton|american",
        ),
        # Black76系（forwards使用）
        CodeFix(
            pattern=r"black76\.greeks_batch\(([^,]+),\s*([^,]+),\s*([^,]+),\s*([^,]+),\s*([^,]+),\s*is_calls=([^)]+)\)",
            replacement=(
                r"black76.greeks_batch(\n    forwards=\1,\n    strikes=\2,\n    times=\3,\n    "
                r"rates=\4,\n    sigmas=\5,\n    is_calls=\6\n)"
            ),
            description="Black76 greeks_batch引数修正",
        ),
    ]

    # bashコマンドパターン
    BASH_COMMAND_PATTERNS = [
        r"^\s*pip\s+",
        r"^\s*uv\s+",
        r"^\s*git\s+",
        r"^\s*cd\s+",
        r"^\s*cargo\s+",
        r"^\s*pytest\s+",
        r"^\s*python\s+-m\s+",
        r"^\s*maturin\s+",
        r"^\s*ruff\s+",
        r"^\s*mypy\s+",
        r"^\s*#.*インストール",
        r"^\s*#.*install",
    ]

    def __init__(self, dry_run: bool = False, verbose: bool = False):
        """初期化。

        Args:
            dry_run: 実際にファイルを変更しない（確認のみ）
            verbose: 詳細な出力を表示
        """
        self.dry_run = dry_run
        self.verbose = verbose
        self.fixes_applied: list[CodeFix] = []

    def fix_file(self, filepath: Path) -> int:
        """ファイル内のコードブロックを修正。

        Args:
            filepath: 修正対象のファイル

        Returns:
            修正した箇所の数
        """
        if not filepath.exists():
            print(f"File not found: {filepath}")
            return 0

        content = filepath.read_text(encoding="utf-8")
        original_content = content
        fix_count = 0

        # コードブロックを検索して修正
        content, count1 = self._fix_code_blocks(content)
        fix_count += count1

        # コードブロックタイプを修正
        content, count2 = self._fix_block_types(content)
        fix_count += count2

        # ファイルを更新（dry_runでない場合）
        if content != original_content:
            if not self.dry_run:
                # バックアップ作成
                backup_path = filepath.with_suffix(filepath.suffix + ".bak")
                shutil.copy2(filepath, backup_path)

                # ファイル更新
                filepath.write_text(content, encoding="utf-8")
                print(f"✅ Fixed {fix_count} issues in {filepath}")
            else:
                print(f"📝 Would fix {fix_count} issues in {filepath}")

            if self.verbose:
                self._show_diff(original_content, content, filepath)
        else:
            if self.verbose:
                print(f"✓ No fixes needed for {filepath}")

        return fix_count

    def _fix_code_blocks(self, content: str) -> tuple[str, int]:
        """コードブロック内のコードを修正。

        Args:
            content: ファイル内容

        Returns:
            (修正後の内容, 修正数)のタプル
        """
        fix_count = 0

        # 単純なPythonコードブロック
        def fix_python_block(match):
            nonlocal fix_count
            code = match.group(1)
            fixed_code, count = self._apply_fixes(code)
            fix_count += count
            return f"```python\n{fixed_code}\n```"

        content = re.sub(r"```python\n(.*?)\n```", fix_python_block, content, flags=re.MULTILINE | re.DOTALL)

        # Sphinxコードブロック
        def fix_sphinx_block(match):
            nonlocal fix_count
            options = match.group(1)
            code = match.group(2)
            fixed_code, count = self._apply_fixes(code)
            fix_count += count
            return f"```{{code-block}} python\n{options}{fixed_code}\n```"

        content = re.sub(
            r"```\{code-block\}\s+python\s*\n((?::.*\n)*)(.*?)\n```",
            fix_sphinx_block,
            content,
            flags=re.MULTILINE | re.DOTALL,
        )

        return content, fix_count

    def _apply_fixes(self, code: str) -> tuple[str, int]:
        """コードに修正を適用。

        Args:
            code: 修正対象のコード

        Returns:
            (修正後のコード, 修正数)のタプル
        """
        fix_count = 0

        # バッチAPIパラメータ名の修正
        if "_batch" in code:  # バッチAPIの場合のみ
            for fix in self.BATCH_API_PARAM_FIXES:
                if re.search(fix.pattern, code):
                    code = re.sub(fix.pattern, fix.replacement, code)
                    fix_count += 1
                    if self.verbose:
                        print(f"  Applied: {fix.description}")

        # Greeks辞書アクセスの修正
        for fix in self.GREEKS_ACCESS_FIXES:
            if re.search(fix.pattern, code):
                code = re.sub(fix.pattern, fix.replacement, code)
                fix_count += 1
                if self.verbose:
                    print(f"  Applied: {fix.description}")

        # greeks_batch引数混在修正
        if "greeks_batch" in code and "is_calls=" in code:
            for fix in self.GREEKS_BATCH_FIXES:
                if re.search(fix.pattern, code):
                    code = re.sub(fix.pattern, fix.replacement, code)
                    fix_count += 1
                    if self.verbose:
                        print(f"  Applied: {fix.description}")

        return code, fix_count

    def _fix_block_types(self, content: str) -> tuple[str, int]:
        """コードブロックのタイプを修正（pythonをbashに）。

        Args:
            content: ファイル内容

        Returns:
            (修正後の内容, 修正数)のタプル
        """
        fix_count = 0

        # bashコマンドパターンをコンパイル
        bash_patterns = [re.compile(p, re.MULTILINE) for p in self.BASH_COMMAND_PATTERNS]

        def check_if_bash(code: str) -> bool:
            """コードがbashコマンドかチェック。"""
            lines = code.strip().split("\n")
            if not lines:
                return False

            # 最初の実行行を確認
            for line in lines:
                # コメント行をスキップ
                if line.strip().startswith("#"):
                    continue
                # 空行をスキップ
                if not line.strip():
                    continue

                # bashパターンと照合
                return any(pattern.search(line) for pattern in bash_patterns)

            return False

        # 単純なpythonブロックをチェック
        def fix_block_type(match):
            nonlocal fix_count
            code = match.group(1)
            if check_if_bash(code):
                fix_count += 1
                if self.verbose:
                    print("  Changed python to bash block")
                return f"```bash\n{code}\n```"
            return match.group(0)

        content = re.sub(r"```python\n(.*?)\n```", fix_block_type, content, flags=re.MULTILINE | re.DOTALL)

        return content, fix_count

    def _show_diff(self, original: str, fixed: str, filepath: Path):
        """差分を表示。"""
        import difflib

        diff = difflib.unified_diff(
            original.splitlines(keepends=True),
            fixed.splitlines(keepends=True),
            fromfile=str(filepath),
            tofile=str(filepath) + " (fixed)",
            lineterm="",
        )

        for line in diff:
            if line.startswith("+") and not line.startswith("+++"):
                print(f"\033[92m{line}\033[0m", end="")  # 緑
            elif line.startswith("-") and not line.startswith("---"):
                print(f"\033[91m{line}\033[0m", end="")  # 赤
            else:
                print(line, end="")

    def fix_directory(self, directory: Path, pattern: str = "*.md") -> int:
        """ディレクトリ内のすべてのファイルを修正。

        Args:
            directory: 対象ディレクトリ
            pattern: ファイルパターン

        Returns:
            総修正数
        """
        total_fixes = 0
        files = list(directory.rglob(pattern))

        print(f"Processing {len(files)} files in {directory}")

        for filepath in files:
            # archiveディレクトリはスキップ
            if "archive" in filepath.parts:
                continue

            fixes = self.fix_file(filepath)
            total_fixes += fixes

        return total_fixes


def main():
    """メイン処理。"""
    parser = argparse.ArgumentParser(description="ドキュメント内のPythonコードサンプルを自動修正")
    parser.add_argument("path", type=Path, help="修正対象のファイルまたはディレクトリ")
    parser.add_argument("--dry-run", action="store_true", help="実際にファイルを変更せず、変更内容を表示")
    parser.add_argument("--verbose", "-v", action="store_true", help="詳細な出力を表示")
    parser.add_argument("--pattern", default="*.md", help="ファイルパターン（ディレクトリ指定時のみ）")

    args = parser.parse_args()

    # 修正ツールを初期化
    fixer = DocumentationCodeFixer(dry_run=args.dry_run, verbose=args.verbose)

    # タイムスタンプ
    print(f"Starting documentation fix at {datetime.now()}")
    if args.dry_run:
        print("🔍 DRY RUN MODE - No files will be modified")

    # 修正実行
    if args.path.is_file():
        fixes = fixer.fix_file(args.path)
        print(f"\nTotal fixes: {fixes}")
    elif args.path.is_dir():
        fixes = fixer.fix_directory(args.path, args.pattern)
        print(f"\nTotal fixes: {fixes}")
    else:
        print(f"Error: {args.path} not found")
        sys.exit(1)

    # 結果サマリー
    if not args.dry_run and fixes > 0:
        print("\n⚠️  Backup files created with .bak extension")
        print("To remove backups: find docs -name '*.bak' -delete")

    sys.exit(0 if fixes == 0 else 0)  # 修正があっても正常終了


if __name__ == "__main__":
    main()
