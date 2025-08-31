# QuantForge Core + Bindings アーキテクチャ要件定義書

## 1. 概要

本文書は、QuantForgeプロジェクトをCore + Bindingsアーキテクチャに移行するための要件を定義する。

## 2. 機能要件

### 2.1 各モデルのAPI仕様

現行のドキュメント（docs/api/）に定義されたAPI仕様を完全に維持する。

#### Black-Scholesモデル
```python
# 価格計算
call_price(s, k, t, r, sigma) -> float
put_price(s, k, t, r, sigma) -> float
call_price_batch(spots, strikes, times, rates, sigmas) -> np.ndarray
put_price_batch(spots, strikes, times, rates, sigmas) -> np.ndarray

# グリークス計算
greeks(s, k, t, r, sigma, is_call) -> Dict[str, float]
greeks_batch(spots, strikes, times, rates, sigmas, is_call) -> Dict[str, np.ndarray]

# IV計算
implied_volatility(price, s, k, t, r, is_call) -> float
implied_volatility_batch(prices, spots, strikes, times, rates, is_call) -> np.ndarray
```

#### Black76モデル
```python
# 価格計算
call_price(f, k, t, r, sigma) -> float
put_price(f, k, t, r, sigma) -> float
call_price_batch(forwards, strikes, times, rates, sigmas) -> np.ndarray
put_price_batch(forwards, strikes, times, rates, sigmas) -> np.ndarray

# グリークス計算
greeks(f, k, t, r, sigma, is_call) -> Dict[str, float]
greeks_batch(forwards, strikes, times, rates, sigmas, is_call) -> Dict[str, np.ndarray]

# IV計算
implied_volatility(price, f, k, t, r, is_call) -> float
implied_volatility_batch(prices, forwards, strikes, times, rates, is_call) -> np.ndarray
```

#### Mertonモデル（配当付き）
```python
# 価格計算
call_price(s, k, t, r, q, sigma) -> float
put_price(s, k, t, r, q, sigma) -> float
call_price_batch(spots, strikes, times, rates, dividend_yields, sigmas) -> np.ndarray
put_price_batch(spots, strikes, times, rates, dividend_yields, sigmas) -> np.ndarray

# グリークス計算（dividend_rho含む）
greeks(s, k, t, r, q, sigma, is_call) -> Dict[str, float]
greeks_batch(spots, strikes, times, rates, dividend_yields, sigmas, is_call) -> Dict[str, np.ndarray]

# IV計算
implied_volatility(price, s, k, t, r, q, is_call) -> float
implied_volatility_batch(prices, spots, strikes, times, rates, dividend_yields, is_call) -> np.ndarray
```

#### Americanモデル
```python
# 価格計算
call_price(s, k, t, r, q, sigma) -> float
put_price(s, k, t, r, q, sigma) -> float
call_price_batch(spots, strikes, times, rates, dividend_yields, sigmas) -> np.ndarray
put_price_batch(spots, strikes, times, rates, dividend_yields, sigmas) -> np.ndarray

# グリークス計算
greeks(s, k, t, r, q, sigma, is_call) -> Dict[str, float]
greeks_batch(spots, strikes, times, rates, dividend_yields, sigmas, is_call) -> Dict[str, np.ndarray]

# 早期行使境界（American特有）
exercise_boundary(s, k, t, r, q, sigma, is_call) -> float
exercise_boundary_batch(spots, strikes, times, rates, dividend_yields, sigmas, is_call) -> np.ndarray

# IV計算
implied_volatility(price, s, k, t, r, q, is_call) -> float
implied_volatility_batch(prices, spots, strikes, times, rates, dividend_yields, is_call) -> np.ndarray
```

### 2.2 バッチ処理要件

- **完全配列サポート**: すべてのパラメータが配列またはスカラーを受け付ける
- **Broadcasting対応**: NumPyスタイルの自動拡張
- **並列処理**: 適切な閾値（実測ベース）での自動並列化
- **ゼロコピー最適化**: NumPy配列との効率的なデータ交換

### 2.3 エラーハンドリング要件

