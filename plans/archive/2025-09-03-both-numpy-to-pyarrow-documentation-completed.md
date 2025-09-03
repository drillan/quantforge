# [両言語] ドキュメントNumPy→PyArrow移行計画

## メタデータ
- **作成日**: 2025-09-03
- **言語**: 両言語（ドキュメントのみ）
- **ステータス**: DRAFT
- **推定規模**: 中
- **推定コード行数**: 変更行数約500-800（ドキュメント更新）
- **対象モジュール**: docs/

## ⚠️ 技術的負債ゼロの原則

**重要**: QuantForgeはArrow-native設計を採用しており、NumPy依存を段階的に削減する必要があります。

### 現状の問題点
- ドキュメントで返り値の型が`np.ndarray`と誤記されている（実際は`arro3.core.Array`）
- サンプルコードがNumPy中心になっている
- Arrow-native設計の利点が十分に説明されていない

### 解決方針
- PyArrowを第一選択として提示
- NumPy互換性は「も使える」という位置づけに
- Arrow-nativeの利点を明確に説明

## タスク規模判定

### 判定基準
- [x] 推定変更行数: 500-800 行
- [x] 新規ファイル数: 2 個
- [x] 影響範囲: 複数モジュール（docs/全体）
- [x] Rust連携: 不要（ドキュメントのみ）
- [x] NumPy/Pandas使用: あり（サンプルコード）
- [ ] 非同期処理: 不要

### 規模判定結果
**中規模タスク**

## 命名定義セクション

### 4.1 使用する既存命名
```yaml
existing_names:
  - name: "spots"
    meaning: "スポット価格（配列）"
    source: "naming_conventions.md#バッチ処理の命名規則"
  - name: "strikes"
    meaning: "権利行使価格（配列）"
    source: "naming_conventions.md#バッチ処理の命名規則"
  - name: "times"
    meaning: "満期までの時間（配列）"
    source: "naming_conventions.md#バッチ処理の命名規則"
  - name: "rates"
    meaning: "無リスク金利（配列）"
    source: "naming_conventions.md#バッチ処理の命名規則"
  - name: "sigmas"
    meaning: "ボラティリティ（配列）"
    source: "naming_conventions.md#バッチ処理の命名規則"
```

### 4.2 新規提案命名
```yaml
proposed_names: []  # 新規命名なし（既存の命名規則に従う）
```

### 4.3 命名の一貫性チェックリスト
- [x] 既存モデルとの整合性確認
- [x] naming_conventions.mdとの一致確認
- [x] ドキュメントでの使用方法定義
- [x] APIパラメータは省略形を使用
- [x] エラーメッセージでもAPI名を使用

## フェーズ構成

### Phase 1: 現状分析と影響調査（完了）

#### 調査結果
- **NumPy使用箇所**: 約50ファイル
- **主な用途**:
  1. 返り値の型記述（誤記）: `np.ndarray` → 実際は`arro3.core.Array`
  2. サンプルコードでのデータ生成: `np.array()`, `np.random`
  3. 統計処理の例: `np.mean()`, `np.std()`
  4. 数値範囲生成: `np.linspace()`

#### 変更方針
1. **返り値の型修正**（最優先）
   - すべてのバッチ関数の返り値を正しく記載
   - `-> np.ndarray` → `-> arro3.core.Array`
   - Greeks: `Dict[str, np.ndarray]` → `Dict[str, arro3.core.Array]`

2. **サンプルコードの改善**
   - 基本例はPyArrowを使用
   - NumPy互換性も併記（「も使える」として）
   - 統計処理・乱数生成はNumPyを維持（自然な使用例）

3. **新規ドキュメント作成**
   - Arrow-native設計の説明
   - 移行ガイド

### Phase 2: APIドキュメント更新（2時間）

#### 対象ファイル（優先度順）
```
docs/ja/api/python/
├── black_scholes.md     # 返り値の型修正
├── black76.md          # 返り値の型修正
├── merton.md           # 返り値の型修正
├── american.md         # 返り値の型修正
├── batch_processing.md # 返り値の型修正、サンプル改善
├── greeks.md          # Greeks辞書の型修正
├── implied_vol.md     # 返り値の型修正
└── pricing.md         # 返り値の型修正

docs/en/api/python/      # 英語版も同様に修正
└── (同様の8ファイル)
```

#### 修正例
```markdown
# 修正前
def call_price_batch(spots, strikes, times, rates, sigmas) -> np.ndarray:

# 修正後
def call_price_batch(spots, strikes, times, rates, sigmas) -> arro3.core.Array:
    """
    バッチ処理でコールオプション価格を計算。
    
    入力: PyArrow配列、NumPy配列、またはPythonスカラーを受け付けます
    出力: arro3.core.Array（Arrow配列）を返します
    """
```

### Phase 3: ユーザーガイド更新（2-3時間）

#### 対象ファイル
```
docs/ja/
├── quickstart.md           # 基本例をPyArrowに変更
├── user_guide/
│   ├── basic_usage.md     # PyArrow優先の例に
│   ├── batch_processing.md # Arrow中心の説明に
│   ├── examples.md        # 統計処理はNumPy維持
│   └── numpy_integration.md # 既存（タイトル変更検討）
└── installation.md         # 依存関係にpyarrowを明記

docs/en/                   # 英語版も同様
└── (同様のファイル構成)
```

