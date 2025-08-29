#!/usr/bin/env python3
"""
MyST記法のname属性を既存のMarkdownドキュメントに自動追加するスクリプト

使用方法:
    python scripts/add_myst_names.py --dir docs/ja
    python scripts/add_myst_names.py --file docs/ja/models/black_scholes.md
"""

import argparse
import re
from pathlib import Path
from typing import List, Tuple
import unicodedata


def slugify(text: str) -> str:
    """テキストをスラグ化（URLフレンドリーな形式に変換）"""
    # 日本語文字を含む場合は簡略化
    if re.search(r'[ぁ-んァ-ヶ一-龠]', text):
        # 英数字とハイフンのみ抽出
        text = re.sub(r'[^a-zA-Z0-9\s-]', '', text)
    
    # NFKDで正規化
    text = unicodedata.normalize('NFKD', text)
    # ASCII文字のみ保持
    text = text.encode('ascii', 'ignore').decode('ascii')
    # 小文字化
    text = text.lower()
    # 空白をハイフンに置換
    text = re.sub(r'[\s]+', '-', text)
    # 連続するハイフンを単一に
    text = re.sub(r'-+', '-', text)
    # 前後のハイフンを削除
    text = text.strip('-')
    
    return text if text else 'section'


def extract_headers(content: str) -> List[Tuple[int, str, int]]:
    """Markdownからヘッダーを抽出
    
    Returns:
        List of (level, text, line_number)
    """
    headers = []
    lines = content.split('\n')
    
    for i, line in enumerate(lines):
        match = re.match(r'^(#{1,6})\s+(.+)$', line)
        if match:
            level = len(match.group(1))
            text = match.group(2).strip()
            headers.append((level, text, i))
    
    return headers


def extract_code_blocks(content: str) -> List[Tuple[str, str, int]]:
    """コードブロックを抽出
    
    Returns:
        List of (language, caption/first_line, line_number)
    """
    code_blocks = []
    lines = content.split('\n')
    
    i = 0
    while i < len(lines):
        line = lines[i]
        
        # コードブロックの開始を検出
        if line.startswith('```'):
            # 言語指定を取得
            lang_match = re.match(r'^```(\w+)?', line)
            language = lang_match.group(1) if lang_match and lang_match.group(1) else 'text'
            
            # 次の行からコード内容を確認
            if i + 1 < len(lines):
                next_line = lines[i + 1].strip()
                # コメントや関数定義を caption として使用
                caption = ""
                if next_line.startswith('#'):
                    caption = next_line[1:].strip()
                elif next_line.startswith('//'):
                    caption = next_line[2:].strip()
                elif 'def ' in next_line or 'function ' in next_line:
                    caption = next_line.strip()
                
                code_blocks.append((language, caption, i))
        
        i += 1
    
    return code_blocks


def generate_myst_name(file_path: Path, element_type: str, text: str, index: int) -> str:
    """MyST用のname属性を生成
    
    Args:
        file_path: ファイルパス
        element_type: 要素タイプ (header, code-block, table, etc.)
        text: 要素のテキスト
        index: 同一要素内でのインデックス
    
    Returns:
        name属性値
    """
    # ファイル名から基本名を取得
    base_name = file_path.stem.replace('_', '-')
    
    # テキストをスラグ化
    slug = slugify(text)
    if not slug:
        slug = f"{element_type}-{index}"
    
    # 名前を生成
    if element_type == 'header':
        return f"{base_name}-{slug}"
    else:
        return f"{base_name}-{element_type}-{slug}"


