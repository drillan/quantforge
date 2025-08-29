# QuantForge Naming Conventions Specification

## 1. 基本原則

### 1.1 命名の哲学
- **業界標準優先**: 金融工学で確立された慣習に従う
- **簡潔性**: APIパラメータは省略形を使用
- **一貫性**: 同じ概念には必ず同じ名前を使用
- **拡張性**: 新モデル追加時も既存の規則に従う

### 1.2 命名の階層
1. **関数パラメータ**: Python API（PyO3）とRust関数の引数で使用（省略形推奨）
2. **構造体フィールド**: 内部データ構造のフィールド名（説明的な名前も可）

### 1.3 命名決定プロセス
1. 既存の命名カタログから選択
2. カタログにない場合は業界標準を調査
3. 新規命名が必要な場合はユーザー承認を取得

## 2. 命名カタログ

### 2.1 共通パラメータ（全モデル共通）

| 概念 | 関数パラメータ | 構造体フィールド（推奨） | 説明 |
|------|---------------|------------------------|------|
| 権利行使価格 | `k` | `strike` | Strike price |
| 満期までの時間 | `t` | `time` | Time to maturity (年) |
| 無リスク金利 | `r` | `rate` | Risk-free rate |
| ボラティリティ | `sigma` | `sigma` | Implied volatility |
| オプションタイプ | `is_call` | `is_call` | True=Call, False=Put |

**注**: 関数パラメータは、Python API（PyO3）とRust関数の両方で使用される名前です。

### 2.2 モデル固有パラメータ

#### Black-Scholes系
| 概念 | 関数パラメータ | 構造体フィールド（推奨） | 適用モデル |
|------|---------------|------------------------|------------|
| スポット価格 | `s` | `spot` | Black-Scholes |
| フォワード価格 | `f` | `forward` | Black76 |
| 配当利回り | `q` | `dividend_yield` | Black-Scholes (配当付き) |

#### 将来追加予定のモデル
| 概念 | 関数パラメータ | 構造体フィールド（推奨） | 適用モデル |
|------|---------------|------------------------|------------|
| バリア価格 | `b` | `barrier` | Barrier Options |
| 平均タイプ | `avg_type` | `avg_type` | Asian Options |
| サンプリング頻度 | `n` | `num_steps` または `n` | Asian Options |
| 早期行使 | `is_american` | `is_american` | American Options |
| 平均回帰率 | `kappa` | `kappa` | Heston Model |
| 長期分散 | `theta_v` | `theta_v` | Heston Model |
| ボラティリティのボラティリティ | `xi` | `xi` または `vol_of_vol` | Heston Model |
| 相関 | `rho_sv` | `rho_sv` | Stochastic Vol Models |
| ジャンプ強度 | `lambda_j` | `lambda_j` | Jump Diffusion |
| ジャンプサイズ平均 | `mu_j` | `mu_j` | Jump Diffusion |
| ジャンプサイズ分散 | `sigma_j` | `sigma_j` | Jump Diffusion |

### 2.3 関数命名パターン

#### 価格計算関数
```
{option_type}_price           # 単一計算: call_price, put_price
{option_type}_price_batch     # バッチ計算: call_price_batch
```

#### 感度計算関数
```
greeks                        # 全グリークス一括計算
calculate_{greek}             # 個別グリークス: calculate_delta
```

#### 逆算関数
```
implied_{parameter}           # パラメータ逆算: implied_volatility
```

### 2.4 構造体・クラス命名

#### Rust構造体
```
{Model}Params                 # パラメータ構造体: BlackScholesParams, Black76Params
{Model}Greeks                 # グリークス構造体: BlackScholesGreeks
{Model}Result                 # 計算結果構造体: MonteCarloResult
```

#### Pythonモジュール
```
{model_name}                  # モジュール名: black_scholes, black76 (アンダースコア)
```

## 3. 新規モデル追加時のガイドライン

### 3.1 既存カタログの優先使用
新モデル追加時は、まず既存のカタログから適切な名前を選択：
- 共通概念（strike, time等）は必ず既存の名前を使用
- モデル固有の概念も可能な限り既存パターンに従う

### 3.2 新規命名の承認プロセス
既存カタログで対応できない場合：
1. 業界標準の調査（学術論文、既存ライブラリ）
2. 命名提案の作成（理由と参考資料を含む）
3. ユーザー承認の取得
4. カタログへの追加

### 3.3 命名の一貫性チェック項目
- [ ] APIパラメータは省略形か
- [ ] 同じ概念に異なる名前を使用していないか
- [ ] 既存モデルとの整合性があるか
- [ ] ドキュメントと実装が一致しているか

## 4. 例：新モデル追加時の命名

### American Options追加の場合
```{code-block} python
:name: naming-conventions-code-python-api
:caption: Python API定義（関数パラメータは省略形）

# Python API定義（関数パラメータは省略形）
american.call_price(s, k, t, r, sigma, n_steps=100)
```

```{code-block} rust
:name: naming-conventions-code-rust
:caption: Rust実装

// Rust実装
#[pyfunction]
#[pyo3(name = "call_price")]
#[pyo3(signature = (s, k, t, r, sigma, n_steps=100))]
fn american_call_price(
    s: f64,      // spot price
    k: f64,      // strike price  
    t: f64,      // time to maturity
    r: f64,      // risk-free rate
    sigma: f64,  // volatility
    n_steps: usize,  // number of steps
) -> PyResult<f64> {
    // バリデーション
    validate_inputs(s, k, t, r, sigma)?;
    
    // 構造体作成（フィールドは説明的な名前も可）
    let params = AmericanParams {
        spot: s,      // または s をそのまま使用
        strike: k,    // または k をそのまま使用
        time: t,
        rate: r,
        sigma,
        num_steps: n_steps,
    };
    
    Ok(American::call_price(&params))
}
```

