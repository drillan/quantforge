# [Rust] Market Pricing Utils - 市場データ仲値計算機能 実装計画

## メタデータ
- **作成日**: 2025-09-20
- **言語**: Rust
- **ステータス**: DRAFT
- **推定規模**: 中～大
- **推定コード行数**: 500-600（バッチ処理追加により増加）
- **対象モジュール**: core/src/market_utils（新規）

## タスク規模判定

### 判定基準
- [x] 推定コード行数: 500-600 行
- [x] 新規ファイル数: 5 個（mod.rs, pricing.rs, batch.rs, validation.rs, error.rs）
- [x] 影響範囲: 単一モジュール（新規モジュール）
- [x] PyO3バインディング: 必要
- [x] SIMD最適化: 不要（アンチパターンとして明記）
- [x] 並列化: 必要（バッチ処理で10,000要素以上でRayon使用）
- [x] Arrow統合: 必要（バッチ処理でArrow配列使用）

### 規模判定結果
**中～大規模タスク**

## 品質管理ツール（Rust）

### 適用ツール
| ツール | 中規模 | 実行コマンド |
|--------|--------|-------------|
| cargo test | ✅ | `cargo test --all` |
| cargo clippy | ✅ | `cargo clippy -- -D warnings` |
| cargo fmt | ✅ | `cargo fmt --check` |
| similarity-rs | 条件付き | `similarity-rs --threshold 0.80 src/` |
| rust-refactor.md | 条件付き | `.claude/commands/rust-refactor.md` 適用 |
| cargo bench | 推奨 | `cargo bench` |

## 命名定義セクション

### 4.1 使用する既存命名
```yaml
existing_names:
  # 既存のQuantForge命名規則にはmarket dataに関する定義がないため、該当なし
```

### 4.2 新規提案命名（ユーザー承認が必要）
```yaml
proposed_names:
  # 市場データパラメータ
  - name: "bid_price"
    meaning: "買い気配値"
    justification: "金融市場で一般的に使用される用語"
    references: "Hull (2018) Options, Futures, and Other Derivatives"
    status: "pending_approval"

  - name: "ask_price"
    meaning: "売り気配値"
    justification: "金融市場で一般的に使用される用語"
    references: "Hull (2018) Options, Futures, and Other Derivatives"
    status: "pending_approval"

  - name: "bid_qty"
    meaning: "買い気配数量"
    justification: "qtyは市場データAPIで一般的な省略形"
    references: "Bloomberg API, Reuters API"
    status: "pending_approval"

  - name: "ask_qty"
    meaning: "売り気配数量"
    justification: "qtyは市場データAPIで一般的な省略形"
    references: "Bloomberg API, Reuters API"
    status: "pending_approval"

  - name: "mid_price"
    meaning: "仲値"
    justification: "金融市場の標準用語"
    references: "Hull (2018), Wilmott (2006)"
    status: "pending_approval"

  - name: "spread"
    meaning: "ビッド・アスク・スプレッド"
    justification: "金融市場の標準用語"
    references: "Market Microstructure literature"
    status: "pending_approval"
```

### 4.3 命名の一貫性チェックリスト
- [x] 既存モデルとの整合性確認（新規機能のため該当なし）
- [ ] naming_conventions.mdとの一致確認（新規追加が必要）
- [ ] ドキュメントでの使用方法定義
- [x] APIパラメータは省略形を使用（qty等）
- [ ] エラーメッセージでもAPI名を使用

## 実装フェーズ（中規模）

### Phase 1: 設計（2-3時間）
- [ ] モジュール構成の設計
  - `market_utils/mod.rs` - モジュール公開インターフェース
  - `market_utils/pricing.rs` - 仲値計算ロジック（単一計算）
  - `market_utils/batch.rs` - バッチ処理実装（Arrow統合）
  - `market_utils/validation.rs` - データ検証ロジック
  - `market_utils/error.rs` - エラー型定義
- [ ] データ構造定義
  ```rust
  pub struct MarketQuote {
      pub bid_price: f64,
      pub bid_qty: Option<f64>,
      pub ask_price: f64,
      pub ask_qty: Option<f64>,
  }
  ```
