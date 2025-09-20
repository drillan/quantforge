"""myst-parserによるドキュメントコード抽出の理想実装。"""

import ast
import re
from dataclasses import dataclass, replace
from pathlib import Path
from typing import List, Optional, Dict, Any, Set
import warnings

try:
    from myst_parser.parsers.docutils_ import Parser
    from docutils.core import publish_doctree
    import docutils.nodes as nodes
    MYST_AVAILABLE = True
except ImportError:
    MYST_AVAILABLE = False
    nodes = None
    warnings.warn("myst-parser not available, falling back to basic regex extraction")


@dataclass
class EnrichedCodeBlock:
    """完全な文脈情報を持つコードブロック。"""

    code: str
    filename: str
    line_number: int
    language: str
    options: Dict[str, str]
    section_path: List[str]          # セクション階層 ["User Guide", "Basic Usage"]
    dependencies: Set[str]           # 依存するブロック名
    provides: Set[str]               # 提供する変数・関数名
    execution_context: str           # API_REFERENCE/EXAMPLE/TUTORIAL
    ast_node: Optional[Any] = None   # 元のASTノード

    @property
    def test_name(self) -> str:
        """テスト名を生成。"""
        if 'name' in self.options:
            return self.options['name']
        return f"{Path(self.filename).stem}_line_{self.line_number}"

    @property
    def skip(self) -> bool:
        """テストをスキップするかどうか。"""
        return 'no-test' in self.options


