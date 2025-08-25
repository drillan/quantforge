# QuantForge テスト戦略

## 📊 実装状況とテスト対応

### 実装済み機能とテスト

| 機能 | 実装状況 | テストファイル | カバレッジ | 備考 |
|------|---------|---------------|-----------|------|
| **Black-Scholes** |||||
| コール価格計算 | ✅ 完了 | `test_integration.py` | 基本テストのみ | norm_cdf精度による誤差あり |
| バッチ処理 | ✅ 完了 | `test_integration.py` | 基本テストのみ | SIMD最適化は未実装 |
| プット価格計算 | ❌ 未実装 | - | - | 次期実装予定 |
| **Greeks** |||||
| デルタ | ❌ 未実装 | - | - | |
| ガンマ | ❌ 未実装 | - | - | |
| シータ | ❌ 未実装 | - | - | |
| ベガ | ❌ 未実装 | - | - | |
| ロー | ❌ 未実装 | - | - | |
| **拡張モデル** |||||
| Merton（配当付き） | ❌ 未実装 | - | - | |
| Black76（先物） | ❌ 未実装 | - | - | |
| American | ❌ 未実装 | - | - | |
| Asian | ❌ 未実装 | - | - | |

### ゴールデンマスター対応状況

- **参照値生成**: ✅ 158テストケース生成済み（`golden/golden_values.json`）
- **現在の精度**: ~1e-5（norm_cdf実装の違いによる）
- **目標精度**: 1e-10（高精度数学関数実装後）

## 🧪 段階的テスト実施計画

### Phase 1: 現在実装済み機能のテスト（即実行可能）

```bash
# 統合テスト実行
uv run pytest tests/test_integration.py -v

# ゴールデンマスターテスト（許容誤差調整版）
uv run pytest tests/test_golden_master.py::TestGoldenMaster::test_black_scholes_call_prices -v
```

**注意**: 現在の許容誤差は`1e-5`に設定する必要があります（norm_cdf精度の制約）

### Phase 2: プットオプション実装時のテスト

実装後に追加すべきテスト：

```python
# tests/test_put_options.py
def test_put_price_calculation():
    """プット価格の基本計算"""
    pass

def test_put_call_parity():
    """Put-Callパリティの検証"""
    # C - P = S - K*e^(-rT)
    pass
```

### Phase 3: Greeks実装時のテスト

```python
# tests/test_greeks.py
def test_delta_calculation():
    """デルタの計算と数値微分での検証"""
    pass

def test_gamma_calculation():
    """ガンマの計算検証"""
    pass
```

### Phase 4: 拡張モデル実装時

各モデル実装時に以下を実施：

1. **ゴールデンマスター更新**
   ```bash
   # 新しいモデルの参照値を追加生成
   cd tests/golden
   # gbs_reference/models.pyに新モデル追加後
   uv run python generate_golden_master.py --regenerate-golden
   ```

2. **専用テストファイル作成**
   - `test_merton_model.py`
   - `test_black76_model.py`
   - `test_american_options.py`

## 📁 テストディレクトリ構成

```
tests/
├── README.md                    # このファイル（テスト戦略全体）
├── golden/                      # ゴールデンマスター参照値生成ツール
│   ├── README.md               # ツールの使用方法
│   ├── generate_golden_master.py
│   ├── gbs_reference/          # 参照実装（生成専用）
│   └── golden_values.json      # 生成済み参照値
├── test_integration.py          # 統合テスト（現在のメイン）
├── test_golden_master.py        # ゴールデンマスター検証
└── （将来追加予定）
    ├── unit/                    # 単体テスト
    ├── property/                # プロパティベーステスト
    └── performance/             # パフォーマンステスト
```

## 🎯 テスト実行ガイド

### 通常のテスト実行

```bash
# 全テスト実行
uv run pytest tests/

# 特定のテストのみ
uv run pytest tests/test_integration.py -v

# ゴールデンマスターテスト
uv run pytest tests/test_golden_master.py -v
```

### ゴールデンマスター関連

```bash
# 参照値の再生成（通常は不要）
uv run pytest tests/golden/generate_golden_master.py --regenerate-golden

# 生成スクリプトは通常自動スキップされる
uv run pytest tests/  # generate_golden_master.pyは実行されない
```

## ⚠️ 重要な注意事項

### 1. 技術的負債ゼロの原則

- **段階的実装は避ける**: 「とりあえず動く」テストは作らない
- **完全性を重視**: 機能を実装したら、そのテストも完全に実装
- **参照実装の隔離**: `gbs_reference/`は生成専用、本番コードから参照禁止

### 2. 精度に関する現状

現在のRust実装では`norm_cdf`の精度制限により、GBS_2025.pyとの誤差が約`1e-5`レベルです。
これは金融計算として実用上問題ありませんが、将来的に高精度実装を行う予定です。

### 3. CI/CD統合

現在はworkflow_dispatchで手動実行としています。テスト基盤が確立した後に自動化予定。

## 📈 カバレッジ目標

| フェーズ | 目標カバレッジ | 期限 | 状況 |
|---------|---------------|------|------|
| Phase 1 | コア機能 100% | 2025-01-31 | 進行中 |
| Phase 2 | Greeks 100% | 2025-02-15 | 未着手 |
| Phase 3 | 全モデル 95% | 2025-03-31 | 未着手 |

## 🔗 関連ドキュメント

- [Pytestカバレッジ戦略](../plans/2025-01-24-pytest-coverage-strategy.md)
- [ゴールデンマスターテスト実装計画](../plans/2025-01-25-golden-master-testing.md)
- [技術的負債ゼロの原則](../CLAUDE.md#技術的負債ゼロの原則)

---

**最終更新**: 2025-01-25