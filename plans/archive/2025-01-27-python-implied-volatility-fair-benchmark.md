# [Python] インプライドボラティリティ公正ベンチマーク実装計画

## メタデータ
- **作成日**: 2025-01-27
- **言語**: Python
- **ステータス**: COMPLETED
- **推定規模**: 中規模
- **推定コード行数**: 400-500行
- **対象モジュール**: tests/performance/, .internal/benchmark_automation/

## ⚠️ 技術的負債ゼロの原則

**重要**: 公正なベンチマークのため、すべての実装で同一アルゴリズム（Newton-Raphson法）を使用

### 現状の問題点と解決方針

#### 問題点
1. **アルゴリズムの混在**
   - QuantForge, Pure Python, NumPy Newton: Newton-Raphson法
   - NumPy SciPy: Brent法（10-15倍遅い別アルゴリズム）
   
2. **不公正な比較**
   - NumPy SciPyが316倍遅く見える（実際はアルゴリズム差）
   - 実装技術の差が正確に測定できない

#### 解決方針
- **Newton-Raphson法で完全統一**
- **同一パラメータ使用**（tolerance: 1e-6, max_iterations: 100）
- **Brent法は参考値として別枠で提示**

## タスク規模判定

### 判定基準
- [x] 推定コード行数: 400-500行
- [x] 新規ファイル数: 0個（既存ファイルの修正・拡張）
- [x] 影響範囲: 複数モジュール（tests/, .internal/）
- [ ] Rust連携: 不要（既存APIを使用）
- [x] NumPy/Pandas使用: あり（NumPy）
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
  # すべて既存の命名を使用、新規なし
```

### 4.3 命名の一貫性チェックリスト
- [x] 既存モデルとの整合性確認
- [x] naming_conventions.mdとの一致確認
- [x] ドキュメントでの使用方法定義
- [x] APIパラメータは省略形を使用
- [x] エラーメッセージでもAPI名を使用

## 実装詳細

### 1. ベンチマーククラスの再編成

#### TestImpliedVolatilityNewtonRaphson（新規）
```python
@pytest.mark.benchmark
class TestImpliedVolatilityNewtonRaphson:
    """Newton-Raphson法のみの公正な比較"""
    
    # 統一パラメータ
    NEWTON_PARAMS = {
        "initial_guess": 0.2,
        "tolerance": 1e-6,
        "max_iterations": 100,
        "min_vega": 1e-10
    }
    
    def test_quantforge_newton_single(self, benchmark):
        """QuantForge Newton-Raphson（既存）"""
        
    def test_pure_python_newton_single(self, benchmark):
        """Pure Python Newton-Raphson（パラメータ統一）"""
        
    def test_numpy_newton_single(self, benchmark):
        """NumPy vectorized Newton-Raphson（既存）"""
    
    @pytest.mark.parametrize("size", [100, 1000, 10000])
    def test_quantforge_newton_batch(self, benchmark, size):
        """QuantForge Newton-Raphson batch"""
    
    # 以下同様のバッチテスト
```

#### TestImpliedVolatilityBrentMethod（参考）
```python
@pytest.mark.benchmark
class TestImpliedVolatilityBrentMethod:
    """Brent法の参考ベンチマーク（堅牢性重視）"""
    
    def test_numpy_scipy_brent_single(self, benchmark):
        """NumPy SciPy Brent法（既存）"""
        # 明確に「異なるアルゴリズム」と記載
```

### 2. ベンチマークレポート生成の拡張

#### generate_benchmark_report.pyの修正
```python
def extract_iv_benchmark_times(self, benchmarks):
    """IVベンチマーク結果を抽出（Newton法のみ）"""
    iv_times = {
        "newton_single": {},
        "newton_batch_100": {},
        "newton_batch_1000": {},
        "newton_batch_10000": {},
        "brent_reference": {}  # 参考値
    }
    # Newton-Raphson法の結果のみを主要結果として扱う
    
def generate_iv_comparison_table(self, times):
    """公正なIV比較表を生成"""
    lines = []
    lines.append("## インプライドボラティリティ計算性能（Newton-Raphson法で統一）")
    lines.append("")
    lines.append("※ すべて同一アルゴリズム・同一パラメータで実装")
    lines.append("")
    # 表生成...
```

### 3. CSVファイル生成

新規CSVファイル：
- `implied_volatility_newton.csv` - Newton法のみの公正な比較
- `implied_volatility_algorithm_comparison.csv` - アルゴリズム間の特性比較

### 4. README更新用マーカー

新規マーカー追加：
```html
<!-- BENCHMARK:IV:START -->
[IVベンチマーク結果]
<!-- BENCHMARK:IV:END -->