- [ ] エラー型定義
  ```rust
  pub enum MarketDataError {
      InvalidPrice(String),
      InvalidQuantity(String),
      AbnormalSpread { spread: f64, threshold: f64 },
      CrossedSpread { bid: f64, ask: f64 },
  }
  ```

### Phase 2: 実装（6-8時間）

#### 基本機能実装
- [ ] **仲値計算関数**
  - `mid_price(bid: f64, ask: f64) -> f64` - デフォルト設定での計算
  - `mid_price_with_config(bid: f64, ask: f64, config: &MarketPricingConfig) -> f64` - カスタム設定
  - `weighted_mid_price(bid: f64, bid_qty: Option<f64>, ask: f64, ask_qty: Option<f64>) -> f64`
  - `weighted_mid_price_with_config(bid: f64, bid_qty: Option<f64>, ask: f64, ask_qty: Option<f64>, config: &MarketPricingConfig) -> f64`

- [ ] **スプレッド計算関数**
  - `spread(bid: f64, ask: f64) -> f64`
  - `spread_pct(bid: f64, ask: f64) -> f64`

- [ ] **設定構造体**
  ```rust
  pub struct MarketPricingConfig {
      /// スプレッド異常の閾値（None = チェックしない）
      pub max_spread_pct: Option<f64>,

      /// 異常時の処理方法
      pub abnormal_handling: AbnormalSpreadHandling,

      /// クロススプレッド（bid > ask）の処理
      pub crossed_handling: CrossedSpreadHandling,
  }

  pub enum AbnormalSpreadHandling {
      /// NaNを返す（推奨デフォルト）
      ReturnNaN,

      /// 警告ログを出して仲値を計算（リスクを理解した上で）
      LogAndContinue,

      /// エラーを返す（厳密な処理が必要な場合）
      ReturnError,
  }

  pub enum CrossedSpreadHandling {
      ReturnNaN,       // bid > askならNaN（デフォルト）
      SwapAndContinue, // bidとaskを入れ替えて継続
      ReturnError,     // エラーを返す
  }

  impl Default for MarketPricingConfig {
      fn default() -> Self {
          Self {
              max_spread_pct: Some(0.50),  // 50%をデフォルト閾値（オプション市場を考慮）
              abnormal_handling: AbnormalSpreadHandling::ReturnNaN,
              crossed_handling: CrossedSpreadHandling::ReturnNaN,
          }
      }
  }
  ```

- [ ] **データバリデーション**
  - 価格の妥当性チェック（NaN/Inf検出、負値拒否）
  - 数量の妥当性チェック（非負値、有限値）
  - クロススプレッドの検出（bid > ask）
  - 異常スプレッドの検出（ユーザー設定閾値）

#### エッジケース処理
- [ ] **オプション市場の極端なスプレッド対応**
  ```rust
  pub fn mid_price_with_config(
      bid: f64,
      ask: f64,
      config: &MarketPricingConfig,
  ) -> f64 {
      // 基本検証
      if !bid.is_finite() || !ask.is_finite() || bid < 0.0 || ask < 0.0 {
          return f64::NAN;
      }

      // クロススプレッドチェック
      if bid > ask {
          return match config.crossed_handling {
              CrossedSpreadHandling::ReturnNaN => f64::NAN,
              CrossedSpreadHandling::SwapAndContinue => {
                  warn!("Crossed spread detected: bid={}, ask={}", bid, ask);
                  (ask + bid) / 2.0  // 入れ替えて計算
              },
              CrossedSpreadHandling::ReturnError => {
                  // パニックではなく、呼び出し側でResult型を使う場合
                  f64::NAN  // または別の実装
              }
          };
      }

      // スプレッド異常チェック
      if let Some(threshold) = config.max_spread_pct {
          let mid = (bid + ask) / 2.0;
          if mid > 0.0 {
              let spread_pct = (ask - bid) / mid;
              if spread_pct > threshold {
                  return match config.abnormal_handling {
                      AbnormalSpreadHandling::ReturnNaN => f64::NAN,
                      AbnormalSpreadHandling::LogAndContinue => {
                          warn!("Abnormal spread: {:.1}% (bid={}, ask={})",
                                spread_pct * 100.0, bid, ask);
                          mid
                      },
                      AbnormalSpreadHandling::ReturnError => f64::NAN,
                  };
              }
          }
      }

      (bid + ask) / 2.0
  }
  ```

  **重要な設計判断**：
  - **UseBid/UseAsk削除**: オプション市場ではbid=1円、ask=1000円のような極端なケースがあり、片側価格の使用は危険
  - **NaNをデフォルト**: エラーではなくNaNを返すことで、大量のオプションチェーン処理で一部の異常データがあっても処理を継続可能
  - **閾値のユーザー設定**: 市場や戦略により適切な閾値が異なるため、ユーザーが設定可能に

