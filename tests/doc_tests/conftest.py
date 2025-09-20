"""ドキュメントコードテスト用のpytest設定とフィクスチャ。"""

import io
import sys
import warnings
from contextlib import contextmanager
from pathlib import Path
from typing import Dict, Any, Optional

import pytest
import numpy as np
import pyarrow as pa


def pytest_configure(config):
    """pytest設定をカスタマイズ。"""
    config.addinivalue_line(
        "markers",
        "documentation: ドキュメントコードテスト用マーカー"
    )
    config.addinivalue_line(
        "markers",
        "doc_slow: 時間のかかるドキュメントテスト"
    )


@pytest.fixture
def mock_functions():
    """ドキュメントで使用される未定義関数のモック。

    Returns:
        モック関数の辞書
    """
    def get_market_price(strike):
        """市場価格を取得する仮の関数。"""
        # ATMに近いほど価格が高くなる簡単なモデル
        base_price = 10.0
        moneyness = abs(100.0 - strike) / 100.0
        return base_price * (1.0 - moneyness * 0.5)

    return {
        'get_market_price': get_market_price,
    }


@pytest.fixture
def doc_environment(mock_functions):
    """ドキュメントコード実行用の環境。

    Args:
        mock_functions: モック関数のフィクスチャ

    Returns:
        実行環境の辞書
    """
    import quantforge
    from quantforge.models import black_scholes, black76, merton, american

    # 基本的なインポート
    env = {
        # QuantForgeモジュール
        'quantforge': quantforge,
        'black_scholes': black_scholes,
        'black76': black76,
        'merton': merton,
        'american': american,

        # 数値計算ライブラリ
        'np': np,
        'numpy': np,
        'pa': pa,
        'pyarrow': pa,

        # モック関数
        **mock_functions,

        # 標準ライブラリ
        'time': __import__('time'),
        'math': __import__('math'),
    }

    return env


@pytest.fixture
def disable_matplotlib():
    """matplotlibの表示を無効化。"""
    try:
        import matplotlib
        matplotlib.use('Agg')  # Non-interactive backend

        # plt.show()を無効化
        import matplotlib.pyplot as plt
        original_show = plt.show

        def no_show(*args, **kwargs):
            pass

        plt.show = no_show
        yield
        plt.show = original_show
    except ImportError:
        # matplotlibがインストールされていない場合はそのままパス
        yield


@contextmanager
def capture_output():
    """標準出力と標準エラー出力をキャプチャ。

    Yields:
        (stdout, stderr)のタプル
    """
    old_stdout = sys.stdout
    old_stderr = sys.stderr
    stdout = io.StringIO()
    stderr = io.StringIO()

    try:
        sys.stdout = stdout
        sys.stderr = stderr
        yield stdout, stderr
    finally:
        sys.stdout = old_stdout
        sys.stderr = old_stderr


@contextmanager
def suppress_warnings():
    """警告を抑制。"""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        yield


class CodeExecutor:
    """コード実行ヘルパークラス。"""

    def __init__(self, environment: Dict[str, Any]):
        """実行環境を初期化。

        Args:
            environment: 実行環境の辞書
        """
        self.globals = environment.copy()
        self.locals = {}

    def execute(self, code: str) -> tuple[bool, Optional[str], Optional[str]]:
        """コードを実行。

        Args:
            code: 実行するPythonコード

        Returns:
            (success, output, error)のタプル
        """
        with capture_output() as (stdout, stderr):
            try:
                # コードをコンパイル
                compiled = compile(code, '<doc_test>', 'exec')

                # 実行
                exec(compiled, self.globals, self.locals)

                # グローバル環境を更新（次のコードブロックで使用可能）
                self.globals.update(self.locals)

                return True, stdout.getvalue(), stderr.getvalue()

            except Exception as e:
                return False, stdout.getvalue(), str(e)

    def reset(self):
        """実行環境をリセット。"""
        self.locals.clear()


@pytest.fixture
def code_executor(doc_environment, disable_matplotlib):
    """コード実行環境を提供。

    Args:
        doc_environment: ドキュメント環境のフィクスチャ
        disable_matplotlib: matplotlib無効化のフィクスチャ

    Returns:
        CodeExecutorインスタンス
    """
    return CodeExecutor(doc_environment)


@pytest.fixture(scope="session")
def doc_root():
    """ドキュメントルートディレクトリ。

    Returns:
        docsディレクトリのPath
    """
    project_root = Path(__file__).parent.parent.parent
    return project_root / 'docs'


@pytest.fixture(scope="session")
def test_report_dir(tmp_path_factory):
    """テストレポート出力ディレクトリ。

    Returns:
        レポート出力用のPath
    """
    return tmp_path_factory.mktemp("doc_test_reports")


def pytest_collection_modifyitems(config, items):
    """テストアイテムを修正（スキップ条件など）。"""
    skip_slow = config.getoption("--skip-doc-slow", default=False)

    if skip_slow:
        skip_marker = pytest.mark.skip(reason="--skip-doc-slow option")
        for item in items:
            if "doc_slow" in item.keywords:
                item.add_marker(skip_marker)


def pytest_addoption(parser):
    """コマンドラインオプションを追加。"""
    parser.addoption(
        "--skip-doc-slow",
        action="store_true",
        default=False,
        help="時間のかかるドキュメントテストをスキップ"
    )
    parser.addoption(
        "--doc-report",
        action="store_true",
        default=False,
        help="ドキュメントテストの詳細レポートを生成"
    )
    parser.addoption(
        "--doc-filter",
        action="store",
        default=None,
        help="特定のドキュメントファイルのみをテスト（例: black_scholes）"
    )