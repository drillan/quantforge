# [両言語] ドキュメント誤記・虚偽記載修正計画

## メタデータ
- **作成日**: 2025-09-03
- **言語**: 両言語（ドキュメントのみ）
- **ステータス**: DRAFT
- **推定規模**: 小
- **推定コード行数**: 変更行数約100-150（ドキュメント修正）
- **対象モジュール**: docs/

## ⚠️ 技術的負債ゼロの原則

**重要**: ドキュメントに虚偽の記載があることは、技術的負債以上の問題です。即座に修正が必要です。

### 現状の問題点

#### 1. 未実装機能の虚偽記載
- **アジアンオプション**: 実装されていないのに「対応」と記載
- **スプレッドオプション**: 実装されていないのに「対応」と記載
- **SIMD最適化**: 2025-08-27に削除済みなのに「CPUのベクトル命令を活用」と記載

#### 2. 存在しない関数の例示
- `qf.black_scholes_call`: 実際は `black_scholes.call_price`
- `qf.calculate`: 存在しない関数
- `qf.evaluate_portfolio`: 存在しない関数

#### 3. 誤った推奨事項
- **推奨ワークフロー**: NumPy配列化が第一となっている（Arrow-native設計と矛盾）
- **移行ガイド**: 既存ユーザーがゼロなので不要かつ有害

### 解決方針
- 虚偽記載を即座に削除または修正
- 実際に存在する機能のみを記載
- Arrow-native設計に沿った正しい例を提供

## タスク規模判定

### 判定基準
- [x] 推定変更行数: 100-150 行
- [x] 新規ファイル数: 0 個
- [x] 影響範囲: 複数モジュール（docs/全体）
- [x] Rust連携: 不要（ドキュメントのみ）
- [ ] NumPy/Pandas使用: 不要
- [ ] 非同期処理: 不要

### 規模判定結果
**小規模タスク**（ただし重要度は最高）

## 命名定義セクション

### 4.1 使用する既存命名
```yaml
existing_names:
  - name: "call_price"
    meaning: "コールオプション価格計算関数"
    source: "naming_conventions.md#関数命名パターン"
  - name: "put_price"
    meaning: "プットオプション価格計算関数"
    source: "naming_conventions.md#関数命名パターン"
  - name: "greeks"
    meaning: "グリークス計算関数"
    source: "naming_conventions.md#関数命名パターン"
```

### 4.2 新規提案命名
```yaml
proposed_names: []  # 新規命名なし（既存の正しい関数名を使用）
```

### 4.3 命名の一貫性チェックリスト
- [x] 既存モデルとの整合性確認
- [x] naming_conventions.mdとの一致確認
- [x] ドキュメントでの使用方法定義
- [x] APIパラメータは省略形を使用
- [x] エラーメッセージでもAPI名を使用

## フェーズ構成

### Phase 1: 虚偽記載の削除（30分）

#### 対象ファイル
```
docs/ja/
├── index.md
│   └── Line 14: "アジアン、スプレッドオプション対応" を削除
├── user_guide/
│   ├── index.md
│   │   ├── Line 14: "アジアン、スプレッドオプション" を削除
│   │   ├── Line 25-26: Asian Options、Spread Options の行を削除
│   │   └── Line 46: "SIMD最適化: CPUのベクトル命令を活用" を削除
│   └── advanced_models.md
│       └── アジアン、スプレッドの記載があれば削除
```

#### 修正例
```markdown
# 修正前
Black-Scholes、アメリカン、アジアン、スプレッドオプション対応

# 修正後
Black-Scholes、Black76、Merton、アメリカンオプション対応
```

### Phase 2: 存在しない関数の修正（30分）

#### 対象箇所
```python
# 修正前（存在しない）
import quantforge as qf
price = qf.black_scholes_call(100, 110, 0.05, 0.2, 1.0)
prices = qf.calculate(spots, strike=100, rate=0.05, vol=0.2, time=1.0)
total_value = qf.evaluate_portfolio(portfolio, rate=0.05, vol=0.2, time=0.25)

# 修正後（正しい）
from quantforge.models import black_scholes
price = black_scholes.call_price(
    s=100.0, 
    k=110.0, 
    t=1.0, 
    r=0.05, 
    sigma=0.2
)
prices = black_scholes.call_price_batch(
    spots=spots, 
    k=100.0, 
    t=1.0, 
    r=0.05, 
    sigma=0.2
)
# evaluate_portfolioは存在しないため、例を削除または別の例に置換
```

