# [Rust] PyO3型スタブ自動生成システム 実装計画

## メタデータ
- **作成日**: 2025-01-28
- **言語**: Rust
- **ステータス**: DRAFT
- **推定規模**: 大
- **推定コード行数**: 800-1000行
- **対象モジュール**: src/lib.rs, src/python_modules.rs, 全PyO3バインディング

## タスク規模判定

### 判定基準
- [x] 推定コード行数: 800-1000 行
- [x] 新規ファイル数: 5-8 個（build.rs, スタブ生成モジュール、.pyi ファイル）
- [x] 影響範囲: 全体（全てのPyO3バインディングに影響）
- [x] PyO3バインディング: 必要（型スタブ生成が主目的）
- [ ] SIMD最適化: 不要
- [ ] 並列化: 不要

### 規模判定結果
**大規模タスク** - 全PyO3バインディングへのマクロ適用と新規ビルドシステム構築

## 品質管理ツール（Rust）

### 適用ツール（規模に応じて自動選択）
| ツール | 小規模 | 中規模 | 大規模 | 実行コマンド |
|--------|--------|--------|--------|-------------|
| cargo test | ✅ | ✅ | ✅ | `cargo test --all` |
| cargo clippy | ✅ | ✅ | ✅ | `cargo clippy -- -D warnings` |
| cargo fmt | ✅ | ✅ | ✅ | `cargo fmt --check` |
| similarity-rs | - | 条件付き | ✅ | `similarity-rs --threshold 0.80 src/` |
| rust-refactor.md | - | 条件付き | ✅ | `.claude/commands/rust-refactor.md` 適用 |
| cargo bench | - | 推奨 | ✅ | `cargo bench` |
| miri（安全性） | - | - | 推奨 | `cargo +nightly miri test` |

## 問題分析

### 現状の問題点
1. **型情報の不完全性**
   - Rust拡張モジュール（quantforge.abi3.so）に型情報なし
   - mypyエラー75個（83.6%削減後も残存）
   - IDE補完機能が効かない

2. **メンテナンスコスト**
   - 手動ラッパー（models.py）の保守負担
   - Rust実装変更時の型情報同期が手動
   - 新機能追加時の二重実装

3. **現在の回避策の限界**
   - Python側ラッパーでの型アノテーション追加
   - type: ignore コメントの多用
   - ベンチマーク用.pyiファイルの手動作成

## 解決策アーキテクチャ

### 採用技術: pyo3-stub-gen
- **理由**: 2024-2025年時点で最も成熟したソリューション
- **バージョン**: 0.12.2（2025年1月時点の最新）
- **特徴**: 
  - コンパイル時型スタブ生成
  - PyO3とのネイティブ統合
  - maturin自動認識

### システム構成
```
quantforge/
├── Cargo.toml            # pyo3-stub-gen依存追加
├── build.rs              # ビルド時スタブ生成スクリプト
├── src/
│   ├── lib.rs            # スタブ生成初期化
│   ├── python_modules.rs # マクロ適用
│   └── stub_gen/         # スタブ生成モジュール（新規）
│       └── mod.rs
├── quantforge.pyi        # 生成される型スタブ（自動）
└── py.typed              # 型情報提供マーカー（新規）
```

## フェーズ構成（大規模実装）

### Phase 1: 設計フェーズ（4時間）
- [x] アーキテクチャ設計（完了）
- [ ] pyo3-stub-genクレート調査詳細
- [ ] 既存PyO3バインディング構造分析
- [ ] エラーハンドリング設計

### Phase 2: 段階的実装（2日）

#### マイルストーン1: 基盤構築（8時間）
- [ ] Cargo.toml依存追加
  ```toml
  [dependencies]
  pyo3-stub-gen = "0.12.2"
  
  [build-dependencies]
  pyo3-stub-gen-derive = "0.12.2"
  ```
- [ ] build.rs作成
- [ ] スタブ生成モジュール基本実装
- [ ] **中間品質チェック**
  ```bash
  cargo test
  cargo clippy
  similarity-rs --threshold 0.80 src/
  ```

#### マイルストーン2: マクロ適用（12時間）
- [ ] #[gen_stub_pyfunction]マクロを全関数に適用
  - [ ] src/python_modules.rs（約30関数）
  - [ ] black_scholes関連（8関数）
  - [ ] black76関連（8関数）
  - [ ] merton関連（8関数）
  - [ ] american関連（8関数）
- [ ] #[gen_stub_pyclass]マクロをクラスに適用
  - [ ] PyGreeks
  - [ ] MertonGreeks
  - [ ] AmericanGreeks
- [ ] **similarity-rs実行**

#### マイルストーン3: 統合（4時間）
- [ ] quantforge.pyiファイル生成確認
- [ ] py.typedファイル追加
- [ ] maturinビルドプロセス統合

### Phase 3: 統合テスト（8時間）
- [ ] 型スタブ生成の自動化確認
- [ ] mypyでの型チェック検証
- [ ] IDE補完機能テスト
- [ ] Python側ラッパー（models.py）との比較

### Phase 4: リファクタリングフェーズ（必須: 8時間）
- [ ] **rust-refactor.md 完全適用**
- [ ] similarity-rs で最終確認
- [ ] 不要になったPython側ラッパーの段階的削除
- [ ] ドキュメント更新

## 命名定義セクション

### 4.1 使用する既存命名
```yaml
existing_names:
  - name: "s"
    meaning: "スポット価格"
    source: "naming_conventions.md#Black-Scholes系"
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
  - name: "call_price"
    meaning: "コール価格計算関数"
    source: "naming_conventions.md#価格計算関数"
  - name: "greeks"
    meaning: "グリークス計算"
    source: "naming_conventions.md#感度計算関数"
```

