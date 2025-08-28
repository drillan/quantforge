# Configuration file for the Sphinx documentation builder.

import tomllib  # Python 3.11+
from pathlib import Path

# -- Project information -----------------------------------------------------
project = 'QuantForge'
copyright = '2025, QuantForge Team'
author = 'QuantForge Team'

# Cargo.tomlからバージョンを自動取得（Single Source of Truth）
root_dir = Path(__file__).resolve().parent.parent.parent
cargo_toml_path = root_dir / 'Cargo.toml'

with open(cargo_toml_path, 'rb') as f:
    cargo_data = tomllib.load(f)
    version = release = cargo_data['package']['version']

# -- General configuration ---------------------------------------------------
extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.napoleon',
    'sphinx.ext.viewcode',
    'sphinx.ext.mathjax',
    'myst_parser',
    'sphinx_copybutton',
]

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

# Language setting
language = 'en'

# -- Options for HTML output -------------------------------------------------
html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']
html_title = 'QuantForge Documentation'
templates_path = ['_templates']

# Theme options
html_theme_options = {
    'navigation_depth': 4,
    'collapse_navigation': False,
    'sticky_navigation': True,
    'navigation_with_keys': True,
    'includehidden': True,
    'titles_only': False,
}

# Language switcher context
html_context = {
    'display_github': True,
    'github_user': 'drillan',
    'github_repo': 'quantforge',
    'github_version': 'main',
    'conf_py_path': '/docs/en/',
    'languages': [
        ('English', '/'),
        ('日本語', '/ja/'),
    ],
    'current_language': 'English',
}

# MyST parser configuration
myst_enable_extensions = [
    "deflist",
    "tasklist",
    "html_image",
    "colon_fence",
    "smartquotes",
    "replacements",
    "linkify",
    "strikethrough",
]

# Source suffix
source_suffix = {
    '.rst': 'restructuredtext',
    '.md': 'markdown',
}