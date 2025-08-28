"""QuantForge: 高性能オプション価格計算エンジン."""

# Import the Rust extension module directly
from quantforge.quantforge import models

__all__ = ["models"]

# バージョンを動的に取得（Single Source of Truth: Cargo.toml）
try:
    from importlib.metadata import PackageNotFoundError, version

    try:
        __version__ = version("quantforge")
    except PackageNotFoundError:
        # 開発環境でパッケージ未インストールの場合
        __version__ = "0.0.0+unknown"
except ImportError:
    # Python 3.7以下（サポート外だが念のため）
    __version__ = "0.0.0+unknown"