### 4.2 新規提案命名（必要な場合）
```yaml
proposed_names:
  # 型スタブ生成に特化した新規命名は不要
  # 既存のPyO3バインディング名をそのまま型スタブに反映
```

### 4.3 命名の一貫性チェックリスト
- [x] 既存モデルとの整合性確認
- [x] naming_conventions.mdとの一致確認
- [x] ドキュメントでの使用方法定義
- [x] APIパラメータは省略形を使用
- [x] エラーメッセージでもAPI名を使用

## 技術要件

### 必須要件
- [ ] 全PyO3関数の型スタブ生成
- [ ] 全PyO3クラスの型スタブ生成
- [ ] バッチ処理関数の配列型情報
- [ ] Optional/Union型の正確な表現

### パフォーマンス目標
- [ ] ビルド時間増加: < 30秒
- [ ] 型スタブファイルサイズ: < 100KB
- [ ] mypyエラー削減: 75個 → 0個

### PyO3連携
- [ ] #[pyfunction]との互換性維持
- [ ] #[pyclass]との互換性維持
- [ ] numpy配列型の正確な表現
- [ ] Dict[str, np.ndarray]型の正確な表現

## 実装詳細

### 1. マクロ適用例
```rust
// Before
#[pyfunction]
#[pyo3(name = "call_price")]
fn bs_call_price(s: f64, k: f64, t: f64, r: f64, sigma: f64) -> PyResult<f64> {
    // ...
}

// After
#[gen_stub_pyfunction]  // 追加
#[pyfunction]
#[pyo3(name = "call_price")]
fn bs_call_price(s: f64, k: f64, t: f64, r: f64, sigma: f64) -> PyResult<f64> {
    // ...
}
```

### 2. build.rs実装
```rust
use pyo3_stub_gen::{StubGenerator, StubInfo};

fn main() {
    // スタブ生成器初期化
    let mut generator = StubGenerator::new();
    
    // インベントリから収集された関数・クラス情報を処理
    generator.generate_stub_file("quantforge.pyi");
    
    println!("cargo:rerun-if-changed=src/");
}
```

### 3. 期待される型スタブ出力
```python
# quantforge.pyi (自動生成)
from typing import Optional, List, Dict
import numpy as np
from numpy.typing import NDArray

class models:
    @staticmethod
    def call_price(s: float, k: float, t: float, r: float, sigma: float) -> float: ...
    
    @staticmethod
    def call_price_batch(
        spots: NDArray[np.float64] | float,
        strikes: NDArray[np.float64] | float,
        times: NDArray[np.float64] | float,
        rates: NDArray[np.float64] | float,
        sigmas: NDArray[np.float64] | float
    ) -> NDArray[np.float64]: ...
    
    @staticmethod
    def greeks_batch(
        spots: NDArray[np.float64] | float,
        k: float,
        t: float,
        r: float,
        sigma: float,
        is_calls: NDArray[np.float64] | float
    ) -> Dict[str, NDArray[np.float64]]: ...

    class black76:
        @staticmethod
        def call_price(f: float, k: float, t: float, r: float, sigma: float) -> float: ...
```

## リスクと対策

| リスク | 影響度 | 対策 |
|--------|--------|------|
| pyo3-stub-genの制限 | 高 | 手動調整用フックを準備 |
| 複雑な型の表現困難 | 中 | カスタム型変換ロジック実装 |
| ビルド時間増加 | 低 | インクリメンタルビルド最適化 |
| 既存コードとの互換性 | 中 | 段階的移行計画 |

## チェックリスト

### 実装前
- [x] 既存PyO3バインディング構造確認
- [x] pyo3-stub-gen動作検証
- [ ] 依存関係の互換性確認

### 実装中
- [ ] 各マイルストーンでのテスト実行
- [ ] 型スタブの生成確認
- [ ] mypyでの検証

### 実装後
- [ ] 全品質ゲート通過
- [ ] mypyエラーゼロ達成
- [ ] IDE補完機能動作確認
- [ ] ドキュメント更新
- [ ] 計画のarchive移動

## 成果物

- [ ] build.rsスクリプト
- [ ] スタブ生成モジュール（src/stub_gen/）
- [ ] quantforge.pyi（自動生成）
- [ ] py.typedファイル
- [ ] 更新されたPyO3バインディング（マクロ適用済み）
- [ ] CI/CD統合スクリプト

## 移行計画

### Phase 1: 並行運用（1週間）
- 型スタブ生成システム構築
- 既存models.pyラッパーは維持
- 両方での型チェック確認

### Phase 2: 段階的移行（1週間）
- 型スタブを主とした型チェック
- models.pyの段階的削除
- テストコードの更新

### Phase 3: 完全移行（最終）
- models.py完全削除
- 型スタブのみでの運用
- ドキュメント最終更新

## 期待される効果

### 定量的効果
- mypyエラー: 75個 → 0個（100%削減）
- 手動メンテナンスコード: 約600行削除
- ビルド時自動生成: 100%自動化

### 定性的効果
- IDE補完機能の完全サポート
- 型安全性の保証
- Rust実装変更時の自動同期
- 開発効率の向上

## 備考

- pyo3-stub-genは2024年に活発に開発されており、今後も機能拡張が期待される
- 将来的にはPyO3本体への統合も検討されている
- 本実装はQuantForgeプロジェクトの技術的負債ゼロ方針に完全準拠

## 参考資料

- [pyo3-stub-gen公式ドキュメント](https://crates.io/crates/pyo3-stub-gen)
- [PyO3 Issue #2454: Python Interface generation](https://github.com/PyO3/pyo3/issues/2454)
- [Maturin Issue #1942: Automatic .pyi generation](https://github.com/PyO3/maturin/issues/1942)