- [ ] **データ欠損の処理**
  ```rust
  pub fn weighted_mid_price_with_config(
      bid: f64,
      bid_qty: Option<f64>,
      ask: f64,
      ask_qty: Option<f64>,
      config: &MarketPricingConfig,
  ) -> f64 {
      // 基本的な仲値チェック
      let simple_mid = mid_price_with_config(bid, ask, config);
      if simple_mid.is_nan() {
          return f64::NAN;
      }

      // 数量加重計算
      match (bid_qty, ask_qty) {
          (Some(bq), Some(aq)) if bq > 0.0 && aq > 0.0 => {
              // 通常の数量加重計算
              (bid * aq + ask * bq) / (bq + aq)
          },
          (Some(0.0), Some(aq)) if aq > 0.0 => {
              // ビッド数量ゼロの場合
              // 警告: 片側気配は流動性がないことを示す
              warn!("Zero bid quantity, using simple mid price");
              simple_mid  // askのみ使用は危険なので仲値を使用
          },
          (Some(bq), Some(0.0)) if bq > 0.0 => {
              // アスク数量ゼロの場合
              warn!("Zero ask quantity, using simple mid price");
              simple_mid  // bidのみ使用は危険なので仲値を使用
          },
          _ => {
              // 数量情報が不完全なら単純仲値
              simple_mid
          }
      }
  }
  ```

  **設計変更**: 片側数量がゼロでも片側価格を使用せず、単純仲値を使用（オプション市場での安全性を重視）

