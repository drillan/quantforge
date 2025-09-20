"""ドキュメント内のPythonコードサンプルのテスト。"""

import json
from pathlib import Path
from typing import List, Dict, Any

import pytest

from tests.doc_tests.code_extractor import DocCodeExtractor, CodeBlock

# ホワイトリスト：テスト対象のドキュメントのみ指定
TESTED_PATHS = [
    "docs/ja/quickstart.md",
    "docs/en/quickstart.md",
    # 日本語APIドキュメント
    "docs/ja/api/python/american.md",
    "docs/ja/api/python/batch_processing.md",
    "docs/ja/api/python/black76.md",
    "docs/ja/api/python/black_scholes.md",
    "docs/ja/api/python/greeks.md",
    "docs/ja/api/python/implied_vol.md",
    "docs/ja/api/python/index.md",
    "docs/ja/api/python/market_utils.md",
    "docs/ja/api/python/merton.md",
    "docs/ja/api/python/pricing.md"
]


class TestDocumentationCode:
    """ドキュメントコードのテストクラス。"""

    @pytest.fixture(scope="class")
    def code_blocks(self, doc_root, request) -> List[CodeBlock]:
        """テスト対象のコードブロックを抽出。

        Args:
            doc_root: ドキュメントルートディレクトリ
            request: pytestリクエストオブジェクト

        Returns:
            抽出されたコードブロックのリスト
        """
        extractor = DocCodeExtractor()

        # フィルターオプションを確認
        doc_filter = request.config.getoption("--doc-filter")

        if doc_filter:
            # 特定のドキュメントのみをテスト
            blocks = []

            # フィルターパスを正規化
            if doc_filter.startswith('docs/'):
                # フルパス指定の場合、project_rootから検索
                project_root = doc_root.parent

                # ワイルドカード（*）を含むかチェック
                if '*' in doc_filter or '?' in doc_filter:
                    # globパターンとして処理
                    for filepath in project_root.glob(doc_filter):
                        if filepath.is_file() and filepath.suffix == '.md':
                            blocks.extend(extractor.extract_from_file(filepath))
                else:
                    # 単一ファイルまたはパターンマッチング
                    target_path = project_root / doc_filter
                    if target_path.exists():
                        blocks.extend(extractor.extract_from_file(target_path))
                    else:
                        # パターンマッチング
                        for filepath in project_root.rglob(f"*{doc_filter}*.md"):
                            blocks.extend(extractor.extract_from_file(filepath))
            else:
                # 相対パス指定の場合、doc_rootから検索
                if '*' in doc_filter or '?' in doc_filter:
                    # globパターンとして処理
                    for filepath in doc_root.glob(doc_filter):
                        if filepath.is_file() and filepath.suffix == '.md':
                            blocks.extend(extractor.extract_from_file(filepath))
                else:
                    # パターンマッチング
                    for filepath in doc_root.rglob(f"*{doc_filter}*.md"):
                        blocks.extend(extractor.extract_from_file(filepath))
        else:
            # ホワイトリストに指定されたドキュメントのみをテスト
            blocks = []
            project_root = doc_root.parent  # docs/ の親ディレクトリ
            for tested_path in TESTED_PATHS:
                filepath = project_root / tested_path
                if filepath.exists():
                    blocks.extend(extractor.extract_from_file(filepath))
                else:
                    print(f"Warning: Tested path not found: {filepath}")

        return blocks

    @pytest.fixture(scope="class")
    def test_results(self) -> Dict[str, Any]:
        """テスト結果を収集。

        Returns:
            テスト結果の辞書
        """
        return {
            'total': 0,
            'executed': 0,
            'skipped': 0,
            'passed': 0,
            'failed': 0,
            'errors': []
        }

    def test_code_blocks_found(self, code_blocks):
        """コードブロックが抽出されたことを確認。"""
        assert len(code_blocks) > 0, "ドキュメントからコードブロックが見つかりません"
        print(f"\n見つかったコードブロック数: {len(code_blocks)}")

    @pytest.mark.documentation
    @pytest.mark.parametrize("block_index", range(100))  # 最大100ブロック（APIドキュメント含む）
    def test_code_execution(
        self,
        block_index,
        code_blocks,
        code_executor,
        test_results,
        request
    ):
        """各コードブロックを実行してテスト。

        Args:
            block_index: ブロックのインデックス
            code_blocks: すべてのコードブロック
            code_executor: コード実行環境
            test_results: テスト結果収集用
            request: pytestリクエスト
        """
        # インデックスが範囲外の場合はスキップ
        if block_index >= len(code_blocks):
            pytest.skip("ブロックインデックスが範囲外")

        block = code_blocks[block_index]
        test_results['total'] += 1

        # スキップフラグが設定されている場合
        if block.skip:
            test_results['skipped'] += 1
            pytest.skip(f"スキップ設定: {block.test_name}")

        # コードを実行
        test_results['executed'] += 1
        success, output, error = code_executor.execute(block.code)

        # 結果を記録
        if success:
            test_results['passed'] += 1
        else:
            test_results['failed'] += 1
            test_results['errors'].append({
                'block': block.test_name,
                'file': block.filename,
                'line': block.line_number,
                'error': error,
                'code_snippet': block.code[:200] + '...' if len(block.code) > 200 else block.code
            })

        # アサーション
        if not success:
            # エラーメッセージを整形
            error_msg = (
                f"\nコードブロックの実行に失敗しました:\n"
                f"  ファイル: {block.filename}:{block.line_number}\n"
                f"  ブロック: {block.test_name}\n"
                f"  エラー: {error}\n"
                f"  コード（先頭200文字）:\n"
                f"    {block.code[:200]}"
            )
            pytest.fail(error_msg)

        # 詳細レポートオプションが有効な場合
        if request.config.getoption("--doc-report"):
            print(f"\n✓ {block.test_name}")
            if output:
                print(f"  出力: {output[:100]}")

    def test_summary(self, test_results, test_report_dir, request):
        """テスト結果のサマリーを生成。"""
        # サマリーを表示
        print("\n" + "=" * 60)
        print("ドキュメントコードテスト サマリー")
        print("=" * 60)
        print(f"総ブロック数:     {test_results['total']}")
        print(f"実行:             {test_results['executed']}")
        print(f"スキップ:         {test_results['skipped']}")
        print(f"成功:             {test_results['passed']}")
        print(f"失敗:             {test_results['failed']}")

        if test_results['failed'] > 0:
            print("\n失敗したブロック:")
            for error in test_results['errors']:
                print(f"  - {error['block']} ({error['file']}:{error['line']})")

        # レポートオプションが有効な場合、JSONファイルに保存
        if request.config.getoption("--doc-report"):
            report_file = test_report_dir / "doc_test_report.json"
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(test_results, f, indent=2, ensure_ascii=False)
            print(f"\n詳細レポート: {report_file}")

        # 失敗があった場合はテスト失敗
        if test_results['failed'] > 0:
            pytest.fail(f"{test_results['failed']}個のコードブロックが失敗しました")


