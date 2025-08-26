# [Both] Black76 API修正 - 計画通りの実装への是正

## メタデータ
- **作成日**: 2025-08-26
- **言語**: Both (Rust + Python)
- **ステータス**: DRAFT
- **推定規模**: 中規模
- **推定コード行数**: 300行
- **対象モジュール**: src/python_modules.rs, docs/api/python/

## 背景と問題

### 問題の発見
Black76実装が元の計画（`2025-08-26-multi-model-architecture.md`）と異なっている：

**計画（正しい仕様）**:
```python
# 統一された省略形パラメータ
black_scholes.call_price(s, k, t, r, sigma)  # s = spot
black76.call_price(f, k, t, r, sigma)        # f = forward
```

**現在の実装（誤り）**:
```python
black_scholes.call_price(s, k, t, r, sigma)  # ✅ 正しい
black76.call_price(forward, strike, time, rate, sigma)  # ❌ 誤り
```

### 根本原因
- 計画を参照せずに独自判断で実装
- Black-Scholesとの一貫性を確認せず
- ドキュメントファーストの原則違反

## タスク規模判定

### 判定基準
- [x] 推定コード行数: 300行
- [x] 新規ファイル数: 0個（既存ファイル修正のみ）
- [x] 影響範囲: 複数モジュール（Python API + ドキュメント）
- [x] PyO3バインディング: 必要（修正）
- [x] SIMD最適化: 不要
- [x] 並列化: 不要

### 規模判定結果
**中規模タスク**

## 修正計画

### Phase 1: ドキュメント修正（D-SSoTプロトコル適用）

#### 1.1 `docs/api/python/black76.md`
```python
# 修正前（誤り）
black76.call_price(
    forward=75.50,    # フォワード価格
    strike=70.00,     # 権利行使価格
    time=0.25,        # 満期までの時間（年）
    rate=0.05,        # リスクフリーレート
    sigma=0.3         # ボラティリティ
)

# 修正後（正しい）
black76.call_price(f, k, t, r, sigma)
# 引数:
#   f: フォワード価格
#   k: 権利行使価格（ストライク）
#   t: 満期までの時間（年）
#   r: リスクフリーレート
#   sigma: ボラティリティ

# 使用例:
black76.call_price(75.50, 70.00, 0.25, 0.05, 0.3)
```

#### 1.2 パラメータ説明の統一表
| パラメータ | Black-Scholes | Black76 | 説明 |
|-----------|--------------|---------|------|
| 第1引数 | `s` (spot) | `f` (forward) | 現在価格/フォワード価格 |
| 第2引数 | `k` | `k` | 権利行使価格 |
| 第3引数 | `t` | `t` | 満期までの時間 |
| 第4引数 | `r` | `r` | 無リスク金利 |
| 第5引数 | `sigma` | `sigma` | ボラティリティ |

### Phase 2: 実装修正

#### 2.1 `src/python_modules.rs` の修正

##### Black76関数の修正箇所:
1. `b76_call_price`: `(forward, strike, time, rate, sigma)` → `(f, k, t, r, sigma)`
2. `b76_put_price`: 同上
3. `b76_call_price_batch`: `(forwards, strike, time, rate, sigma)` → `(fs, k, t, r, sigma)`
4. `b76_put_price_batch`: 同上
5. `b76_greeks`: `(forward, strike, time, rate, sigma, is_call)` → `(f, k, t, r, sigma, is_call)`
6. `b76_implied_volatility`: `(price, forward, strike, time, rate, is_call)` → `(price, f, k, t, r, is_call)`