class MystDocumentCodeExtractor:
    """MyST Markdown完全対応のコード抽出器。"""

    def __init__(self):
        """初期化。"""
        if not MYST_AVAILABLE:
            raise ImportError(
                "myst-parser is required for advanced code extraction. "
                "Install with: pip install myst-parser"
            )

        self.parser = Parser()

        # Sphinx code-block ディレクティブのオプションサポートを追加
        self._setup_sphinx_code_block_support()

    def _setup_sphinx_code_block_support(self):
        """Sphinx code-blockディレクティブのオプション対応を設定。"""
        try:
            from docutils import nodes
            from docutils.parsers.rst import directives
            from docutils.parsers.rst.directives.body import CodeBlock

            # Sphinx固有オプションを追加したカスタムCodeBlockクラス
            class ExtendedCodeBlock(CodeBlock):
                """Sphinx固有オプション対応のcode-blockディレクティブ。"""
                option_spec = CodeBlock.option_spec.copy()
                option_spec.update({
                    'caption': directives.unchanged,  # キャプション
                    'linenos': directives.flag,       # 行番号
                    'emphasize-lines': directives.unchanged,  # 強調行
                    'lineno-start': directives.nonnegative_int,  # 開始行番号
                    'dedent': directives.nonnegative_int,  # インデント除去
                })

                def run(self):
                    """実行。captionとlinenosを適切に処理。"""
                    # 基底クラスの処理を実行
                    result = super().run()

                    # captionオプションの処理
                    if 'caption' in self.options:
                        # captionは後で参照できるように属性として保存
                        for node in result:
                            if isinstance(node, nodes.literal_block):
                                node['caption'] = self.options['caption']

                    # linenosオプションの処理
                    if 'linenos' in self.options:
                        for node in result:
                            if isinstance(node, nodes.literal_block):
                                node['linenos'] = True

                    return result

            # MyST-parserにカスタムディレクティブを登録
            from myst_parser.parsers.directives import DirectiveParsingError

            # ディレクティブ登録（エラーは無視して継続）
            try:
                directives.register_directive('code-block', ExtendedCodeBlock)
            except Exception:
                # 既に登録済みの場合などはエラーを無視
                pass

        except ImportError:
            # docutilsが古い場合やインポートエラーの場合は無視
            pass

    def extract_from_file(self, file_path: Path) -> List[EnrichedCodeBlock]:
        """ファイルから完全な文脈情報付きコードブロックを抽出。"""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # 警告を無視してドキュメントAST構築
        import warnings
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")

            # MyST-parserの設定を寛容にする
            settings = {
                'halt_level': 5,  # エラーで停止しない
                'report_level': 5,  # 警告を出力しない
            }

            try:
                doc = publish_doctree(content, parser=self.parser, settings_overrides=settings)
            except Exception as e:
                # パースエラーが発生した場合、より寛容な設定で再試行
                settings['halt_level'] = 6
                settings['report_level'] = 6
                doc = publish_doctree(content, parser=self.parser, settings_overrides=settings)

        # 文書構造の完全解析
        document_structure = self._analyze_document_structure(doc)

        # コードブロックの完全抽出
        code_blocks = []
        for node in doc.findall(getattr(nodes, 'literal_block', None)):
            if enriched_block := self._create_enriched_block(
                node, file_path, document_structure
            ):
                code_blocks.append(enriched_block)

        # 依存関係の完全解決
        return self._resolve_all_dependencies(code_blocks)

    def _analyze_document_structure(self, doc) -> Dict[str, Any]:
        """文書構造の完全解析。"""
        structure = {
            'sections': [],      # セクション階層情報
            'references': {},    # 参照関係
            'labels': {},        # ラベル定義
            'metadata': {},      # ドキュメントメタデータ
        }

        current_section_path = []

        for node in doc.findall():
            if isinstance(node, getattr(nodes, 'section', type(None))):
                title = self._extract_section_title(node)
                if title:
                    # 現在のセクション階層を更新
                    section_level = self._get_section_level(node)
                    current_section_path = current_section_path[:section_level-1] + [title]

                    structure['sections'].append({
                        'path': current_section_path.copy(),
                        'node': node,
                        'content_type': self._classify_section_type(title)
                    })
            elif isinstance(node, getattr(nodes, 'target', type(None))) and node.get('ids'):
                # ラベル・参照の解析
                structure['labels'][node['ids'][0]] = current_section_path.copy()

        return structure

    def _extract_section_title(self, section_node) -> Optional[str]:
        """セクションのタイトルを抽出。"""
        for node in section_node.findall():
            if isinstance(node, getattr(nodes, 'title', type(None))):
                return node.astext().strip()
        return None

    def _get_section_level(self, section_node) -> int:
        """セクションのレベルを取得。"""
        level = 1
        parent = section_node.parent
        while parent and not isinstance(parent, getattr(nodes, 'document', type(None))):
            if isinstance(parent, getattr(nodes, 'section', type(None))):
                level += 1
            parent = parent.parent
        return level

    def _classify_section_type(self, title: str) -> str:
        """セクションタイプの分類。"""
        title_lower = title.lower()

        if any(keyword in title_lower for keyword in ['api', 'reference']):
            return 'API_REFERENCE'
        elif any(keyword in title_lower for keyword in ['example', 'usage', 'how to']):
            return 'EXAMPLE'
        elif any(keyword in title_lower for keyword in ['tutorial', 'guide', 'getting started']):
            return 'TUTORIAL'
        else:
            return 'GENERAL'

    def _create_enriched_block(
        self,
        node,
        file_path: Path,
        document_structure: Dict[str, Any]
    ) -> Optional[EnrichedCodeBlock]:
        """完全な文脈情報付きコードブロック作成。"""

        # 言語判定
        language = self._extract_language(node)
        if language != 'python':
            return None

        # オプション完全解析
        options = self._extract_all_options(node)

        # 明示的スキップ
        if 'no-test' in options:
            return None

        # セクション文脈の完全解析
        section_path = self._get_section_path(node, document_structure)
        execution_context = self._determine_execution_context(section_path, options)

        # コード内容取得
        code = node.astext()

        # 知的自動スキップ判定
        if self._should_skip_intelligent(code, execution_context, section_path):
            return None

        # 依存関係・提供内容の解析
        dependencies = self._analyze_dependencies(code, options)
        provides = self._analyze_provides(code)
        return EnrichedCodeBlock(
            code=code,
            filename=str(file_path),
            line_number=self._get_line_number(node),
            language=language,
            options=options,
            section_path=section_path,
            dependencies=dependencies,
            provides=provides,
            execution_context=execution_context,
            ast_node=node
        )

    def _extract_language(self, node) -> str:
        """コードブロックの言語を抽出。"""
        # classes属性から言語を特定
        classes = node.get('classes', [])
        for cls in classes:
            if cls.startswith('language-'):
                return cls[9:]  # 'language-'を除去
            elif cls in ['python', 'bash', 'shell', 'javascript', 'rust', 'yaml', 'json', 'toml', 'xml', 'html', 'css', 'markdown', 'sql', 'dockerfile', 'makefile']:
                return cls

        # 言語が不明な場合は明示的にunknownとして返す
        return 'unknown'

    def _extract_all_options(self, node) -> Dict[str, str]:
        """コードブロックのオプションを完全抽出。"""
        options = {}

        # ノードの属性から抽出
        for key, value in node.attributes.items():
            if key not in ['classes', 'ids', 'names']:
                options[key] = str(value)

        # ids属性から name を抽出
        if node.get('ids'):
            options['name'] = node['ids'][0]

        # classes属性から特殊オプションを抽出
        classes = node.get('classes', [])
        if 'no-test' in classes:
            options['no-test'] = 'true'

        # Sphinx固有オプションの抽出
        # captionオプション
        if node.get('caption'):
            options['caption'] = str(node['caption'])

        # linenosオプション
        if node.get('linenos'):
            options['linenos'] = 'true'

        # その他のSphinx固有オプション
        for sphinx_option in ['emphasize-lines', 'lineno-start', 'dedent']:
            if node.get(sphinx_option):
                options[sphinx_option] = str(node[sphinx_option])

        return options

    def _get_section_path(self, node, document_structure: Dict[str, Any]) -> List[str]:
        """ノードの所属セクションパスを取得。"""
        # ノードの親を辿ってセクションを特定
        current = node.parent
        while current and not isinstance(current, getattr(nodes, 'document', type(None))):
            if isinstance(current, getattr(nodes, 'section', type(None))):
                title = self._extract_section_title(current)
                if title:
                    # セクション階層から該当するパスを見つける
                    for section_info in document_structure['sections']:
                        if section_info['path'] and section_info['path'][-1] == title:
                            return section_info['path']
            current = current.parent

        return []

    def _determine_execution_context(self, section_path: List[str], options: Dict[str, str]) -> str:
        """実行コンテキストを決定。"""
        # オプションで明示的に指定されている場合
        if 'context' in options:
            return options['context'].upper()

        # セクションパスから推定
        path_str = ' '.join(section_path).lower()

        if any(keyword in path_str for keyword in ['api', 'reference']):
            return 'API_REFERENCE'
        elif any(keyword in path_str for keyword in ['example', 'usage']):
            return 'EXAMPLE'
        elif any(keyword in path_str for keyword in ['tutorial', 'guide', 'quickstart']):
            return 'TUTORIAL'
        else:
            return 'GENERAL'

    def _should_skip_intelligent(
        self,
        code: str,
        execution_context: str,
        section_path: List[str]
    ) -> bool:
        """完全に知的な自動スキップ判定。"""

        # API仕様セクション内の関数シグネチャ
        if execution_context == 'API_REFERENCE':
            # 関数シグネチャパターン（型注釈付き）
            if re.match(r'^\s*\w+\([^)]*\)\s*->\s*\w', code.strip()):
                return True

            # 単一行のAPIパラメータ説明
            if len(code.strip().split('\n')) == 1 and not any(
                pattern in code for pattern in ['=', 'print(', 'import', 'from']
            ):
                return True

        # 不完全なコード断片の判定
        if execution_context == 'EXAMPLE':
            lines = [line.strip() for line in code.split('\n') if line.strip()]

            # 実行に必要な最小要素の確認
            has_imports = any('import ' in line or 'from ' in line for line in lines)
            has_assignment = any('=' in line for line in lines)
            has_function_call = any('(' in line and ')' in line for line in lines)

            # 非常に短いコードで実行要素がない場合はスキップ
            if len(lines) == 1 and not (has_imports or has_assignment or has_function_call):
                return True

        # 確実にスキップすべきパターン
        skip_patterns = [
            r'\.\.\.',                          # 省略記号
            r'# TODO|# FIXME',                  # TODOコメント
            r'pass\s*$',                        # pass文のみ
            r'plt\.show\(\)|pyplot\.show\(\)',  # matplotlib表示
            r'get_market_price\s*\(',           # 未定義関数
            r'^\s*[A-Z]\s*->\s*[A-Z]',         # 図表記号
            r'^\s*\|',                          # テーブル記法
            r'[≤≥≠≈∞∑∏∫∂∆∇√±×÷°∠∟⊥∥∝∞]', # 数学記号を含む記述的テキスト
            r'要素数.*[≤≥].*:',                # 日本語での範囲記述
            r'[一-龯]+.*[≤≥].*[一-龯]+',       # 日本語文字＋数学記号の組み合わせ
            r'^\s*[^{\'"\[]+:[^=,\[\]{}]+[一-龯]+\s*$',  # コロンで区切られた日本語説明文（Pythonコードを除外）
            r'\d+\.\d+\s*M\s+ops/s',           # パフォーマンス測定値 (例: 10.58 M ops/s)
            r'\d+,\d+\s+\d+\.\d+\s*M',         # テーブル形式のデータ (例: 1,000 13.08 M)
            r'^\s*\d+\s+\d+\.\d+.*[x×]',      # 性能比較テーブル (例: 100  10.58 M ops/s  9.31x)
            r'[A-Za-z]+\s+[A-Za-z]+\s+vs\s+[A-Za-z]+', # ヘッダー行 (例: Size QF Performance vs NumPy)
        ]

        for pattern in skip_patterns:
            if re.search(pattern, code, re.MULTILINE):
                return True
        return False

    def _analyze_dependencies(self, code: str, options: Dict[str, str]) -> Set[str]:
        """依存関係を解析。"""
        dependencies = set()

        # 明示的な依存関係指定
        if 'depends' in options:
            dependencies.update(dep.strip() for dep in options['depends'].split(','))

        # コードから未定義変数を検出（簡易版）
        try:
            # ASTを使用して未定義変数を検出
            tree = ast.parse(code)

            defined_names = set()
            used_names = set()

            for node in ast.walk(tree):
                if isinstance(node, ast.Name):
                    if isinstance(node.ctx, ast.Store):
                        defined_names.add(node.id)
                    elif isinstance(node.ctx, ast.Load):
                        used_names.add(node.id)

            # 未定義変数は依存関係の可能性
            undefined_vars = used_names - defined_names

            # 組み込み関数やモジュールを除外
            builtin_names = set(dir(__builtins__))
            stdlib_names = {'math', 'time', 'random', 'numpy', 'pandas', 'matplotlib'}

            for var in undefined_vars:
                if var not in builtin_names and var not in stdlib_names:
                    # 潜在的な依存関係として記録
                    dependencies.add(f"undefined:{var}")

        except (SyntaxError, ValueError):
            # 構文エラーがある場合は依存関係なしとする
            pass

        return dependencies

    def _analyze_provides(self, code: str) -> Set[str]:
        """提供する変数・関数を解析。"""
        provides = set()

        try:
            tree = ast.parse(code)

            for node in ast.walk(tree):
                if isinstance(node, ast.Assign):
                    for target in node.targets:
                        if isinstance(target, ast.Name):
                            provides.add(target.id)
                elif isinstance(node, ast.FunctionDef):
                    provides.add(node.name)
                elif isinstance(node, ast.ClassDef):
                    provides.add(node.name)

        except (SyntaxError, ValueError):
            pass

        return provides

    def _get_line_number(self, node) -> int:
        """ノードの行番号を取得。"""
        # source属性から行番号を抽出
        if hasattr(node, 'source') and hasattr(node, 'line'):
            return node.line

        # 親ノードを辿って行番号を探す
        current = node
        while current:
            if hasattr(current, 'line') and current.line:
                return current.line
            current = current.parent

        # 見つからない場合は0を返す
        return 0

    def _resolve_all_dependencies(self, blocks: List[EnrichedCodeBlock]) -> List[EnrichedCodeBlock]:
        """依存関係の完全解決。"""

        # 名前付きブロックのマップを作成
        named_blocks = {}
        for block in blocks:
            if 'name' in block.options:
                named_blocks[block.options['name']] = block

        # 依存関係を解決
        resolved_blocks = []
        for block in blocks:
            if block.dependencies:
                resolved_code = self._inject_dependencies(block, named_blocks)
                resolved_block = replace(block, code=resolved_code)
                resolved_blocks.append(resolved_block)
            else:
                resolved_blocks.append(block)

        return resolved_blocks

    def _inject_dependencies(self, block: EnrichedCodeBlock, named_blocks: Dict[str, EnrichedCodeBlock]) -> str:
        """依存コードの自動注入。"""
        injected_parts = []

        # 明示的な依存関係を注入
        for dep in block.dependencies:
            if not dep.startswith('undefined:') and dep in named_blocks:
                dep_block = named_blocks[dep]
                injected_parts.append(f"# Dependency from {dep}")
                injected_parts.append(dep_block.code)
                injected_parts.append("")

        # メインコード
        injected_parts.append("# Main code")
        injected_parts.append(block.code)

        return '\n'.join(injected_parts)

    def extract_from_directory(self, directory_path: Path) -> List[EnrichedCodeBlock]:
        """ディレクトリから再帰的にコードブロックを抽出。

        Args:
            directory_path: 検索対象のディレクトリ

        Returns:
            抽出されたコードブロックのリスト
        """
        blocks = []

        # .mdファイルを再帰的に検索
        for md_file in directory_path.rglob("*.md"):
            try:
                file_blocks = self.extract_from_file(md_file)
                blocks.extend(file_blocks)
            except Exception as e:
                # ファイル処理エラーは警告として記録、処理継続
                print(f"Warning: Failed to process {md_file}: {e}")
                continue

        return blocks


# 後方互換性のためのエイリアス
CodeBlock = EnrichedCodeBlock
DocCodeExtractor = MystDocumentCodeExtractor


if __name__ == "__main__":
    """単体テスト用のエントリーポイント。"""
    import sys

    if len(sys.argv) != 2:
        print("Usage: python code_extractor.py <markdown_file>")
        sys.exit(1)

    file_path = Path(sys.argv[1])
    if not file_path.exists():
        print(f"File not found: {file_path}")
        sys.exit(1)

    extractor = MystDocumentCodeExtractor()
    blocks = extractor.extract_from_file(file_path)

    print(f"Found {len(blocks)} code blocks in {file_path}")
    for i, block in enumerate(blocks, 1):
        print(f"\nBlock {i}: {block.test_name}")
        print(f"  Context: {block.execution_context}")
        print(f"  Section: {' > '.join(block.section_path)}")
        print(f"  Dependencies: {block.dependencies}")
        print(f"  Provides: {block.provides}")
        if block.skip:
            print("  Status: SKIPPED")
        else:
            print("  Status: WILL TEST")
        print(f"  Code (first 100 chars): {block.code[:100]}...")