- **入力検証**: 負の値、NaN、無限大のチェック
- **一貫したエラーメッセージ**: パラメータ名は省略形を使用
- **適切な例外型**: ValueError、RuntimeError等の使い分け

## 3. 非機能要件

### 3.1 パフォーマンス基準

| メトリクス | 基準値 | 測定方法 |
|-----------|--------|----------|
| 単一計算 | < 10ns | ベンチマーク |
| 全Greeks | < 50ns | ベンチマーク |
| IV計算 | < 200ns | ベンチマーク |
| 100万件バッチ | < 20ms | ベンチマーク |
| NumPy比較（1M要素） | 1.4倍以上高速 | performance_guard.py |
| GILリリース率 | > 95% | py-spy |

### 3.2 メモリ使用量制限

- 100万要素処理時: < 100MB
- ゼロコピー実装の維持
- メモリリークなし

### 3.3 スレッド安全性要件

- Core層: Send + Sync実装
- Bindings層: 適切なGIL管理
- 並列処理時のデータ競合なし

## 4. アーキテクチャ要件

### 4.1 Core層要件

- **PyO3依存ゼロ**: 純粋なRust実装
- **言語非依存**: 任意の言語から利用可能な設計
- **完全なテストカバレッジ**: 90%以上
- **ドキュメント完備**: すべての公開APIにdocコメント

### 4.2 Bindings層要件

- **薄いラッパー**: ロジックはCore層に集約
- **型変換のみ**: Python型 ↔ Rust型の変換
- **エラー変換**: Rustエラー → Python例外
- **GIL管理**: 計算時の適切なリリース

### 4.3 モジュール構造要件

```
core/
├── src/
│   ├── lib.rs              # Core層のエントリポイント
│   ├── models/
│   │   ├── black_scholes.rs
│   │   ├── black76.rs
│   │   ├── merton.rs
│   │   └── american.rs
│   ├── math/               # 数学関数
│   │   ├── norm.rs         # norm_cdf, norm_pdf
│   │   └── erf.rs          # erf関数
│   ├── traits/             # 共通トレイト
│   │   └── batch.rs        # バッチ処理トレイト
│   └── error.rs            # エラー定義

bindings/python/
├── src/
│   ├── lib.rs              # PyO3モジュール定義
│   ├── models/             # 各モデルのPyO3ラッパー
│   ├── converters/         # 型変換
│   └── error.rs            # エラー変換
└── quantforge/             # Pythonパッケージ
    ├── __init__.py
    ├── models.py           # モデルAPIの公開
    └── py.typed            # 型ヒント
```

## 5. 移行要件

### 5.1 既存機能の完全維持

- すべてのAPI関数が同じシグネチャで動作
- パフォーマンスの劣化なし（1.4倍高速を維持）
- ゴールデンマスターテスト（95%カバレッジ）合格

### 5.2 段階的移行の禁止（C004原則）

- 中間状態なしの完全移行
- 旧実装と新実装の共存禁止
- 一度のリリースで完全切り替え

## 6. 品質要件

### 6.1 テスト要件

- Core層: Rustユニットテスト + property-based testing
- Bindings層: Pythonインテグレーションテスト
- E2E: ゴールデンマスターテスト
- パフォーマンス: 継続的ベンチマーク

### 6.2 ドキュメント要件

- API仕様: 完全な型定義とdocstring
- アーキテクチャ: 設計判断の記録
- 移行ガイド: 開発者向け手順書

## 7. 制約事項

### 7.1 技術的制約

- Python 3.12以上
- Rust stable（最新）
- PyO3 0.22（abi3-py312）
- NumPy 1.20以上

### 7.2 プロジェクト制約

- ユーザーゼロ前提（後方互換性不要）
- 技術的負債ゼロ（妥協実装禁止）
- 6営業日での完成

## 8. 成功基準

- [ ] Core層のPyO3依存ゼロ達成
- [ ] 全ゴールデンマスターテスト合格
- [ ] パフォーマンス基準達成（1.4倍高速維持）
- [ ] メモリ効率維持（ゼロコピー）
- [ ] ドキュメント完全性100%
- [ ] テストカバレッジ90%以上