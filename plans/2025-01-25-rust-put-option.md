# Black-Scholesプットオプション実装計画

作成日: 2025-01-25
ステータス: 実行中

## 概要

Black-Scholesモデルのプットオプション価格計算機能を実装する。現在コールオプションのみが実装されているため、プットオプションを追加し、Put-Callパリティのテストも含めて完全な実装とする。

## 実装内容

### 1. プットオプション価格計算関数

**数式**:
```
P = K * exp(-r*T) * N(-d2) - S * N(-d1)
```

where:
- S: スポット価格
- K: 権利行使価格
- r: リスクフリーレート
- T: 満期までの時間
- N: 標準正規分布の累積分布関数
- d1, d2: Black-Scholesのパラメータ

### 2. 実装ファイル

1. `src/models/black_scholes.rs`:
   - `bs_put_price()` 関数の追加
   - `bs_put_price_batch()` 関数の追加

2. `src/models/black_scholes_parallel.rs`:
   - `bs_put_price_batch_parallel()` 関数の追加

3. `src/lib.rs`:
   - `calculate_put_price()` PyO3バインディング
   - `calculate_put_price_batch()` PyO3バインディング

### 3. テスト実装

1. 単体テスト:
   - ATM/ITM/OTMプットの価格検証
   - 境界条件テスト
   - Put-Callパリティテスト

2. 統合テスト:
   - バッチ処理の一致性確認
   - 並列処理の一致性確認

## 品質基準

- [x] DRY原則遵守（共通ロジックの再利用）
- [x] ハードコード禁止（定数の適切な管理）
- [x] テスト駆動開発（Red-Green-Refactor）
- [x] 相対誤差 < PRACTICAL_TOLERANCE (1e-3)

## 実装手順

1. **仕様確認** ✓
   - Black-Scholesプット価格の数式確認
   - 既存コール実装の構造理解

2. **テスト作成（TDD Red Phase）**
   - プット価格の期待値テスト
   - Put-Callパリティテスト

3. **実装（TDD Green Phase）**
   - bs_put_price関数実装
   - バッチ処理関数実装
   - 並列処理関数実装

4. **リファクタリング（TDD Refactor Phase）**
   - 共通ロジックの抽出
   - パフォーマンス最適化

5. **PyO3バインディング**
   - Python APIの追加
   - NumPy配列対応

6. **品質保証**
   - cargo test実行
   - cargo clippy実行
   - cargo fmt実行