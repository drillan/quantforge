# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

import tomllib  # Python 3.11+
from pathlib import Path

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = "quantforge"
copyright = "2025, driller"
author = "driller"

# Cargo.tomlからバージョンを自動取得（Single Source of Truth）
root_dir = Path(__file__).resolve().parent.parent.parent
cargo_toml_path = root_dir / "Cargo.toml"

with open(cargo_toml_path, "rb") as f:
    cargo_data = tomllib.load(f)
    version = release = cargo_data["package"]["version"]

# -- Project URLs ------------------------------------------------------------
html_context = {
    "display_github": True,
    "github_user": "drillan",
    "github_repo": "quantforge",
    "github_version": "main",
    "conf_py_path": "/docs/ja/",
    "languages": [
        ("English", "../"),
        ("日本語", "/ja/"),
    ],
    "current_language": "日本語",
}

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "myst_parser",
    "sphinxcontrib.mermaid",
    "sphinx.ext.autodoc",  # APIドキュメント自動生成
    "sphinx.ext.napoleon",  # Google/NumPyスタイルdocstring
    "sphinx.ext.viewcode",  # ソースコードリンク
    "sphinx.ext.mathjax",  # 数式表示
    "sphinx_copybutton",  # コードブロックコピーボタン
    "sphinx_tabs.tabs",  # タブ表示
]

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store", "internal"]


# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "sphinx_rtd_theme"
html_static_path = ["_static"]
html_css_files = ["custom.css"]
html_title = "QuantForge ドキュメント"

# テーマ設定
html_theme_options = {
    "navigation_depth": 4,
    "collapse_navigation": False,
    "sticky_navigation": True,
    "includehidden": True,
    "titles_only": False,
}

# 言語設定
language = "ja"  # 日本語対応

# MyST Parser configuration
myst_enable_extensions = [
    "colon_fence",
    "deflist",
    "dollarmath",
    "fieldlist",
    "html_admonition",
    "html_image",
    "linkify",
    "replacements",
    "smartquotes",
    "strikethrough",
    "substitution",
    "tasklist",
]
