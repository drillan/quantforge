# ゴールデンマスターテスト

## 概要

このディレクトリには、QuantForgeのテストで使用する参照値（ゴールデンマスター）を生成・管理するツールが含まれています。

## ディレクトリ構造

```
golden/
├── __init__.py                 # モジュール初期化
├── generate_golden_master.py   # 参照値生成スクリプト
├── gbs_reference/              # リファクタリング版GBS実装
│   ├── __init__.py
│   ├── models.py              # Black-Scholesモデル
│   └── utils.py               # 数学関数ユーティリティ
├── golden_values.json         # 生成された参照値
├── .golden_generated          # 生成済みフラグファイル
└── README.md                  # このファイル
```

## 使用方法

### 初回の参照値生成

```bash
# 参照値を生成（初回のみ必要）
uv run pytest tests/golden/generate_golden_master.py --generate-golden
```

### 参照値の再生成

```bash
# 何らかの理由で再生成が必要な場合
uv run pytest tests/golden/generate_golden_master.py --regenerate-golden
```

### 通常のテスト実行

```bash
# ゴールデンマスターテストの実行
uv run pytest tests/test_golden_master.py

# 全テストの実行（generate_golden_master.pyは自動スキップ）
uv run pytest tests/
```

## 重要な注意事項

1. **技術的負債ゼロの原則**
   - `gbs_reference/`内のコードは参照値生成専用
   - 本番コードからは一切参照しない
   - 生成後は`.golden_generated`フラグにより自動スキップ

2. **参照値の妥当性**
   - GBS_2025.py（MIT License）から抽出
   - 業界標準の計算式を実装
   - 生成された値は`golden_values.json`に永続化

3. **再生成のタイミング**
   - 新しいモデルを追加した場合
   - 計算精度要件が変更された場合
   - 参照実装のバグが発見された場合

## 参照値フォーマット

```json
{
  "version": "1.0.0",
  "generated_at": "2025-01-25T00:00:00Z",
  "source": "GBS_2025.py (MIT License)",
  "test_cases": [
    {
      "id": "BS_ATM_001",
      "category": "black_scholes",
      "inputs": {
        "s": 100.0,
        "k": 100.0,
        "t": 1.0,
        "r": 0.05,
        "v": 0.2
      },
      "outputs": {
        "call_price": 10.450583572185565
      }
    }
  ],
  "tolerance": 1e-10
}
```

## トラブルシューティング

### 生成スクリプトが実行されない
- `--generate-golden`または`--regenerate-golden`フラグを確認

### 参照値が見つからない
- `golden_values.json`が存在することを確認
- 初回生成コマンドを実行

### テスト精度エラー
- `tolerance`設定を確認（デフォルト: 1e-10）
- Rust実装の数値精度を検証