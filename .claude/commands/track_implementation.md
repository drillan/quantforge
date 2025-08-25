# 実装進捗追跡プロンプト

## タスク: QuantForge実装進捗の確認と更新

このプロジェクトのドキュメント構造に対して、実装状況を確認し、進捗を記録してください。

### 確認手順

1. **ドキュメントの見出し抽出**
   - 対象ファイル: `docs/models/*.md`, `docs/api/**/*.md`, `docs/performance/*.md`
   - 各Markdownファイルから見出し（#, ##, ###）を階層的に抽出

2. **実装状況の検索と判定**
   各見出し項目について、以下の場所で対応する実装を検索：
   - Rustコード: `src/models/`, `src/math/`, `src/`
   - Pythonバインディング: `python/quantforge/`
   - テスト: `tests/`, `src/**/*.rs` の `#[test]`

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

### 出力形式

```yaml
# ファイル: docs/models/black_scholes.md
black_scholes:
  - title: "Black-Scholesモデル"
    level: 1
    status: partial
    items:
      - title: "理論的背景"
        level: 2
        status: documented_only
        notes: "理論説明のみ"
      
      - title: "解析解"
        level: 2
        status: partial
        items:
          - title: "ヨーロピアンコール"
            level: 3
            status: implemented
            location: "src/models/black_scholes.rs:11-17"
            tests: "src/models/black_scholes.rs:44-55"
          
          - title: "ヨーロピアンプット"
            level: 3
            status: not_started
            notes: "TODO: プット実装"
      
      - title: "グリークス"
        level: 2
        status: not_started
        items:
          - title: "Delta (Δ)"
            level: 3
            status: not_started
          - title: "Gamma (Γ)"
            level: 3
            status: not_started
```

### 進捗レポート生成

確認結果を以下の形式でレポート：

```markdown
# QuantForge 実装進捗状況

最終更新: [日付]

## 📊 全体進捗
- 完了: X項目 (XX%)
- 実装中: Y項目 (YY%)
- 未着手: Z項目 (ZZ%)

## 📁 docs/models/black_scholes.md
- Black-Scholesモデル: 🟡 (40%)
  - 理論的背景: 📝
  - 解析解: 🟡 (50%)
    - ヨーロピアンコール: ✅ [src/models/black_scholes.rs:11]
    - ヨーロピアンプット: ⭕
  - グリークス: ⭕ (0%)
    - Delta (Δ): ⭕
    - Gamma (Γ): ⭕
    - Vega (ν): ⭕
    - Theta (Θ): ⭕
    - Rho (ρ): ⭕
```

### ステータス記号

- ⭕ : not_started (未着手)
- 🟡 : partial (部分実装)
- 🟢 : implemented (実装完了)
- ✅ : tested (テスト済み)
- 📝 : documented_only (ドキュメントのみ)

### 実行コマンド例

```bash
# 1. 特定ドキュメントの進捗確認
echo "docs/models/black_scholes.mdの実装進捗を確認してください" | claude

# 2. 全体進捗の確認
echo "docs/配下の全ドキュメントの実装進捗を確認してください" | claude

# 3. 未実装項目のリストアップ
echo "status: not_startedの項目をリストアップしてください" | claude
```

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