@pytest.mark.documentation
class TestSpecificDocuments:
    """特定のドキュメントファイルのテスト。"""

    def test_quickstart_examples(self, doc_root, code_executor):
        """クイックスタートガイドの例をテスト。"""
        quickstart_path = doc_root / "ja" / "quickstart.md"
        if not quickstart_path.exists():
            pytest.skip("quickstart.mdが見つかりません")

        extractor = DocCodeExtractor()
        blocks = extractor.extract_from_file(quickstart_path)

        executed = 0
        failed_blocks = []
        for i, block in enumerate(blocks):
            if not block.skip:
                success, output, error = code_executor.execute(block.code)
                executed += 1
                if not success:
                    failed_blocks.append({
                        'index': i + 1,
                        'line': block.line_number,
                        'name': block.test_name,
                        'error': error,
                        'code_snippet': block.code[:200]
                    })

        if failed_blocks:
            error_msg = "クイックスタートの例が失敗しました:\n"
            for fb in failed_blocks:
                error_msg += f"\nBlock {fb['index']} (line {fb['line']}, {fb['name']}):\n"
                error_msg += f"  Error: {fb['error']}\n"
                error_msg += f"  Code: {fb['code_snippet']}...\n"
            pytest.fail(error_msg)

        assert executed > 0, "クイックスタートに実行可能な例がありません"

    def test_api_reference_examples(self, doc_root, code_executor):
        """APIリファレンスの例をテスト。"""
        api_dir = doc_root / "ja" / "api" / "python"
        if not api_dir.exists():
            pytest.skip("APIディレクトリが見つかりません")

        extractor = DocCodeExtractor()
        blocks = extractor.extract_from_directory(api_dir)

        # 各APIファイルごとに集計
        by_file = {}
        for block in blocks:
            filename = Path(block.filename).name
            if filename not in by_file:
                by_file[filename] = {'total': 0, 'executed': 0, 'passed': 0}

            by_file[filename]['total'] += 1

            if not block.skip:
                success, output, error = code_executor.execute(block.code)
                by_file[filename]['executed'] += 1
                if success:
                    by_file[filename]['passed'] += 1

        # 結果を表示
        print("\nAPIドキュメントのテスト結果:")
        for filename, stats in by_file.items():
            print(f"  {filename}: {stats['passed']}/{stats['executed']} 成功 "
                  f"({stats['total']} ブロック中)")

        # すべてのファイルで少なくとも1つは実行可能な例があることを確認
        for filename, stats in by_file.items():
            assert stats['executed'] > 0, f"{filename}に実行可能な例がありません"


def pytest_collection_modifyitems(config, items):
    """テストアイテムをカスタマイズ。"""
    # 範囲外のtest_code_executionテストを事前に除外
    remaining_items = []

    # 実際のコードブロック数を取得（簡易的な推定）
    doc_filter = config.getoption("--doc-filter")
    if doc_filter:
        # フィルター使用時は多めに推定（ワイルドカード対応）
        max_expected_blocks = 80
    else:
        # デフォルト時（TESTED_PATHS）は現在の設定に基づく
        max_expected_blocks = 80  # 日本語APIドキュメント追加により増加

    for item in items:
        # test_code_executionのパラメータ化テストを対象に
        if "test_code_execution[" in item.nodeid and hasattr(item, 'callspec'):
            block_index = item.callspec.params.get('block_index')
            if block_index is not None and block_index >= max_expected_blocks:
                # 範囲外と推定されるテストは除外
                continue
        remaining_items.append(item)

    # アイテムリストを更新
    items[:] = remaining_items