def add_myst_names_to_file(file_path: Path, dry_run: bool = False) -> str:
    """ファイルにMyST name属性を追加
    
    Args:
        file_path: 処理対象ファイル
        dry_run: True の場合、実際の書き込みは行わない
    
    Returns:
        処理後の内容
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    lines = content.split('\n')
    headers = extract_headers(content)
    code_blocks = extract_code_blocks(content)
    
    # 処理済み行を記録
    processed_lines = set()
    result_lines = []
    
    # ヘッダー処理
    header_counts = {}
    for level, text, line_no in headers:
        # 既にname属性がある場合はスキップ
        if line_no > 0 and lines[line_no - 1].strip().startswith('(') and lines[line_no - 1].strip().endswith(')='):
            continue
        
        # カウンタ管理
        key = slugify(text)
        header_counts[key] = header_counts.get(key, 0) + 1
        
        # name属性を生成
        name = generate_myst_name(file_path, 'header', text, header_counts[key])
        processed_lines.add(line_no)
    
    # コードブロック処理
    code_counts = {}
    for lang, caption, line_no in code_blocks:
        # 既にMyST形式の場合はスキップ
        if line_no > 0 and '```{' in lines[line_no]:
            continue
        
        key = f"{lang}-{slugify(caption)}"
        code_counts[key] = code_counts.get(key, 0) + 1
    
    # 結果を構築
    i = 0
    while i < len(lines):
        line = lines[i]
        
        # ヘッダーの処理
        header_match = re.match(r'^(#{1,6})\s+(.+)$', line)
        if header_match and i not in processed_lines:
            level = len(header_match.group(1))
            text = header_match.group(2).strip()
            
            # 前の行がname属性でない場合のみ追加
            if i == 0 or not (lines[i-1].strip().startswith('(') and lines[i-1].strip().endswith(')=')):
                name = generate_myst_name(file_path, 'header', text, 1)
                result_lines.append(f"({name})=")
        
        # コードブロックの処理
        if line.startswith('```') and not line.startswith('```{'):
            lang_match = re.match(r'^```(\w+)?', line)
            language = lang_match.group(1) if lang_match and lang_match.group(1) else 'text'
            
            # 次の行からcaptionを推測
            caption = ""
            if i + 1 < len(lines):
                next_line = lines[i + 1].strip()
                if next_line.startswith('#'):
                    caption = next_line[1:].strip()
                elif next_line.startswith('//'):
                    caption = next_line[2:].strip()
                elif 'def ' in next_line or 'function ' in next_line:
                    # 関数名を抽出
                    func_match = re.search(r'(?:def|function)\s+(\w+)', next_line)
                    if func_match:
                        caption = func_match.group(1)
            
            # MyST形式に変換
            if caption:
                name = generate_myst_name(file_path, 'code', caption, 1)
                result_lines.append(f"```{{code-block}} {language}")
                result_lines.append(f":name: {name}")
                result_lines.append(f":caption: {caption}")
                result_lines.append("")
                
                # 元の```行をスキップし、内容から開始
                i += 1
                while i < len(lines) and not lines[i].startswith('```'):
                    result_lines.append(lines[i])
                    i += 1
                # 終了の```を追加
                if i < len(lines):
                    result_lines.append(lines[i])
            else:
                result_lines.append(line)
        else:
            result_lines.append(line)
        
        i += 1
    
    result = '\n'.join(result_lines)
    
    if not dry_run:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(result)
    
    return result


def process_directory(dir_path: Path, dry_run: bool = False):
    """ディレクトリ内のすべてのMarkdownファイルを処理"""
    md_files = list(dir_path.rglob('*.md'))
    
    print(f"Found {len(md_files)} Markdown files in {dir_path}")
    
    for file_path in md_files:
        # README.md や CHANGELOG.md はスキップ
        if file_path.name in ['README.md', 'CHANGELOG.md']:
            continue
        
        print(f"Processing: {file_path.relative_to(dir_path.parent)}")
        try:
            add_myst_names_to_file(file_path, dry_run)
            if dry_run:
                print(f"  ✓ Would update {file_path.name}")
            else:
                print(f"  ✓ Updated {file_path.name}")
        except Exception as e:
            print(f"  ✗ Error: {e}")


def main():
    parser = argparse.ArgumentParser(
        description='Add MyST name attributes to Markdown documents'
    )
    parser.add_argument(
        '--file',
        type=Path,
        help='Single file to process'
    )
    parser.add_argument(
        '--dir',
        type=Path,
        help='Directory to process recursively'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be changed without modifying files'
    )
    
    args = parser.parse_args()
    
    if not args.file and not args.dir:
        parser.error('Either --file or --dir must be specified')
    
    if args.file:
        if not args.file.exists():
            print(f"Error: File {args.file} not found")
            return 1
        
        print(f"Processing single file: {args.file}")
        result = add_myst_names_to_file(args.file, args.dry_run)
        if args.dry_run:
            print("\n--- Preview ---")
            print(result[:1000] + "..." if len(result) > 1000 else result)
    
    if args.dir:
        if not args.dir.exists():
            print(f"Error: Directory {args.dir} not found")
            return 1
        
        process_directory(args.dir, args.dry_run)
    
    return 0


if __name__ == '__main__':
    exit(main())