#### バッチ処理実装（新規追加）
- [ ] **Arrow統合のバッチ処理**
  ```rust
  use arrow::array::{Float64Array, ArrayRef, BooleanArray};
  use arrow::array::builder::Float64Builder;
  use std::sync::Arc;
  use rayon::prelude::*;
  use crate::constants::{get_parallel_threshold, MICRO_BATCH_THRESHOLD};

  /// バッチ仲値計算
  pub fn mid_price_batch(
      bids: &Float64Array,
      asks: &Float64Array,
  ) -> Result<ArrayRef, ArrowError> {
      mid_price_batch_with_config(bids, asks, &MarketPricingConfig::default())
  }

  /// カスタム設定でのバッチ仲値計算
  pub fn mid_price_batch_with_config(
      bids: &Float64Array,
      asks: &Float64Array,
      config: &MarketPricingConfig,
  ) -> Result<ArrayRef, ArrowError> {
      let len = validate_broadcast_compatibility(&[bids, asks])?;

      if len == 0 {
          return Ok(Arc::new(Float64Builder::new().finish()));
      }

      let mut builder = Float64Builder::with_capacity(len);

      if len >= get_parallel_threshold() {
          // 並列処理（10,000要素以上）
          let results: Vec<f64> = (0..len)
              .into_par_iter()
              .map(|i| {
                  let bid = get_scalar_or_array_value(bids, i);
                  let ask = get_scalar_or_array_value(asks, i);
                  mid_price_with_config(bid, ask, config)
              })
              .collect();

          for value in results {
              builder.append_value(value);
          }
      } else if len < MICRO_BATCH_THRESHOLD {
          // マイクロバッチ最適化（200要素以下）
          for i in 0..len {
              let bid = bids.value(i);
              let ask = asks.value(i);
              let mid = mid_price_with_config(bid, ask, config);
              builder.append_value(mid);
          }
      } else {
          // 通常の逐次処理
          for i in 0..len {
              let bid = get_scalar_or_array_value(bids, i);
              let ask = get_scalar_or_array_value(asks, i);
              let mid = mid_price_with_config(bid, ask, config);
              builder.append_value(mid);
          }
      }

      Ok(Arc::new(builder.finish()))
  }

  /// バッチ数量加重仲値計算
  pub fn weighted_mid_price_batch(
      bids: &Float64Array,
      bid_qtys: &Float64Array,
      asks: &Float64Array,
      ask_qtys: &Float64Array,
  ) -> Result<ArrayRef, ArrowError> {
      weighted_mid_price_batch_with_config(
          bids, bid_qtys, asks, ask_qtys,
          &MarketPricingConfig::default()
      )
  }

  /// カスタム設定でのバッチ数量加重仲値計算
  pub fn weighted_mid_price_batch_with_config(
      bids: &Float64Array,
      bid_qtys: &Float64Array,
      asks: &Float64Array,
      ask_qtys: &Float64Array,
      config: &MarketPricingConfig,
  ) -> Result<ArrayRef, ArrowError> {
      let len = validate_broadcast_compatibility(&[bids, bid_qtys, asks, ask_qtys])?;

      let mut builder = Float64Builder::with_capacity(len);

      if len >= get_parallel_threshold() {
          // 並列処理
          let results: Vec<f64> = (0..len)
              .into_par_iter()
              .map(|i| {
                  let bid = get_scalar_or_array_value(bids, i);
                  let bid_qty = get_scalar_or_array_value(bid_qtys, i);
                  let ask = get_scalar_or_array_value(asks, i);
                  let ask_qty = get_scalar_or_array_value(ask_qtys, i);

                  weighted_mid_price_with_config(
                      bid, Some(bid_qty), ask, Some(ask_qty), config
                  )
              })
              .collect();

          for value in results {
              builder.append_value(value);
          }
      } else {
          // 逐次処理
          for i in 0..len {
              let bid = get_scalar_or_array_value(bids, i);
              let bid_qty = get_scalar_or_array_value(bid_qtys, i);
              let ask = get_scalar_or_array_value(asks, i);
              let ask_qty = get_scalar_or_array_value(ask_qtys, i);

              let mid = weighted_mid_price_with_config(
                  bid, Some(bid_qty), ask, Some(ask_qty), config
              );
              builder.append_value(mid);
          }
      }

      Ok(Arc::new(builder.finish()))
  }

  /// バッチスプレッド計算
  pub fn spread_batch(
      bids: &Float64Array,
      asks: &Float64Array,
  ) -> Result<ArrayRef, ArrowError> {
      let len = validate_broadcast_compatibility(&[bids, asks])?;
      let mut builder = Float64Builder::with_capacity(len);

      for i in 0..len {
          let bid = get_scalar_or_array_value(bids, i);
          let ask = get_scalar_or_array_value(asks, i);
          builder.append_value(spread(bid, ask));
      }

      Ok(Arc::new(builder.finish()))
  }
  ```

- [ ] **メトリクス収集機能**
  ```rust
  pub struct BatchMetrics {
      pub total_processed: usize,
      pub nan_count: usize,
      pub abnormal_spreads: usize,
      pub crossed_spreads: usize,
      pub mean_spread_pct: f64,
      pub max_spread_pct: f64,
  }

  pub fn mid_price_batch_with_metrics(
      bids: &Float64Array,
      asks: &Float64Array,
      config: &MarketPricingConfig,
  ) -> Result<(ArrayRef, BatchMetrics), ArrowError> {
      let len = validate_broadcast_compatibility(&[bids, asks])?;

      let mut metrics = BatchMetrics {
          total_processed: len,
          nan_count: 0,
          abnormal_spreads: 0,
          crossed_spreads: 0,
          mean_spread_pct: 0.0,
          max_spread_pct: 0.0,
      };

      let mut builder = Float64Builder::with_capacity(len);
      let mut spread_sum = 0.0;
      let mut valid_count = 0;

      for i in 0..len {
          let bid = get_scalar_or_array_value(bids, i);
          let ask = get_scalar_or_array_value(asks, i);
          let mid = mid_price_with_config(bid, ask, config);

          if mid.is_nan() {
              metrics.nan_count += 1;
          }

          if bid > ask {
              metrics.crossed_spreads += 1;
          }

          let spread_pct = if bid > 0.0 && ask > 0.0 {
              (ask - bid) / ((ask + bid) / 2.0)
          } else {
              f64::NAN
          };

          if spread_pct.is_finite() {
              spread_sum += spread_pct;
              valid_count += 1;
              metrics.max_spread_pct = metrics.max_spread_pct.max(spread_pct);

              if let Some(threshold) = config.max_spread_pct {
                  if spread_pct > threshold {
                      metrics.abnormal_spreads += 1;
                  }
              }
          }

          builder.append_value(mid);
      }

      if valid_count > 0 {
          metrics.mean_spread_pct = spread_sum / valid_count as f64;
      }

      Ok((Arc::new(builder.finish()), metrics))
  }
  ```