#### サンプルコード改善例
```python
# === 基本的な使用例 ===

# PyArrowを使用（推奨）
import pyarrow as pa
from quantforge import black_scholes

spots = pa.array([100.0, 105.0, 110.0])
prices = black_scholes.call_price_batch(spots, 100.0, 1.0, 0.05, 0.2)
# 返り値: arro3.core.Array

# NumPyも使用可能
import numpy as np
spots_np = np.array([100.0, 105.0, 110.0])
prices = black_scholes.call_price_batch(spots_np, 100.0, 1.0, 0.05, 0.2)
# 返り値: arro3.core.Array（同じ）

# Arrow配列からNumPyへの変換（必要な場合）
np_prices = np.array(prices)  # または prices.to_numpy()
```

### Phase 4: 新規ドキュメント作成（1時間）

#### 作成ファイル
1. **`docs/ja/user_guide/arrow_native_guide.md`**
   ```markdown
   # Arrow-Native設計ガイド
   
   ## なぜArrow-Nativeなのか
   - ゼロコピーFFI
   - 言語間の効率的なデータ交換
   - メモリ効率の最適化
   
   ## 利点
   - パフォーマンス: メモリコピーなし
   - 相互運用性: 多言語対応
   - 標準化: Apache Arrow標準準拠
   ```

2. **`docs/ja/migration/numpy_to_arrow.md`**
   ```markdown
   # NumPyからArrowへの移行ガイド
   
   ## 基本的な変換
   | NumPy | PyArrow |
   |-------|---------|
   | np.array([1,2,3]) | pa.array([1,2,3]) |
   | np.zeros(10) | pa.array([0]*10) |
   | np.arange(10) | pa.array(range(10)) |
   ```

### Phase 5: 高度な例の更新（1時間）

#### 方針
- **統計処理・乱数生成**: NumPy維持（自然な使用）
- **データ入力**: PyArrow例を追加
- **説明文**: Arrow-nativeの利点を明記

#### 対象ファイル
```
docs/ja/
├── models/
│   ├── black_scholes.md
│   ├── black76.md
│   └── merton.md
└── performance/
    ├── optimization.md
    └── tuning.md
```

### Phase 6: 品質チェック（30分）

#### チェック項目
- [ ] すべての返り値の型が正しく修正されているか
- [ ] PyArrowの例が適切に追加されているか
- [ ] NumPy互換性の説明が適切か
- [ ] 英語版と日本語版の一貫性
- [ ] リンク切れがないか

#### 確認コマンド
```bash
# 型の誤記が残っていないか確認
grep -r "-> np.ndarray" docs/
grep -r "Dict\[str, np.ndarray\]" docs/

# PyArrowのインポートが追加されているか
grep -r "import pyarrow" docs/ | wc -l

# 一貫性チェック
diff docs/ja/api/python/black_scholes.md docs/en/api/python/black_scholes.md
```

## リスクと対策

| リスク | 影響度 | 対策 |
|--------|--------|------|
| 既存ユーザーの混乱 | 中 | 移行ガイドを明確に提供 |
| NumPy依存の例が多い | 低 | 段階的に改善、互換性は維持 |
| ドキュメントの不整合 | 中 | 自動チェックスクリプト作成 |
| 英語/日本語版の差異 | 低 | 同時更新で対応 |

## チェックリスト

### 実装前
- [x] 現状分析完了
- [x] 影響範囲の特定
- [x] 修正方針の決定
- [ ] 命名規則の確認

### 実装中
- [ ] APIドキュメントの型修正
- [ ] サンプルコードのPyArrow化
- [ ] 新規ドキュメント作成
- [ ] 英語版の同期更新

### 実装後
- [ ] 型の誤記が完全に修正されているか
- [ ] PyArrowの例が適切か
- [ ] NumPy互換性の説明が明確か
- [ ] リンク切れチェック
- [ ] 計画のarchive移動

## 成果物

- [ ] 修正されたAPIドキュメント（16ファイル）
- [ ] 改善されたユーザーガイド（10ファイル）
- [ ] 新規Arrow-nativeガイド（2ファイル）
- [ ] 移行ガイド
- [ ] 更新されたサンプルコード

## 備考

### NumPyを維持すべき箇所
1. **統計処理**: `np.mean()`, `np.std()` - 広く知られた関数
2. **乱数生成**: `np.random` - 科学計算の標準
3. **数値範囲**: `np.linspace()` - 便利な生成関数
4. **高度な数学処理**: モンテカルロシミュレーション等

### PyArrowを優先すべき箇所
1. **基本的な配列作成**: `pa.array()`
2. **バッチ処理の入力例**
3. **パフォーマンスを重視する例**
4. **新規のサンプルコード**

### 今後の方向性
- Arrow-native設計の利点を前面に
- NumPy互換性は「も使える」という位置づけ
- 将来的にはPolars等のArrow対応ライブラリとの連携も視野に