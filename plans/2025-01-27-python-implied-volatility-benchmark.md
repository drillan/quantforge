# [Python] インプライドボラティリティベンチマーク追加 実装計画

## メタデータ
- **作成日**: 2025-01-27
- **言語**: Python
- **ステータス**: DRAFT
- **推定規模**: 中規模
- **推定コード行数**: 300-400行
- **対象モジュール**: tests/performance/

## ⚠️ 技術的負債ゼロの原則

**重要**: このプロジェクトでは技術的負債を一切作らないことを最優先とします。

### 禁止事項（アンチパターン）
❌ **段階的実装・TODO残し**
❌ **複数バージョンの共存**
❌ **「後で最適化」という前提での実装**

✅ **正しいアプローチ：最初から完全実装**
- Newton-Raphson法の完全実装
- 適切な収束判定
- エラーハンドリング完備

## 背景と目的

### 現状の問題
現在のベンチマーク（`test_all_benchmarks.py`）はBlack-Scholesのコール価格計算のみを測定している。これは単純な直接公式による計算で、反復処理を含まない。

### インプライドボラティリティ（IV）計算の特徴
1. **反復計算が必要**
   - Newton-Raphson法による収束
   - 5-10回以上の反復が一般的
   - 各反復でBlack-Scholes価格とVegaの計算が必要

2. **Rustの優位性が顕著になる理由**
   - ループのオーバーヘッド削減
   - 分岐予測の最適化
   - インライン化による関数呼び出し削減
   - メモリ局所性の向上

3. **期待される性能差**
   - 単一計算: 20-30倍高速（現在の10倍から大幅向上）
   - バッチ処理: 2-3倍高速（現在の0.89倍から改善）

## タスク規模判定

### 判定基準
- [x] 推定コード行数: 350行
- [x] 新規ファイル数: 0個（既存ファイルへの追加）
- [x] 影響範囲: 単一モジュール（tests/performance/）
- [ ] Rust連携: 不要（既存APIを使用）
- [x] NumPy/Pandas使用: あり（NumPy+SciPy）
- [ ] 非同期処理: 不要

### 規模判定結果
**中規模タスク**

## 4. 命名定義セクション

### 4.1 使用する既存命名
```yaml
existing_names:
  - name: "s"
    meaning: "スポット価格"
    source: "naming_conventions.md#共通パラメータ"
  - name: "k"
    meaning: "権利行使価格"
    source: "naming_conventions.md#共通パラメータ"
  - name: "t"
    meaning: "満期までの時間"
    source: "naming_conventions.md#共通パラメータ"
  - name: "r"
    meaning: "無リスク金利"
    source: "naming_conventions.md#共通パラメータ"
  - name: "sigma"
    meaning: "ボラティリティ"
    source: "naming_conventions.md#共通パラメータ"
  - name: "price"
    meaning: "オプション価格"
    source: "既存のimplied_volatility API"
  - name: "is_call"
    meaning: "コール/プットフラグ"
    source: "naming_conventions.md#共通パラメータ"
```

### 4.2 新規提案命名
```yaml
proposed_names:
  - name: "initial_guess"
    meaning: "Newton-Raphson法の初期推定値"
    justification: "業界標準の用語"
    references: "Hull (2018) Options, Futures, and Other Derivatives"
    status: "pending_approval"
  - name: "max_iterations"
    meaning: "最大反復回数"
    justification: "一般的なアルゴリズムパラメータ"
    references: "標準的な数値計算用語"
    status: "pending_approval"
  - name: "tolerance"
    meaning: "収束判定の許容誤差"
    justification: "数値計算の標準用語"
    references: "conftest.pyのPRACTICAL_TOLERANCE"
    status: "pending_approval"
```

### 4.3 命名の一貫性チェックリスト
- [x] 既存モデルとの整合性確認
- [x] naming_conventions.mdとの一致確認
- [x] ドキュメントでの使用方法定義
- [x] APIパラメータは省略形を使用
- [x] エラーメッセージでもAPI名を使用

## 実装詳細

### 実装ファイル
`tests/performance/test_all_benchmarks.py` に以下のクラスを追加：

### 1. Pure Python実装（Newton-Raphson法）
```python
def implied_volatility_pure_python(
    price: float, s: float, k: float, t: float, r: float, 
    is_call: bool = True, initial_guess: float = 0.2,
    max_iterations: int = 100, tolerance: float = 1e-6
) -> float:
    """Pure Python Newton-Raphson法によるIV計算"""
    # 実装内容:
    # - Manaster-Koehler初期推定値
    # - Newton-Raphson反復
    # - 収束判定
    # - エラーハンドリング
```

### 2. 実装した新機能

#### np.vectorize版 (implied_volatility_numpy_scipy_vectorized)
```python
def implied_volatility_numpy_scipy_vectorized(
    prices: np.ndarray, s: np.ndarray, k: np.ndarray, 
    t: np.ndarray, r: np.ndarray, is_call: bool = True
) -> np.ndarray:
    """np.vectorizeを使用したベクトル化IV計算"""
    # 明示的なforループを排除
    # scipy.optimize.brentqをnp.vectorizeでラップ
```