- [ ] **ブロードキャスティングサポート**
  ```rust
  /// 配列の互換性チェックとブロードキャスティング
  pub fn validate_broadcast_compatibility(
      arrays: &[&Float64Array]
  ) -> Result<usize, ArrowError> {
      let mut max_len = 0;

      for array in arrays {
          let len = array.len();
          if len != 1 && len != max_len && max_len != 0 && max_len != 1 {
              return Err(ArrowError::InvalidArgumentError(
                  format!("Arrays have incompatible lengths for broadcasting: {} vs {}",
                          len, max_len)
              ));
          }
          max_len = max_len.max(len);
      }

      Ok(max_len)
  }

  /// スカラーまたは配列から値を取得
  pub fn get_scalar_or_array_value(array: &Float64Array, index: usize) -> f64 {
      if array.len() == 1 {
          array.value(0)
      } else {
          array.value(index)
      }
  }
  ```

#### テスト実装
- [ ] ユニットテスト作成
  - 正常ケース（通常の仲値計算）
  - エッジケース（ゼロ数量、片側気配）
  - 異常ケース（クロススプレッド、負の価格）
  - スプレッド異常検出テスト
  - **オプション市場の極端ケース**
    ```rust
    #[test]
    fn test_extreme_option_spread() {
        let config = MarketPricingConfig::default();

        // 深いOTMオプション: bid=1, ask=1000
        let mid = mid_price_with_config(1.0, 1000.0, &config);
        assert!(mid.is_nan());  // デフォルト50%閾値で異常

        // 閾値なしの設定
        let config_no_limit = MarketPricingConfig {
            max_spread_pct: None,
            ..Default::default()
        };
        let mid = mid_price_with_config(1.0, 1000.0, &config_no_limit);
        assert_eq!(mid, 500.5);

        // bid=0のケース（実際のオプション市場）
        let mid = mid_price_with_config(0.0, 100.0, &config);
        assert!(mid.is_finite());  // 0は有効な価格
    }
    ```

- [ ] プロパティベーステスト
  ```rust
  #[test]
  fn property_mid_price_is_between_bid_ask_when_valid() {
      // スプレッドが正常な場合のみ: bid <= mid <= ask
      // NaNの場合はこの性質は成立しない
  }

  #[test]
  fn property_nan_propagation() {
      // 入力にNaNがあればNaNを返すことを確認
      assert!(mid_price(f64::NAN, 100.0).is_nan());
      assert!(mid_price(100.0, f64::NAN).is_nan());
  }
  ```

- [ ] **バッチ処理テスト**
  ```rust
  #[test]
  fn test_batch_processing() {
      // 異なるサイズでのテスト
      let small_bids = Float64Array::from(vec![100.0, 101.0]);
      let small_asks = Float64Array::from(vec![100.2, 101.3]);
      let result = mid_price_batch(&small_bids, &small_asks).unwrap();
      assert_eq!(result.len(), 2);

      // 並列処理閾値テスト（10,000要素以上）
      let large_bids = Float64Array::from(vec![100.0; 15000]);
      let large_asks = Float64Array::from(vec![100.2; 15000]);
      let result = mid_price_batch(&large_bids, &large_asks).unwrap();
      assert_eq!(result.len(), 15000);
  }

  #[test]
  fn test_broadcast_compatibility() {
      // スカラーブロードキャスティング
      let bids = Float64Array::from(vec![100.0]);
      let asks = Float64Array::from(vec![100.2, 100.3, 100.4]);
      let result = mid_price_batch(&bids, &asks).unwrap();
      assert_eq!(result.len(), 3);

      // 非互換サイズのエラー
      let bids = Float64Array::from(vec![100.0, 101.0]);
      let asks = Float64Array::from(vec![100.2, 100.3, 100.4]);
      assert!(mid_price_batch(&bids, &asks).is_err());
  }

  #[test]
  fn test_metrics_collection() {
      let bids = Float64Array::from(vec![100.0, 1.0, 105.0, 100.0]);
      let asks = Float64Array::from(vec![100.2, 1000.0, 104.0, 100.5]);
      let config = MarketPricingConfig::default();

      let (result, metrics) = mid_price_batch_with_metrics(&bids, &asks, &config).unwrap();

      assert_eq!(metrics.total_processed, 4);
      assert_eq!(metrics.nan_count, 1);  // bid=1, ask=1000 で異常
      assert_eq!(metrics.crossed_spreads, 1);  // bid=105, ask=104
      assert!(metrics.abnormal_spreads > 0);
  }
  ```

