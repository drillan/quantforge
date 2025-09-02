# [Both] ベンチマーク記録システム実装計画

## メタデータ
- **作成日**: 2025-09-02
- **言語**: Both (Python/Rust統合)
- **ステータス**: DRAFT
- **推定規模**: 中
- **推定コード行数**: 新規150行、修正50行
- **対象モジュール**: bindings/python/src/lib.rs, tests/performance/

## タスク規模判定

### 判定基準
- [x] 推定コード行数: 200行（中規模）
- [x] 新規ファイル数: 0個
- [x] 影響範囲: 複数モジュール（lib.rs、conftest.py、test_all_benchmarks.py）
- [ ] PyO3バインディング: 修正のみ
- [ ] SIMD最適化: 不要
- [ ] 並列化: 不要

### 規模判定結果
**中規模タスク**（既存システムの修正・拡張）

## 品質管理ツール（Both）

### 適用ツール
| ツール | 適用 | 実行コマンド |
|--------|------|-------------|
| cargo test | ✅ | `cargo test --all --release` |
| cargo clippy | ✅ | `cargo clippy --all-targets --all-features -- -D warnings` |
| cargo fmt | ✅ | `cargo fmt --all --check` |
| pytest | ✅ | `pytest tests/performance/ -m benchmark` |
| ruff | ✅ | `uv run ruff check tests/performance/` |
| mypy | ✅ | `uv run mypy tests/performance/` |

## 命名定義セクション

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

## 現状の問題点

### 1. バージョン不整合 🔴
- **現状**: 
  - `bindings/python/src/lib.rs`: ハードコード `"0.2.0"`
  - `Cargo.toml`: `version = "0.0.6"`
- **影響**: ベンチマーク記録が誤ったバージョンで記録される
- **原因**: lib.rsでのバージョンハードコード

### 2. Arrow Native未測定 🟡
- **現状**: `test_all_benchmarks.py`にArrow Nativeベンチマークなし
- **影響**: 最新のパフォーマンス改善（ゼロコピー実装）が測定されていない
- **要求**: pyo3-arrow/arro3-coreによる性能向上を定量化

### 3. パス設定の脆弱性 🟡
- **現状**: `conftest.py`で相対パス`Path("benchmark_results")`使用
- **影響**: 実行ディレクトリによって記録場所が変わる可能性
- **要求**: プロジェクトルートからの絶対パス保証

## 実装フェーズ

### Phase 1: バージョン管理の修正（即座実施）
- [ ] lib.rsのバージョン自動化
  ```rust
  // bindings/python/src/lib.rs
  m.add("__version__", env!("CARGO_PKG_VERSION"))?;
  ```
- [ ] maturin developでビルド
  ```bash
  uv run maturin develop --release
  ```
- [ ] バージョン確認
  ```bash
  python -c "import quantforge; print(quantforge.__version__)"
  # Expected: "0.0.6"
  ```

### Phase 2: パス設定の堅牢化（即座実施）
- [ ] conftest.pyの修正
  ```python
  # tests/performance/conftest.py
  def __init__(self):
      # プロジェクトルートからの絶対パス
      self.results_dir = Path(__file__).parent.parent.parent / "benchmark_results"
      self.results_dir.mkdir(parents=True, exist_ok=True)
  ```
- [ ] エラーハンドリング追加
  - ディレクトリ作成失敗時の警告
  - JSON書き込み失敗時の例外処理

### Phase 3: Arrow Nativeベンチマーク追加（優先実施）
- [ ] test_all_benchmarks.pyに新規テストクラス追加
  ```python
  @pytest.mark.benchmark
  class TestArrowNative:
      """Benchmark tests for Arrow Native implementation."""
      
      def setup_method(self):
          """Setup Arrow arrays for testing."""
          import pyarrow as pa
          # PyArrow配列の準備
          
      @pytest.mark.parametrize("size", [100, 1000, 10000])
      def test_arrow_native_batch(self, benchmark, size):
          """Benchmark Arrow Native batch calculation."""
          # arro3-coreを使用したゼロコピー処理
  ```
- [ ] インポート確認
  ```python
  try:
      import quantforge.arrow_native as arrow_native
      HAS_ARROW_NATIVE = True
  except ImportError:
      HAS_ARROW_NATIVE = False
  ```

### Phase 4: ベンチマーク実行と検証
- [ ] 全ベンチマーク実行
  ```bash
  pytest tests/performance/ -m benchmark -v
  ```
- [ ] Arrow Nativeのみ実行
  ```bash
  pytest tests/performance/test_all_benchmarks.py::TestArrowNative -m benchmark
  ```