##### 修正例:
```rust
// 修正前
#[pyfunction]
#[pyo3(name = "call_price")]
#[pyo3(signature = (forward, strike, time, rate, sigma))]
fn b76_call_price(forward: f64, strike: f64, time: f64, rate: f64, sigma: f64) -> PyResult<f64> {
    // 内部実装
    let params = Black76Params::new(forward, strike, time, rate, sigma);
    Ok(Black76::call_price(&params))
}

// 修正後
#[pyfunction]
#[pyo3(name = "call_price")]
#[pyo3(signature = (f, k, t, r, sigma))]
fn b76_call_price(f: f64, k: f64, t: f64, r: f64, sigma: f64) -> PyResult<f64> {
    // バリデーション
    if f <= 0.0 || k <= 0.0 || t <= 0.0 || sigma <= 0.0 {
        return Err(pyo3::exceptions::PyValueError::new_err(
            "f, k, t, and sigma must be positive",
        ));
    }
    // 内部実装（forward → f に変更）
    let params = Black76Params::new(f, k, t, r, sigma);
    Ok(Black76::call_price(&params))
}
```

### Phase 3: テスト修正

#### 3.1 `tests/test_black76.py`
全テストでパラメータ名を修正：
```python
# 修正前
call_price = black76.call_price(forward, strike, time, rate, sigma)

# 修正後（変数名も統一）
f = 75.50  # forward price
k = 70.00  # strike price
t = 0.25   # time to maturity
r = 0.05   # risk-free rate
sigma = 0.3  # volatility
call_price = black76.call_price(f, k, t, r, sigma)
```

### Phase 4: 追加ドキュメント更新

#### 4.1 `docs/api/python/index.md`
```python
# モデル間の一貫したAPI
from quantforge.models import black_scholes, black76

# 統一された省略形パラメータ
bs_price = black_scholes.call_price(s, k, t, r, sigma)  # s = spot
b76_price = black76.call_price(f, k, t, r, sigma)       # f = forward
```

#### 4.2 `docs/api/python/pricing.md`
Black-Scholesの例も位置引数のみに修正（名前付き引数を削除）

## 品質管理

### 修正前の確認
```bash
# 現在の関数シグネチャを確認
uv run python -c "from quantforge.models import black76; help(black76.call_price)"
```

### 修正後のテスト
```bash
# Rustビルド
cargo build --release
cargo test --all

# Python統合
uv run maturin develop --release
uv run pytest tests/test_black76.py -v
uv run pytest tests/test_models_api.py -v

# ドキュメントビルド
uv run sphinx-build -b html docs docs/_build -W
```

## チェックリスト

### Phase 1: ドキュメント修正
- [ ] `docs/api/python/black76.md` 修正
- [ ] `docs/api/python/index.md` 修正
- [ ] `docs/api/python/pricing.md` 修正
- [ ] `docs/api/python/implied_vol.md` 確認

### Phase 2: 実装修正
- [ ] `b76_call_price` パラメータ名変更
- [ ] `b76_put_price` パラメータ名変更
- [ ] `b76_call_price_batch` パラメータ名変更
- [ ] `b76_put_price_batch` パラメータ名変更
- [ ] `b76_greeks` パラメータ名変更
- [ ] `b76_implied_volatility` パラメータ名変更

### Phase 3: テスト修正
- [ ] `tests/test_black76.py` 全テスト更新
- [ ] `playground/test_black76_integration.py` 更新

### Phase 4: 最終確認
- [ ] cargo test --all 成功
- [ ] uv run pytest 全テスト成功
- [ ] ドキュメントビルド成功（警告なし）
- [ ] 統合テスト実行

## リスクと対策

| リスク | 影響度 | 対策 |
|--------|--------|------|
| 後方互換性への影響 | なし | 位置引数のみのため影響なし |
| テスト失敗 | 低 | 単純な置換で対応可能 |
| ドキュメント不整合 | 中 | 全ドキュメントを網羅的に確認 |

## 成果物

- 統一されたAPI設計（全モデルで一貫）
- 修正されたドキュメント（実装と完全一致）
- 更新されたテスト（新しいAPI対応）
- 技術的負債ゼロの実装

## 完了条件

1. 全モデルで統一された省略形パラメータ名
2. ドキュメントと実装の完全一致
3. 全テスト成功（警告なし）
4. 将来の拡張に備えた明確なガイドライン確立

## 備考

この修正は`2025-08-26-multi-model-architecture.md`で策定された元の計画への是正である。
今後は計画を必ず参照し、独自判断での実装変更を避けること。