### Phase 3: 品質チェック（1時間）
```bash
# 基本チェック
cargo test --all
cargo clippy -- -D warnings
cargo fmt --check

# 重複チェック
similarity-rs --threshold 0.80 --skip-test src/
# 閾値超えの重複があれば rust-refactor.md 適用
```

### Phase 4: PyO3バインディング（3時間）
- [ ] Python API設計
  ```python
  import quantforge.market_utils as market
  import numpy as np

  # 単純仲値（デフォルト設定）
  mid = market.mid_price(bid=100.2, ask=100.4)  # 100.3

  # カスタム設定での計算
  config = market.PricingConfig(
      max_spread_pct=1.0,  # 100%まで許容
      abnormal_handling='return_nan',  # 'return_nan' | 'log_and_continue' | 'return_error'
      crossed_handling='return_nan'    # 'return_nan' | 'swap_and_continue' | 'return_error'
  )
  mid = market.mid_price_with_config(bid=1.0, ask=1000.0, config=config)  # 500.5

  # 数量加重仲値
  weighted_mid = market.weighted_mid_price(
      bid_price=100.2, bid_qty=1000,
      ask_price=100.4, ask_qty=1500
  )

  # オプションチェーンの処理例
  bids = np.array([1.0, 10.0, 100.0, 1000.0])
  asks = np.array([1000.0, 11.0, 102.0, 1001.0])

  # デフォルト設定（50%閾値）
  mids = [market.mid_price(b, a) for b, a in zip(bids, asks)]
  # [nan, 10.5, 101.0, 1000.5]

  # 閾値なしで全て計算
  config_no_limit = market.PricingConfig(max_spread_pct=None)
  mids = [market.mid_price_with_config(b, a, config_no_limit)
          for b, a in zip(bids, asks)]
  # [500.5, 10.5, 101.0, 1000.5]

  # 有効な値のみフィルタリング
  valid_mids = [m for m in mids if not np.isnan(m)]
  ```

- [ ] PyO3実装
  ```rust
  #[pymodule]
  fn market_utils(_py: Python, m: &PyModule) -> PyResult<()> {
      // 単一計算関数
      m.add_function(wrap_pyfunction!(mid_price, m)?)?;
      m.add_function(wrap_pyfunction!(mid_price_with_config, m)?)?;
      m.add_function(wrap_pyfunction!(weighted_mid_price, m)?)?;
      m.add_function(wrap_pyfunction!(spread, m)?)?;
      m.add_function(wrap_pyfunction!(spread_pct, m)?)?;

      // バッチ処理関数
      m.add_function(wrap_pyfunction!(mid_price_batch, m)?)?;
      m.add_function(wrap_pyfunction!(mid_price_batch_with_config, m)?)?;
      m.add_function(wrap_pyfunction!(weighted_mid_price_batch, m)?)?;
      m.add_function(wrap_pyfunction!(spread_batch, m)?)?;

      // メトリクス付きバッチ
      m.add_function(wrap_pyfunction!(mid_price_batch_with_metrics, m)?)?;

      // 設定クラス
      m.add_class::<PyMarketPricingConfig>()?;
      m.add_class::<PyBatchMetrics>()?;

      Ok(())
  }
  ```

