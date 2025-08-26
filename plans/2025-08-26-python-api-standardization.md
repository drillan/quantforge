# Python API 引数名の業界標準化計画

## メタデータ
- **作成日**: 2025-08-26
- **ステータス**: DRAFT
- **タイプ**: API改善（Python）
- **規模**: 中（100-500行）
- **期間**: 1週間
- **優先度**: MEDIUM
- **関連文書**:
  - [Black-Scholesコア実装](./archive/2025-01-24-rust-bs-core.md)
  - README.md（サンプルコード更新対象）

## 1. 概要

### 1.1 目的
Python APIの引数名をBlack-Scholesモデルの業界標準表記に統一し、デリバティブ専門家にとって直感的なインターフェースを提供する。

### 1.2 背景
- 現在のREADME.md: `calculate_call_price(spot, strike, time, rate, vol)` - わかりやすい変数名
- 現在の実装: `calculate_call_price(s, k, t, r, v)` - 部分的に1文字だが非標準
- 業界標準: `s, k, t, r, σ(sigma)` - 学術論文・Wikipedia準拠

### 1.3 変更内容
```python
# 現在の実装
calculate_call_price(s, k, t, r, v)

# 変更後（業界標準）
calculate_call_price(s, k, t, r, sigma)
```

引数名の対応:
- `s`: Spot price（原資産価格）
- `k`: striKe price（権利行使価格）
- `t`: Time to maturity（満期までの時間）
- `r`: Risk-free rate（リスクフリーレート）
- `sigma`: volatility（ボラティリティ、業界標準記号σ）

## 2. 影響範囲分析

### 2.1 変更対象ファイル

#### Rustバインディング層
- [ ] `src/lib.rs` - 19関数の引数名変更
  - calculate_call_price
  - calculate_call_price_batch  
  - calculate_put_price
  - calculate_put_price_batch
  - calculate_delta_call
  - calculate_delta_put
  - calculate_gamma
  - calculate_vega
  - calculate_theta_call
  - calculate_theta_put
  - calculate_rho_call
  - calculate_rho_put
  - calculate_all_greeks
  - calculate_delta_call_batch
  - calculate_gamma_batch

#### Python型定義
- [ ] `python/quantforge/__init__.pyi` - 型シグネチャとdocstring更新

#### テストコード
- [ ] `tests/integration/test_integration.py`
- [ ] `tests/unit/test_black_scholes.py`
- [ ] `tests/unit/test_greeks.py`
- [ ] `tests/unit/test_implied_volatility.py`
- [ ] `tests/conftest.py` - テストヘルパー関数

#### ドキュメント
- [ ] `README.md` - サンプルコード（英語版）
- [ ] `README-ja.md` - サンプルコード（日本語版）
- [ ] `docs/models/black_scholes.md`
- [ ] `docs/api/python_api.md`

### 2.2 影響を受けない部分
- **Rust内部実装**: `bs_call_price(s, k, t, r, v)` は変更不要
- **定数定義**: そのまま維持
- **バリデーション**: ロジック変更なし

## 3. 実装計画

### Phase 1: Rustバインディング層の更新（Day 1）
1. `src/lib.rs` の全関数で引数名を `v` → `sigma` に変更
2. PyO3シグネチャの更新
3. エラーメッセージの調整

### Phase 2: Python型定義の更新（Day 1）
1. `.pyi` ファイルの引数名更新
2. docstringの引数説明を業界標準に合わせる

### Phase 3: テストコードの更新（Day 2）
1. 全テストファイルで変数名を統一
2. テスト実行して動作確認

### Phase 4: ドキュメントの更新（Day 3）
1. README.mdのサンプルコードを更新
2. APIドキュメントの更新
3. 日本語版も同時更新

### Phase 5: 品質保証（Day 4）
1. 全テスト実行
2. 品質チェック（ruff, mypy, cargo test）
3. ベンチマーク実行（性能劣化がないことを確認）

## 4. メリット・デメリット

### 4.1 メリット
✅ **業界標準準拠**: Black-Scholes論文、Wikipedia、教科書と一致
✅ **入力効率**: タイプ数約30%削減（`volatility` → `sigma`）
✅ **専門性**: デリバティブトレーダー/クォンツには直感的
✅ **一貫性**: 学術・実務の両方で使われる表記

### 4.2 デメリット
⚠️ **初心者への配慮**: `spot, strike` の方が明確
⚠️ **既存コードとの乖離**: サンプルコードの更新が必要
⚠️ **ギリシャ文字の制約**: `σ` は使えないため `sigma` を使用

### 4.3 リスクと対策
- **リスク**: 初心者が引数の意味を理解しにくい
- **対策**: docstringを充実させ、各引数の意味を明記

## 5. 代替案の検討

### 案1: 現状維持
- メリット: 変更不要、わかりやすい
- デメリット: 業界標準と乖離

### 案2: エイリアスサポート（両方受け入れ）
```python
def calculate_call_price(s=None, k=None, t=None, r=None, sigma=None,
                        spot=None, strike=None, time=None, rate=None, vol=None):
```
- メリット: 後方互換性、柔軟性
- デメリット: 実装複雑、混乱の元

### 案3: 業界標準化（採用案）
- メリット: シンプル、業界標準準拠
- デメリット: 破壊的変更（ただし既存ユーザーなし）

## 6. 検証基準

### 6.1 機能テスト
- [ ] 全既存テストがパス
- [ ] 新しい引数名でのテスト追加

### 6.2 性能テスト
- [ ] ベンチマーク結果が変更前と同等

### 6.3 ドキュメント
- [ ] 全サンプルコードが動作
- [ ] APIドキュメントの整合性

## 7. 実装チェックリスト

### 準備
- [ ] 現在の実装を確認
- [ ] 影響範囲の最終確認

### 実装
- [ ] src/lib.rs の更新
- [ ] .pyi ファイルの更新
- [ ] テストコードの更新
- [ ] ドキュメントの更新

### 検証
- [ ] cargo test --release
- [ ] uv run pytest
- [ ] uv run ruff check
- [ ] uv run mypy

### 完了
- [ ] PR作成
- [ ] レビュー＆マージ
- [ ] 計画をarchiveへ移動

## 8. 参考資料

### Black-Scholesモデル標準表記
- Wikipedia: https://en.wikipedia.org/wiki/Black%E2%80%93Scholes_model
- 原論文: Black, F., & Scholes, M. (1973)
- 業界慣習: Bloomberg Terminal, Reuters等

### 実装例
```python
# 業界標準的な使用例
from quantforge import calculate_call_price

# デリバティブトレーダーには直感的
s, k, t, r, sigma = 100.0, 105.0, 0.25, 0.05, 0.2
price = calculate_call_price(s, k, t, r, sigma)
```

## 9. 決定事項

### 採用する命名規則
- `s`: spot price（spotではない）
- `k`: strike price（strikeではない）
- `t`: time to maturity（timeではない）
- `r`: risk-free rate（rateではない）
- `sigma`: volatility（volやvではない）

### 理由
1. Black-Scholesモデルの学術的標準表記
2. 金融工学の教科書で一般的
3. 簡潔性と専門性のバランス

---

**注記**: この変更は破壊的変更だが、プロジェクトに既存ユーザーがいないため、早期に実施することで将来の技術的負債を回避する。