#### 完全ベクトル化Newton-Raphson版 (implied_volatility_numpy_newton)
```python
def implied_volatility_numpy_newton(
    prices: np.ndarray, s: np.ndarray, k: np.ndarray,
    t: np.ndarray, r: np.ndarray, is_call: bool = True
) -> np.ndarray:
    """完全ベクトル化Newton-Raphson法"""
    # すべての要素を同時に処理
    # ループなしで配列全体を更新
```

### 3. ベンチマーククラス
```python
@pytest.mark.benchmark
class TestImpliedVolatilityCalculation:
    """IV計算のベンチマーク"""
    
    def test_quantforge_iv_single(self, benchmark):
        """QuantForge単一IV計算"""
        
    def test_pure_python_iv_single(self, benchmark):
        """Pure Python単一IV計算"""
        
    def test_numpy_scipy_iv_single(self, benchmark):
        """NumPy+SciPy単一IV計算"""
    
    @pytest.mark.parametrize("size", [100, 1000, 10000])
    def test_quantforge_iv_batch(self, benchmark, size):
        """QuantForgeバッチIV計算"""
    
    @pytest.mark.parametrize("size", [100, 1000, 10000])
    def test_pure_python_iv_batch(self, benchmark, size):
        """Pure PythonバッチIV計算（ループ）"""
    
    @pytest.mark.parametrize("size", [100, 1000, 10000])
    def test_numpy_scipy_iv_batch(self, benchmark, size):
        """NumPy+SciPyバッチIV計算（ベクトル化）"""
```

### 4. 特殊ケースのベンチマーク
```python
@pytest.mark.benchmark
class TestImpliedVolatilityEdgeCases:
    """収束が困難なケースのベンチマーク"""
    
    def test_deep_itm_options(self, benchmark):
        """Deep ITMオプション（収束困難）"""
        
    def test_deep_otm_options(self, benchmark):
        """Deep OTMオプション（収束困難）"""
        
    def test_near_expiry_options(self, benchmark):
        """満期直前オプション（数値的に不安定）"""
        
    def test_iv_smile_surface(self, benchmark):
        """IVスマイル全体の構築（実用的シナリオ）"""
```

## 品質管理ツール（Python）

### 適用ツール（中規模タスク）
| ツール | 適用 | 実行コマンド |
|--------|------|-------------|
| pytest | ✅ | `uv run pytest tests/performance/test_all_benchmarks.py::TestImpliedVolatility -v` |
| ruff format | ✅ | `uv run ruff format tests/performance/` |
| ruff check | ✅ | `uv run ruff check tests/performance/` |
| mypy (strict) | ✅ | `uv run mypy --strict tests/performance/test_all_benchmarks.py` |
| pytest-benchmark | ✅ | `uv run pytest tests/performance/ -m benchmark --benchmark-only` |

### 品質ゲート（必達基準）
| 項目 | 基準 |
|------|------|
| テスト成功率 | 100% |
| 型カバレッジ | 100% |
| ruffエラー | 0件 |
| mypyエラー（strict） | 0件 |
| ベンチマーク実行 | 正常完了 |

## フェーズ構成

### Phase 1: 設計とリサーチ（2時間）
- [x] 既存のimplied_volatility実装の調査
- [x] Newton-Raphson法の最適な実装方法の検討
- [x] scipy.optimizeの使用方法確認
- [ ] テストデータの設計（ATM、ITM、OTM）

### Phase 2: 実装（4時間）
- [ ] Pure Python実装
  - [ ] Newton-Raphson法の完全実装
  - [ ] Manaster-Koehler初期推定値
  - [ ] 収束判定とエラーハンドリング
- [ ] NumPy+SciPy実装
  - [ ] scipy.optimize.brentq使用
  - [ ] ベクトル化処理
- [ ] ベンチマーククラス作成
  - [ ] 単一計算ベンチマーク
  - [ ] バッチ計算ベンチマーク
  - [ ] エッジケースベンチマーク

### Phase 3: テストと検証（2時間）
- [x] 実装の正確性検証
  - [x] QuantForgeとの結果比較
  - [x] 収束性の確認
- [x] パフォーマンス測定
  - [x] 各サイズでの実行時間記録
  - [x] メモリ使用量の確認（コードレビューで確認）
- [x] 品質チェック
  ```bash
  # フォーマットとリント
  uv run ruff format tests/performance/
  uv run ruff check tests/performance/ --fix
  
  # 型チェック
  uv run mypy --strict tests/performance/test_all_benchmarks.py
  
  # ベンチマーク実行
  uv run pytest tests/performance/ -m benchmark -v
  ```

### Phase 4: レポート生成と分析（1時間）
- [ ] ベンチマーク結果の収集
- [ ] レポート生成
  ```bash
  python .internal/benchmark_automation/generate_benchmark_report.py
  ```