### Asian Options追加の場合
```{code-block} python
:name: naming-conventions-code-api
:caption: API定義（既存の命名規則に従う）

# API定義（既存の命名規則に従う）
asian.call_price(s, k, t, r, sigma, avg_type='arithmetic')

# avg_typeは新規だが、業界標準に従う
# 'arithmetic' | 'geometric' は一般的な分類
```

### Heston Model追加の場合
```{code-block} python
:name: naming-conventions-code-api
:caption: API定義（確立された記号を使用）

# API定義（確立された記号を使用）
heston.call_price(s, k, t, r, v0, kappa, theta_v, xi, rho_sv)

# パラメータ説明:
# v0: 初期分散
# kappa: 平均回帰率
# theta_v: 長期分散
# xi: ボラティリティのボラティリティ
# rho_sv: 株価とボラティリティの相関
```

## 5. バッチ処理の命名規則

### 配列パラメータの命名（完全配列API）
- 単数形の複数形を使用（spots, strikes, times, rates, sigmas）
- `f` の複数形は `forwards` とする（完全配列APIでは明確性優先）
- `q` の複数形は `dividend_yields` とする（説明的）
- すべてのパラメータが配列を受け付ける（Broadcasting対応）

```{code-block} python
:name: naming-conventions-code-black-scholes-batch
:caption: Black-Scholes batch（完全配列サポート）

# Black-Scholes batch（完全配列サポート）
call_prices = black_scholes.call_price_batch(
    spots=np.array([100, 105, 110]),     # 複数のスポット価格
    strikes=np.array([95, 100, 105]),    # 複数のストライク
    times=1.0,                            # スカラー（自動拡張）
    rates=0.05,                           # スカラー（自動拡張）
    sigmas=np.array([0.18, 0.20, 0.22])  # 複数のボラティリティ
)

# Black76 batch（完全配列サポート）
call_prices = black76.call_price_batch(
    forwards=np.array([100, 105, 110]),  # 複数のフォワード価格
    strikes=100.0,                        # スカラー（自動拡張）
    times=np.array([0.5, 1.0, 1.5]),     # 複数の満期
    rates=0.05,                           # スカラー（自動拡張）
    sigmas=0.2                            # スカラー（自動拡張）
)

# Merton batch（配当付き）
call_prices = merton.call_price_batch(
    spots=np.array([100, 105, 110]),
    strikes=100.0,
    times=1.0,
    rates=0.05,
    dividend_yields=np.array([0.01, 0.02, 0.03]),  # 複数の配当利回り
    sigmas=0.2
)
```

### Greeks戻り値の形式
- Dict[str, np.ndarray] 形式で返却（List[PyGreeks]は廃止）
- キー名はgreek名の小文字（'delta', 'gamma', 'vega', 'theta', 'rho'）
- モデル固有のgreek（'dividend_rho'等）も同様

```{code-block} python
:name: naming-conventions-code-section
:caption: 戻り値形式

# 戻り値形式
greeks = black_scholes.greeks_batch(...)
# {'delta': np.ndarray, 'gamma': np.ndarray, 'vega': np.ndarray, ...}
```

## 6. エラーメッセージの命名

### パラメータ名の参照
エラーメッセージでは、APIで使用される省略形を使用：

```{code-block} python
:name: naming-conventions-code-section
:caption: 良い例

# 良い例
raise ValueError("s must be positive")
raise ValueError("k, t, and sigma must be positive")

# 悪い例
raise ValueError("spot_price must be positive")  # APIと不一致
raise ValueError("strike must be positive")      # APIでは 'k' を使用
```

## 7. ドキュメントでの命名

### パラメータ説明
ドキュメントでは初出時にフルネームを併記：

```{code-block} markdown
:name: naming-conventions-code-section
:caption: 良い例

# 良い例
パラメータ: s (spot price), k (strike), t (time to maturity)

# その後の参照では省略形のみ
s = 100.0, k = 105.0
```

### コード例での命名
ドキュメント内のコード例では、API通りの省略形を使用：

```{code-block} python
:name: naming-conventions-code-api
:caption: 良い例（API通り）

# 良い例（API通り）
call_price = black_scholes.call_price(s, k, t, r, sigma)

# 悪い例（独自の変数名）
call_price = black_scholes.call_price(spot, strike, maturity, rate, vol)
```

## 8. 参考資料

### 業界標準の出典
- Hull, J. C. (2018). "Options, Futures, and Other Derivatives"
- Wilmott, P. (2006). "Paul Wilmott on Quantitative Finance"
- Haug, E. G. (2007). "The Complete Guide to Option Pricing Formulas"

### 既存ライブラリの命名規則
- QuantLib: 参考にするが、より簡潔な形を採用
- NumPy/SciPy: 配列処理の命名規則に準拠
- PyTorch/TensorFlow: バッチ処理の概念を参考

## 9. 現在の実装状況

### Black-Scholesモデル
- **関数パラメータ**: `(s, k, t, r, sigma)` - 省略形で統一
- **構造体フィールド**: `BlackScholesParams { spot, strike, time, rate, sigma }`

### Black76モデル
- **関数パラメータ**: `(f, k, t, r, sigma)` - 省略形で統一
- **構造体フィールド**: `Black76Params { forward, strike, time, rate, sigma }`

## 10. 変更履歴

| 日付 | バージョン | 変更内容 |
|------|------------|----------|
| 2025-01-26 | 1.0 | 初版作成（Black-Scholes, Black76対応） |
| 2025-01-26 | 1.1 | 「API省略形」「内部」の誤解を招く表現を修正 |