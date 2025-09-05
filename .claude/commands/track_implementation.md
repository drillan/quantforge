# 実装進捗追跡プロンプト

## タスク: QuantForge実装進捗の確認と更新

このプロジェクトのドキュメント構造に対して、実装状況を確認し、進捗を記録してください。
現在のCore + Bindingsアーキテクチャ構造に基づいて確認します。

## 出力先ファイル
- **詳細データ**: `.internal/tracker/data.yaml`
- **進捗レポート**: `.internal/tracker/report.md`

### 確認手順

1. **ドキュメントの見出し抽出**
   - 対象ファイル: `docs/ja/models/*.md`, `docs/ja/api/**/*.md`, `docs/en/models/*.md`, `docs/en/api/**/*.md`
   - 各Markdownファイルから見出し（#, ##, ###）を階層的に抽出

2. **実装状況の検索と判定**（Core + Bindings構造）
   各見出し項目について、以下の場所で対応する実装を検索：
   - Rustコア: `core/src/models/`, `core/src/math/`, `core/src/`
   - Pythonバインディング: `bindings/python/src/`, `bindings/python/python/quantforge/`
   - テスト: `tests/`, `core/tests/`, `bindings/python/tests/`

3. **ステータス判定基準**
   - `not_started`: 実装なし、TODOコメントのみ
   - `partial`: 一部実装済み、基本機能のみ
   - `implemented`: 完全実装済み、テスト待ち
   - `tested`: テスト済み、本番準備完了
   - `documented_only`: ドキュメントのみ（理論説明等、実装不要）

### 検索パターン例

```yaml
# 見出しから実装を探すパターン
"Black-Scholesモデル" → 
  - black_scholes.rs
  - bs_*, black_scholes_*
  
"ヨーロピアンコール" →
  - bs_call_price, european_call
  - calculate_call_price
  
"Delta (Δ)" →
  - delta, calculate_delta
  - greeks::delta
  
"SIMD最適化" →
  - simd, avx2, avx512
  - #[cfg(target_feature = "avx2")]
```

### 出力形式（data.yaml）

```yaml
# ドキュメントファイルごとに階層的に管理
docs/ja/models/black_scholes.md:
  - title: "Black-Scholesモデル"
    level: 1
    status: partial
    items:
      - title: "理論的背景"
        level: 2
        status: documented_only  # 理論説明のため実装不要
      - title: "解析解"
        level: 2
        status: partial
        items:
          - title: "ヨーロピアンコール"
            level: 3
            status: tested
            location: "core/src/models/black_scholes.rs:11-27"
            tests: "tests/unit/test_black_scholes.py"
          - title: "ヨーロピアンプット"
            level: 3
            status: tested
            location: "core/src/models/black_scholes.rs:28-37"
            tests: "tests/unit/test_black_scholes.py"
      - title: "グリークス"
        level: 2
        status: tested
        items:
          - title: "Delta (Δ)"
            level: 3
            status: tested
            location: "core/src/models/greeks.rs:60-85"
```

### 進捗レポート生成（report.md）

確認結果を以下の形式でレポート：

```markdown
# QuantForge 実装進捗レポート

**最終更新**: 2025-09-03

## 📊 全体統計

| 指標 | 値 |
|------|-----|
| **総項目数** | X |
| **テスト済み** | Y ✅ |
| **実装済み** | Z 🟢 |
| **部分実装** | A 🟡 |
| **未着手** | B ⭕ |
| **ドキュメントのみ** | C 📝 |
| **完了率** | XX.X% |

## 📦 モデル別進捗

### Black-Scholes (90% 完了)
- ✅ ヨーロピアンコール (`core/src/models/black_scholes.rs:11-27`)
- ✅ ヨーロピアンプット (`core/src/models/black_scholes.rs:28-37`)
- ✅ 全Greeks (`core/src/models/greeks.rs`)
- 📝 理論的背景（ドキュメントのみ）

### Black76 (100% 完了)
- ✅ 先物オプション価格計算
- ✅ Greeks計算
- ✅ インプライドボラティリティ

## ✨ 主要な実装済み機能

### コアモデル
- ✅ Black-Scholes（コール/プット価格、Greeks）
- ✅ Black76（先物オプション）
- ✅ Merton（配当付きモデル）
- ✅ American（アメリカンオプション、Bjerksund-Stensland 2002）

### アーキテクチャ
- ✅ Core + Bindings 構造（言語非依存コア）
- ✅ Arrow Native実装（ゼロコピー）
- ✅ 完全配列サポート（Broadcasting対応）
- ✅ 並列処理最適化（Rayon統合）
```

### ステータス記号

- ⭕ : not_started (未着手)
- 🟡 : partial (部分実装)
- 🟢 : implemented (実装完了)
- ✅ : tested (テスト済み)
- 📝 : documented_only (ドキュメントのみ)

### 実行方法

このコマンドをAIアシスタント（Claude）で実行すると、自動的に：
1. ドキュメント構造を解析
2. 実装ファイルを検索
3. `.internal/tracker/data.yaml` を更新
4. `.internal/tracker/report.md` を生成

```bash
# コマンド実行例
echo "QuantForgeの実装進捗を確認し、.internal/tracker/配下のファイルを更新してください" | claude
```

### 検証スクリプトとの連携

1. **先に検証スクリプトを実行**
   ```bash
   python .internal/tracker/verify_documentation_code.py
   ```
   
2. **検証結果を含めてレポート生成**
   - `doc_verification_results.json` の内容も参照
   - コード例の検証結果を統合

### 注意事項

1. **False Positive回避**
   - 同名の異なる関数を区別
   - コメント内の記述と実装を区別
   - テストコードと本番コードを区別

2. **バージョン管理**
   - 進捗状況はtracker.yamlに保存
   - 変更履歴を記録

3. **優先度判定**
   - Phase 1-7の実装計画と照合
   - 依存関係を考慮

このプロンプトを使用して、定期的に実装進捗を確認し、ドキュメントと実装の乖離を防いでください。