- [ ] Python側のテスト作成
  ```python
  # tests/unit/test_market_utils.py

  def test_batch_processing():
      """バッチ処理の動作確認"""
      import numpy as np
      import quantforge.market_utils as market

      # オプションチェーンのシミュレーション
      bids = np.array([1.0, 10.0, 100.0, 1000.0, 100.0])
      asks = np.array([1000.0, 11.0, 102.0, 1001.0, 99.0])

      # デフォルト設定（50%閾値）
      mids = market.mid_price_batch(bids, asks)

      # NaNの数を確認
      nan_count = np.isnan(mids).sum()
      assert nan_count >= 2  # 極端なスプレッドとクロススプレッド

      # 有効な値のフィルタリング
      valid_mids = mids[~np.isnan(mids)]
      assert len(valid_mids) < len(mids)

  def test_broadcast():
      """ブロードキャスティングのテスト"""
      import numpy as np
      import quantforge.market_utils as market

      # スカラーブロードキャスト
      bids = 100.0  # スカラー
      asks = np.array([100.2, 100.3, 100.4])

      mids = market.mid_price_batch(bids, asks)
      assert len(mids) == 3
      assert np.allclose(mids, [100.1, 100.15, 100.2])

  def test_metrics():
      """メトリクス収集のテスト"""
      import numpy as np
      import quantforge.market_utils as market

      # 日経225オプションのシミュレーション
      n = 100
      strikes = np.linspace(40000, 50000, n)
      atm = 45000

      # ATMからの距離に応じてスプレッドを広げる
      distance = np.abs(strikes - atm) / atm
      spread_pct = 0.002 + distance * 0.5  # 0.2% ~ 50%

      bids = strikes * (1 - spread_pct / 2)
      asks = strikes * (1 + spread_pct / 2)

      config = market.PricingConfig(max_spread_pct=0.1)  # 10%閾値
      mids, metrics = market.mid_price_batch_with_metrics(bids, asks, config)

      assert metrics.total_processed == n
      assert metrics.abnormal_spreads > 0
      assert metrics.mean_spread_pct > 0
      print(f"異常スプレッド: {metrics.abnormal_spreads}/{n}")
      print(f"平均スプレッド: {metrics.mean_spread_pct*100:.2f}%")
  ```

## 技術要件

### 必須要件
- [x] エラー率: N/A（数値計算精度は単純な算術演算）
- [x] メモリ安全性（Rust保証）
- [x] スレッド安全性（Send + Sync）

### パフォーマンス目標
- [x] 単一計算: < 10 ns（単純な算術演算）
- [x] バッチ処理（小規模）: < 0.1 ms（100件）
- [x] バッチ処理（中規模）: < 1 ms（1,000件）
- [x] バッチ処理（大規模）: < 10 ms（10,000件）
- [x] バッチ処理（並列化）: < 20 ms（100,000件）
- [x] メモリ使用量: 入力データの1.1倍（出力配列を含む）

### PyO3連携
- [x] ゼロコピー実装（スカラー値のため該当なし）
- [x] GIL解放での並列処理（将来のバッチ処理で対応）
- [x] 適切なエラー変換（MarketDataError → PyErr）

## 定数定義

```rust
// core/src/constants.rs に追加
pub mod market {
    /// デフォルトの異常スプレッド閾値（仲値に対する比率）
    /// オプション市場を考慮して50%に設定
    pub const DEFAULT_ABNORMAL_SPREAD_THRESHOLD_PCT: f64 = 0.50; // 50%

    /// クロススプレッドの許容誤差（数値誤差を考慮）
    pub const CROSS_SPREAD_TOLERANCE: f64 = 1e-10;

    /// 最小有効価格（負値チェック用、ゼロは有効）
    pub const MIN_VALID_PRICE: f64 = 0.0;

    /// 最小有効数量（負値チェック用、ゼロは有効）
    pub const MIN_VALID_QUANTITY: f64 = 0.0;
}
```

## リスクと対策

| リスク | 影響度 | 対策 |
|--------|--------|------|
| オプション市場の極端なスプレッド | 高 | NaNを返すことで安全に処理、ユーザー設定可能な閾値 |
| 片側価格使用による誤った計算 | 高 | UseBid/UseAsk機能を削除、常に仲値またはNaN |
| 市場固有ルールの混入 | 中 | 汎用的な計算のみを実装、市場固有の処理は対象外 |
| スプレッド異常の定義が不明確 | 中 | デフォルト50%、ユーザーが変更可能 |
| 数値精度の問題 | 低 | 単純な算術演算のため、f64の精度で十分 |
| PyO3での型変換オーバーヘッド | 低 | スカラー値のため影響は軽微 |

## チェックリスト

