"""QuantForge: 高性能オプション価格計算エンジン."""

# Import the Rust extension module directly
from quantforge.quantforge import models

__all__ = ["models"]


# バージョンを動的に取得（Single Source of Truth: Cargo.toml）
def _get_version() -> str:
    """パッケージバージョンを取得する内部関数."""
    try:
        from importlib.metadata import PackageNotFoundError, version

        try:
            return version("quantforge")
        except PackageNotFoundError:
            # 開発環境でパッケージ未インストールの場合
            return "0.0.0+unknown"
    except ImportError:
        # Python 3.7以下（サポート外だが念のため）
        return "0.0.0+unknown"


__version__ = _get_version()