<!-- BENCHMARK:IV:NEWTON_SPEEDUP -->293<!-- /BENCHMARK:IV:NEWTON_SPEEDUP -->
```

## フェーズ構成

### Phase 1: 既存コードのリファクタリング（2時間）
- [x] 計画書作成
- [x] TestImpliedVolatilityCalculationクラスを分割
- [x] Newton-Raphson法テストを新クラスに移動
- [x] パラメータを統一（NEWTON_PARAMS定数）
- [x] Brent法を別クラスに分離

### Phase 2: ベンチマーク実装の改善（2時間）
- [x] Pure Python Newton-Raphsonのパラメータ統一
- [x] NumPy Newton実装のパラメータ確認
- [x] 各実装で同一の初期値・収束判定を使用
- [x] docstringでアルゴリズムを明記

### Phase 3: レポート生成の拡張（3時間）
- [x] generate_benchmark_report.pyにIV処理追加
- [x] Newton法のみの結果抽出ロジック
- [x] 公正な比較表の生成
- [x] Brent法を参考値として別枠表示

### Phase 4: 自動化統合（2時間）
- [x] update_readme.pyにIVマーカー処理追加（既存機能で対応）
- [x] CSVファイル生成ロジック
- [x] update_all.shスクリプトの更新（既存で対応）
- [x] ドキュメントへの自動反映確認

### Phase 5: テストと検証（1時間）
- [x] 全ベンチマークの実行
- [x] 結果の公正性確認
- [x] レポート生成の動作確認
- [x] README自動更新の確認（CSVエクスポート確認）

## 品質管理

### 品質ゲート（必達基準）
| 項目 | 基準 |
|------|------|
| テストカバレッジ | 90%以上 |
| 型カバレッジ | 100% |
| ruffエラー | 0件 |
| mypyエラー（strict） | 0件 |
| ベンチマーク実行成功率 | 100% |
| アルゴリズム統一性 | Newton-Raphson法のみ |

### 品質チェックコマンド
```bash
# フォーマットとリント
uv run ruff format tests/performance/
uv run ruff check tests/performance/ --fix

# 型チェック
uv run mypy --strict tests/performance/test_all_benchmarks.py

# ベンチマーク実行
uv run pytest tests/performance/ -m benchmark -v

# レポート生成テスト
python .internal/benchmark_automation/generate_benchmark_report.py
```

## 期待される成果

### 1. 公正なベンチマーク結果

```markdown
## インプライドボラティリティ計算性能（Newton-Raphson法で統一）

※ すべて同一アルゴリズム（Newton-Raphson）、同一パラメータで実装

### バッチ処理（10,000件）
| 実装技術 | 実行時間 | vs QuantForge |
|----------|----------|---------------|
| QuantForge (Rust + Rayon) | 333μs | 1.0x |
| NumPy Newton (vectorized) | 4,153μs | 12.5x遅い |
| Pure Python (loop) | 97,722μs | 293x遅い |

純粋に実装技術（Rust vs Python vs NumPy）の差を反映
```

### 2. 透明性の向上
- アルゴリズムの明記
- パラメータの開示
- 測定条件の統一

### 3. 自動化の実現
- ベンチマーク結果の自動収集
- READMEへの自動反映
- 継続的な性能監視

## リスクと対策

| リスク | 影響度 | 対策 |
|--------|--------|------|
| パラメータ統一による精度差 | 低 | 各実装で同じ精度になることを確認 |
| 既存テストへの影響 | 中 | 既存テストは別クラスで保持 |
| レポート生成の複雑化 | 低 | 段階的にテスト・検証 |

## チェックリスト

### 実装前
- [x] 現在のアルゴリズムの確認（QuantForge, Python実装）
- [x] 不公正な比較の特定（Brent vs Newton）
- [x] 公正性確保の方針決定

### 実装中
- [x] Newton-Raphson法で統一
- [x] パラメータの完全一致
- [x] アルゴリズムの明記

### 実装後
- [x] 公正性の検証
- [x] 自動化の動作確認
- [x] ドキュメント更新
- [ ] 計画書のarchive移動

## 成果物

1. **リファクタリングされたテストコード**
   - TestImpliedVolatilityNewtonRaphson（公正な比較）
   - TestImpliedVolatilityBrentMethod（参考）

2. **拡張されたレポート生成**
   - generate_benchmark_report.py（IV対応）
   - 新規CSVファイル

3. **更新されたREADME**
   - 公正なIVベンチマーク結果
   - アルゴリズムの明記

## 備考

- このベンチマークの目的は、QuantForgeの性能優位性を**公正に**示すこと
- Newton-Raphson法での統一により、純粋な実装技術の差を測定
- Brent法は堅牢性重視の選択肢として別途説明