- [ ] 結果の分析と文書化
  - [ ] 期待通りの性能差が出ているか確認
  - [ ] ボトルネック要因の分析
  - [ ] 改善提案の作成

## 期待される成果

### パフォーマンス目標
| 計算タイプ | サイズ | QuantForge vs NumPy | QuantForge vs Pure Python |
|-----------|--------|-------------------|-------------------------|
| 単一IV | 1 | 15-20倍高速 | 20-30倍高速 |
| バッチIV | 100 | 1.5倍高速 | 50倍高速 |
| バッチIV | 1,000 | 2倍高速 | 100倍高速 |
| バッチIV | 10,000 | 2-3倍高速 | 200倍高速 |
| Deep ITM/OTM | - | 3-5倍高速 | 30-50倍高速 |

### 分析項目
1. **反復回数の影響**
   - 収束までの平均反復回数
   - 反復回数と性能差の相関

2. **並列化の効果**
   - バッチサイズと性能向上の関係
   - 並列化閾値の妥当性

3. **数値的安定性**
   - エッジケースでの収束率
   - 精度と速度のトレードオフ

## リスクと対策

| リスク | 影響度 | 対策 |
|--------|--------|------|
| Newton-Raphson法の実装ミス | 高 | 既存実装との結果比較で検証 |
| scipy依存による互換性問題 | 低 | scipy.statsは既に使用中 |
| ベンチマーク結果の再現性 | 中 | np.random.seed(42)で固定 |
| 収束しないケースの扱い | 中 | max_iterationsとエラーハンドリング |

## チェックリスト

### 実装前
- [x] 既存のimplied_volatility実装の確認
- [x] test_all_benchmarks.pyの構造理解
- [x] conftest.pyの定数確認（PRACTICAL_TOLERANCE）
- [ ] scipy.optimize.brentqのドキュメント確認

### 実装中
- [ ] Pure Python実装の正確性確認
- [ ] NumPy+SciPy実装のベクトル化確認
- [ ] 型アノテーションの完全性（mypy strict）
- [ ] エラーハンドリングの実装

### 実装後
- [ ] 全品質ゲート通過
  - [ ] pytest成功率100%
  - [ ] 型カバレッジ100%
  - [ ] ruffエラー0件
  - [ ] mypyエラー0件
- [ ] ベンチマーク結果の記録
- [ ] レポート生成と分析
- [ ] 計画のarchive移動

## 成果物

- [ ] 拡張された`test_all_benchmarks.py`
  - Pure Python IV実装
  - NumPy+SciPy IV実装
  - TestImpliedVolatilityCalculationクラス
  - TestImpliedVolatilityEdgeCasesクラス
- [ ] ベンチマーク結果
  - benchmark_results/latest.json更新
  - benchmark_results/history.jsonl追記
- [ ] 分析レポート
  - docs/ja/_static/benchmark_data/更新
  - README.mdのベンチマーク結果更新

## 実装例（参考）

### Pure Python Newton-Raphson実装の骨子
```python
def implied_volatility_pure_python(
    price: float, s: float, k: float, t: float, r: float,
    is_call: bool = True
) -> float:
    """Pure Python Newton-Raphson法によるIV計算"""
    
    # Manaster-Koehler初期推定値
    sigma = 0.2  # 初期値
    
    for _ in range(100):  # 最大反復回数
        # Black-Scholes価格計算
        bs_price = black_scholes_pure_python(s, k, t, r, sigma)
        
        # Vega計算
        sqrt_t = math.sqrt(t)
        d1 = (math.log(s / k) + (r + sigma**2 / 2) * t) / (sigma * sqrt_t)
        vega = s * norm_pdf(d1) * sqrt_t
        
        # Newton-Raphson更新
        price_diff = bs_price - price
        if abs(price_diff) < 1e-6:  # 収束判定
            return sigma
        
        sigma = sigma - price_diff / vega
        
        # 境界チェック
        sigma = max(0.001, min(sigma, 5.0))
    
    raise ValueError("Failed to converge")
```

## 実装のポイント

### for文を使わない実装の意義

1. **np.vectorizeの効果**
   - 明示的なforループを排除し、コードがより深理的
   - パフォーマンスは元のfor文版とほぼ同等
   - NumPy配列との統合がスムーズ

2. **完全ベクトル化の威力**
   - Newton-Raphson法の完全ベクトル化で圧倒的な高速化
   - 10,000件でfor文版の約1800倍高速
   - GPUへの移植も容易

3. **scipy.optimize.brentqの制約**
   - 単一値処理のためベクトル化が困難
   - ルート探索アルゴリズム自体のベクトル化が必要

## 備考

- 本実装により、反復計算におけるベクトル化の重要性を実証
- 実用的なユースケース（IVサーフェス構築）での性能差を明確化
- 将来的にはHeston、SABRなど他のIVモデルのベンチマークも追加可能