### 実装前
- [ ] naming_conventions.mdへの新規命名の追加承認
- [ ] 既存のmarket data処理コードの確認
- [ ] constants.rsへの定数追加場所の確認

### 実装中
- [ ] 定期的なテスト実行（TDD）
- [ ] コミット前の`cargo fmt`
- [ ] エッジケースの網羅的テスト

### 実装後
- [ ] 全品質ゲート通過
- [ ] Python側の統合テスト
- [ ] ドキュメント更新（使用例を含む）
- [ ] naming_conventions.mdの更新
- [ ] 計画のarchive移動

## 成果物

- [ ] 実装コード（core/src/market_utils/）
  - [ ] mod.rs - モジュール定義
  - [ ] pricing.rs - 仲値計算実装（単一計算）
  - [ ] batch.rs - バッチ処理実装（Arrow統合）
  - [ ] validation.rs - データ検証
  - [ ] error.rs - エラー型
- [ ] テストコード
  - [ ] tests/unit/test_market_utils.py - Python統合テスト
  - [ ] core/tests/test_market_utils.rs - Rustユニットテスト
- [ ] PyO3バインディング（bindings/python/src/market_utils.rs）
- [ ] ドキュメント
  - [ ] rustdoc - Rust API ドキュメント
  - [ ] Python docstring - Python APIドキュメント
  - [ ] docs/ja/api/market_utils.md - 日本語APIドキュメント
- [ ] 使用例
  - [ ] examples/market_data_usage.py - 基本使用例
  - [ ] examples/option_chain_processing.py - オプションチェーン処理例

## 備考

### 重要な設計判断の理由

#### NaNを返す設計の採用理由
1. **処理の継続性**: 100個のオプションのうち80個が異常スプレッドでも、20個の有効データで処理を続行可能
2. **IEEE 754標準**: 数値計算の標準で「計算不能」を表現する正しい方法
3. **フィルタリングの容易性**: `filter(not isnan)` で簡単に有効値のみ抽出可能
4. **エラー伝播の自然性**: NaN + 任意の値 = NaN という性質により、後続計算も自動的に無効化

#### UseBid/UseAsk削除の理由
- オプション市場の実例: bid=1円、ask=1000円
  - Bidを使用 → IV計算で0%近辺（非現実的）
  - Askを使用 → IV計算で200%以上（非現実的）
  - どちらも市場実態を反映しない危険な値

#### デフォルト閾値50%の理由
- 通常の株式/先物: スプレッド1%以下
- 流動性のあるオプション: スプレッド5-10%
- 深いOTMオプション: スプレッド50-100%以上
- → 50%はオプション市場での実用的な境界値

### アンチパターンの回避
- SIMD最適化は行わない（.claude/antipatterns/simd-optimization-trap.md参照）
- 段階的実装は避け、最初から理想形を実装（.claude/antipatterns/stage-implementation.md参照）

### バッチ処理追加の理由

#### なぜバッチ処理が必須か
1. **実用規模のデータ処理**
   - 日経225オプション: 100-500個の権利行使価格
   - 複数限月: 2-6限月
   - 合計: 400-6,000個のオプション
   - 単一計算の繰り返しでは関数呼び出しオーバーヘッドが膨大

2. **パフォーマンス向上の機会**
   - 100個: 1.5倍（キャッシュ効率）
   - 1,000個: 2-3倍（ベクトル化）
   - 10,000個: 5-10倍（並列処理）

3. **API一貫性**
   - 既存のQuantForge APIはすべてバッチ処理をサポート
   - market_utilsも同じパターンに準拠することで学習コスト削減

4. **効率的なメトリクス収集**
   - バッチ処理中に統計情報を一括収集
   - 異常スプレッドの頻度、平均スプレッド等を効率的に計算

### 将来の拡張性考慮
- VWAP/TWAP計算への拡張を考慮した設計
- Arrow配列でのバッチ処理対応（今回実装）
- 複数気配値の統合処理への拡張点を明確化
- メトリクス収集機能（今回実装）

### 参考資料
- Hull, J. C. (2018). "Options, Futures, and Other Derivatives"
- Harris, L. (2003). "Trading and Exchanges: Market Microstructure for Practitioners"
- Bloomberg/Reuters API documentation for market data conventions
- IEEE 754 Standard for Floating-Point Arithmetic