- [ ] 結果確認
  ```bash
  # バージョン確認
  cat benchmark_results/latest.json | jq .version
  # Expected: "0.0.6"
  
  # Arrow Nativeベンチマーク確認
  cat benchmark_results/latest.json | jq '.benchmarks[] | select(.name | contains("arrow"))'
  ```

### Phase 5: パフォーマンス比較レポート生成
- [ ] generate_benchmark_report.py実行
  ```bash
  python tests/performance/generate_benchmark_report.py
  ```
- [ ] 比較分析
  - QuantForge (Rust) vs Arrow Native
  - メモリ使用量の差（ゼロコピー効果）
  - 処理速度の改善率

## 技術要件

### 必須要件
- [x] **pytest -m benchmark**での自動記録
- [x] **バージョン整合性**（Cargo.toml = Python = JSON記録）
- [x] **Arrow Native測定**（pyo3-arrow/arro3-core性能）
- [x] **プロジェクトルートからの絶対パス**

### パフォーマンス目標
- [ ] Arrow Native: 10,000要素で100-150μs（従来245μs）
- [ ] メモリ使用量: 1.0倍（ゼロコピー確認）
- [ ] 記録オーバーヘッド: < 10ms

## リスクと対策

| リスク | 影響度 | 対策 |
|--------|--------|------|
| Arrow Nativeインポート失敗 | 中 | skipif装飾子で条件付き実行 |
| 既存ベンチマーク互換性 | 低 | 既存テストは変更なし、追加のみ |
| パフォーマンス測定ばらつき | 中 | warmup追加、実行回数増加 |

## チェックリスト

### 実装前
- [x] 現状のベンチマークシステム分析完了
- [x] 問題点の特定完了
- [x] pytest-benchmark動作確認

### 実装中
- [ ] lib.rsのバージョン修正
- [ ] conftest.pyのパス修正
- [ ] Arrow Nativeテスト追加
- [ ] pytest -m benchmarkで実行確認

### 実装後
- [ ] バージョン0.0.6で記録確認
- [ ] Arrow Nativeベンチマーク結果確認
- [ ] history.jsonlへの追記確認
- [ ] パフォーマンスレポート生成

## 成果物

- [ ] 修正済みlib.rs（バージョン自動化）
- [ ] 修正済みconftest.py（絶対パス使用）
- [ ] 拡張済みtest_all_benchmarks.py（Arrow Native追加）
- [ ] benchmark_results/latest.json（正しいバージョン記録）
- [ ] benchmark_results/history.jsonl（履歴追記）
- [ ] パフォーマンス比較レポート

## 実装の具体的内容

### lib.rsの修正（最小限の変更）
```rust
// bindings/python/src/lib.rs
#[pymodule]
fn quantforge(m: &Bound<'_, PyModule>) -> PyResult<()> {
    // バージョンをCargo.tomlから自動取得
    m.add("__version__", env!("CARGO_PKG_VERSION"))?;
    // 以下既存のコード...
}
```

### test_all_benchmarks.pyへの追加
```python
# Arrow Native実装のベンチマーク（既存テストに追加）
@pytest.mark.benchmark
@pytest.mark.skipif(not HAS_ARROW_NATIVE, reason="Arrow Native not available")
class TestArrowNative:
    """Benchmark tests for Arrow Native zero-copy implementation."""
    
    def setup_method(self):
        """Setup Arrow arrays for testing."""
        import pyarrow as pa
        np.random.seed(42)
        
    @pytest.mark.parametrize("size", [100, 1000, 10000])
    def test_arrow_native_batch(self, benchmark, size):
        """Benchmark Arrow Native batch calculation with zero-copy."""
        import pyarrow as pa
        
        # PyArrow配列生成
        spots = pa.array(np.random.uniform(80, 120, size))
        strikes = pa.array(np.full(size, 100.0))
        times = pa.array(np.full(size, 1.0))
        rates = pa.array(np.full(size, 0.05))
        sigmas = pa.array(np.random.uniform(0.15, 0.35, size))
        
        # ゼロコピーでのベンチマーク
        result = benchmark(
            qf.arrow_native.arrow_call_price,
            spots, strikes, times, rates, sigmas
        )
        
        # 結果検証
        assert len(result) == size
        assert all(p > 0 for p in result.to_pylist())
```

## 備考

- **破壊的変更なし**: 既存のベンチマークはそのまま維持
- **追加のみ**: Arrow Nativeテストを追加するだけ
- **CI/CD対応**: `pytest -m benchmark`でGitHub Actions統合可能
- **パフォーマンス劣化検出**: 将来的に閾値ベースの自動検出追加可能