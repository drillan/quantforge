# コントリビューションガイド

QuantForgeへの貢献を歓迎します！このガイドでは、プロジェクトへの貢献方法を説明します。

## 行動規範

- 建設的で敬意のあるコミュニケーション
- 多様性と包括性の尊重
- プロフェッショナルな振る舞い

## 貢献の種類

### 🐛 バグ報告

Issue作成時に含めるべき情報：

```{code-block} markdown
:name: contributing-code-bug-report
:caption: Bug Report Template

## 環境
- OS: [例: Ubuntu 22.04]
- Python: [例: 3.12.1]
- QuantForge: [例: 0.1.0]
- CPU: [例: Intel i9-12900K]

## 再現手順
1. ...
2. ...

## 期待される動作
...

## 実際の動作
...

## エラーメッセージ
```

### ✨ 機能提案

```{code-block} markdown
:name: contributing-code-feature-proposal
:caption: Feature Proposal Template

## 提案内容
...

## モチベーション
なぜこの機能が必要か

## 提案する API
```python
# 使用例
```

## 想定される実装
...
```

### 📝 ドキュメント改善

- 誤字脱字の修正
- 説明の改善
- 新しい例の追加
- 翻訳

## 開発フロー

### 1. 環境セットアップ

```{code-block} bash
:name: contributing-code-fork-setup
:caption: リポジトリをフォーク

# リポジトリをフォーク
git clone https://github.com/yourusername/quantforge.git
cd quantforge

# 開発ブランチ作成
git checkout -b feature/your-feature

# 開発環境構築
uv venv
source .venv/bin/activate
uv pip install -e ".[dev]"

# Rust環境
rustup update
cargo build
```

### 2. コーディング規約

#### Rust

```{code-block} rust
:name: contributing-code-rust-good
:caption: ✅ Good

// ✅ Good
pub fn calculate_price(
    spot: f64,
    strike: f64,
    rate: f64,
    vol: f64,
    time: f64,
) -> Result<f64> {
    validate_inputs(spot, strike, rate, vol, time)?;
    // ...
}

// ❌ Bad
pub fn calc(s: f64, k: f64, r: f64, v: f64, t: f64) -> f64 {
    // ...
}
```

#### Python

```{code-block} python
:name: contributing-code-python-good
:caption: ✅ Good

# ✅ Good
def calculate_implied_volatility(
    price: float,
    spot: float,
    strike: float,
    rate: float,
    time: float,
    option_type: str = "call",
) -> float:
    """
    Calculate implied volatility using Newton-Raphson method.
    
    Args:
        price: Market price of the option
        spot: Current spot price
        strike: Strike price
        rate: Risk-free rate
        time: Time to maturity in years
        option_type: "call" or "put"
    
    Returns:
        Implied volatility
    
    Raises:
        ConvergenceError: If calculation doesn't converge
    """
    # Implementation
```

### 3. テスト作成

#### Rust テスト

```{code-block} rust
:name: contributing-code-[cfg(test)]
:caption: [cfg(test)]

#[cfg(test)]
mod tests {
    use super::*;
    use approx::assert_relative_eq;
    
    #[test]
    fn test_black_scholes_call() {
        let price = black_scholes_call(100.0, 100.0, 0.05, 0.2, 1.0);
        assert_relative_eq!(price, 10.4506, epsilon = 1e-4);
    }
    
    #[test]
    #[should_panic(expected = "Invalid spot price")]
    fn test_negative_spot() {
        black_scholes_call(-100.0, 100.0, 0.05, 0.2, 1.0);
    }
}
```

#### Python テスト