### Phase 3: 推奨ワークフローの修正（15分）

#### 修正内容
```mermaid
# 修正前
graph TD
    A[データ準備] --> B[NumPy配列化]
    B --> C[QuantForge計算]

# 修正後
graph TD
    A[データ準備] --> B[PyArrow配列化（推奨）]
    B --> C[QuantForge計算]
    A --> D[NumPy配列化（互換性）]
    D --> C
```

### Phase 4: 移行ガイドの削除（15分）

#### 対象ファイル
- `docs/ja/api/python/batch_processing.md`
  - 「## 移行ガイド」セクション全体を削除
  - 理由: 既存ユーザーがゼロであり、移行の必要がない

### Phase 5: 実装済み機能の正確な記載（30分）

#### 実装済みモデル
1. **Black-Scholesモデル**: ヨーロピアンオプション
2. **Black76モデル**: 先物オプション
3. **Mertonモデル**: 配当付きヨーロピアンオプション
4. **アメリカンオプション**: Barone-Adesi-Whaley近似

#### パフォーマンス最適化
- **Rayonによる並列処理**: 大規模データセットの自動並列化
- **Arrow-native設計**: ゼロコピーFFI
- ~~SIMD最適化~~: 削除済み（記載しない）

### Phase 6: 品質チェック（10分）

#### チェック項目
- [ ] 未実装機能の記載がすべて削除されているか
- [ ] 存在しない関数の例がすべて修正されているか
- [ ] Arrow-native設計が正しく説明されているか
- [ ] 英語版も同様に修正されているか

#### 確認コマンド
```bash
# 誤記が残っていないか確認
grep -r "アジアン\|Asian" docs/
grep -r "スプレッド\|Spread" docs/
grep -r "SIMD" docs/
grep -r "qf\." docs/
grep -r "evaluate_portfolio" docs/
grep -r "移行ガイド" docs/
```

## リスクと対策

| リスク | 影響度 | 対策 |
|--------|--------|------|
| 誤った期待の形成 | 高 | 即座に修正、正確な機能説明 |
| 信頼性の損失 | 中 | 透明性のある修正、今後の防止策 |
| ドキュメントの不整合 | 低 | 包括的なチェックスクリプト |

## チェックリスト

### 実装前
- [x] 虚偽記載箇所の特定完了
- [x] 正しい関数名の確認
- [x] 実装済み機能の確認
- [ ] 修正方針の決定

### 実装中
- [ ] 未実装機能の記載削除
- [ ] 存在しない関数の修正
- [ ] 推奨ワークフローの更新
- [ ] 移行ガイドの削除

### 実装後
- [ ] 虚偽記載が完全に削除されているか
- [ ] すべての例が動作するか
- [ ] Arrow-native設計が正しく説明されているか
- [ ] 英語版との一貫性
- [ ] 計画のarchive移動

## 成果物

- [ ] 修正されたindex.md（虚偽機能削除）
- [ ] 修正されたuser_guide/index.md（正確な記載）
- [ ] 修正されたbatch_processing.md（移行ガイド削除）
- [ ] 正しい使用例（実際に動作するコード）

## 備考

### 削除済み機能の履歴
- **SIMD最適化**: 2025-08-27に完全削除（plans/archive/2025-08-27-rust-remove-simd-implementation.md）
  - 理由: 一度も使用されていない虚偽のドキュメント
  - 削除コード: src/simd/mod.rs（210行）

### 未実装機能
- **アジアンオプション**: 計画なし
- **スプレッドオプション**: 計画なし
- **エキゾチックオプション**: 計画なし

### 今後の防止策
1. ドキュメントレビューの強化
2. 実装とドキュメントの同期確認
3. Critical Rules遵守（C008: ドキュメント整合性絶対遵守）

### 緊急度
**最高**：虚偽記載は即座に修正が必要。ユーザーに誤った期待を与えることは最も避けるべき事態。