```python
import pytest
import numpy as np
from quantforge.models import black_scholes

def test_black_scholes_call():
    """Test Black-Scholes call option pricing."""
    price = black_scholes.call_price(100, 100, 1.0, 0.05, 0.2)
    assert abs(price - 10.4506) < 1e-4

def test_batch_processing():
    """Test batch processing with NumPy arrays."""
    spots = np.array([95, 100, 105])
    prices = black_scholes.call_price_batch(spots, 100, 1.0, 0.05, 0.2)
    assert len(prices) == 3
    assert all(p > 0 for p in prices)

@pytest.mark.parametrize("spot,strike,time,expected", [
    (110, 100, 1.0, True),   # ITM
    (100, 100, 1.0, False),  # ATM
    (90, 100, 1.0, False),   # OTM
])
def test_moneyness(spot, strike, time, expected):
    """Test in-the-money detection via price comparison."""
    price = black_scholes.call_price(spot, strike, time, 0.05, 0.2)
    # ITM calls have intrinsic value > 0
    intrinsic = max(spot - strike, 0)
    assert (intrinsic > 0) == expected
```

### 4. ドキュメント

```{code-block} python
:name: contributing-code-new_feature
:caption: new_feature

def new_feature(param1: float, param2: str) -> dict:
    """
    Brief description of the feature.
    
    Longer description explaining the purpose
    and behavior of the function.
    
    Args:
        param1: Description of param1
        param2: Description of param2
        
    Returns:
        Dictionary containing:
            - key1: Description
            - key2: Description
    
    Raises:
        ValueError: When param1 is negative
        TypeError: When param2 is not a string
    
    Examples:
        >>> result = new_feature(10.0, "test")
        >>> print(result['key1'])
        10.0
    
    Note:
        This feature requires Python 3.12+
    
    See Also:
        related_function: For similar functionality
    """
    pass
```

### 5. コミット

```{code-block} bash
:name: contributing-code-commit-workflow
:caption: 変更の確認

# 変更の確認
git status
git diff

# テスト実行
cargo test
pytest

# フォーマット
cargo fmt
black .
isort .

# リント
cargo clippy
ruff check .

# コミット
git add -A
git commit -m "feat: Add new pricing model

- Implement Heston model
- Add tests and documentation
- Update Python bindings

Closes #123"
```

#### コミットメッセージ規約

```
<type>(<scope>): <subject>

<body>

<footer>
```

Types:
- `feat`: 新機能
- `fix`: バグ修正
- `docs`: ドキュメント
- `style`: フォーマット
- `refactor`: リファクタリング
- `test`: テスト追加
- `chore`: ビルド・ツール関連

### 6. プルリクエスト

```{code-block} markdown
:name: contributing-code-pr-template
:caption: Pull Request Template

## 概要
この PR は...

## 変更内容
- [ ] 機能Aを実装
- [ ] テストを追加
- [ ] ドキュメントを更新

## テスト
- [ ] 全テストがパス
- [ ] 新しいテストを追加
- [ ] パフォーマンステスト実施

## レビューポイント
- ファイルXの実装方針
- パフォーマンスへの影響

## スクリーンショット（該当する場合）
...

## 関連 Issue
Closes #123
```

## レビュープロセス

### レビュアーとして

- 建設的なフィードバック
- 具体的な改善提案
- 良い点も指摘

```{code-block} markdown
:name: contributing-code-feedback-example
:caption: 良いフィードバック例

# 良いフィードバック例
この実装は効率的ですね！さらに改善するなら、
ここで事前計算を使うと約20%高速化できそうです：

```rust
let sqrt_time = time.sqrt();  // 事前計算
```

# 悪いフィードバック例
このコードは遅い。
```

### 作者として

- フィードバックに感謝
- 不明点は質問
- 必要に応じて説明を追加

## リリースプロセス

1. バージョン更新
2. CHANGELOG更新
3. タグ作成
4. GitHub Release作成
5. PyPI公開

## サポート

### 質問がある場合

- [GitHub Discussions](https://github.com/yourusername/quantforge/discussions)
- [Discord](https://discord.gg/quantforge)
- [Stack Overflow](https://stackoverflow.com/questions/tagged/quantforge)

### 貢献者への謝辞

すべての貢献者に感謝します！貢献者リストは[こちら](https://github.com/yourusername/quantforge/graphs/contributors)。

## ライセンス

貢献されたコードは、プロジェクトと同じMITライセンスの下で公開されます。