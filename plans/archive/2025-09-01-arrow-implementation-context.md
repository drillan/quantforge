# QuantForge Arrow-Native実装 コンテキスト引き継ぎ書

## 📌 実装指示
このドキュメントに基づいてArrow-Native実装を進めてください。
不明瞭な点があれば、実装前に要件定義を行ってください。

## 🎯 実装目標
Apache Arrowをネイティブデータ表現として採用し、QuantForgeを完全に再構築する。

## ⚡ 実証済みの成果
- **パフォーマンス**: 60.5%改善（10,000要素で166.71μs）
- **高速化**: 2.53倍（421.69μs → 166.71μs）
- **メモリ**: ゼロコピー実現
- **検証場所**: `playground/arrow_prototype/`

## 🔑 重要な前提条件
1. **既存ユーザー**: ゼロ（破壊的変更可能）
2. **レガシーコード**: 完全削除（残さない）
3. **技術的負債**: 作らない（C004/C014原則）

## 📁 実装計画
**詳細**: `plans/2025-09-01-arrow-native-migration.md`

### ディレクトリ構造（維持）
```
core/           # 内容を完全にArrow化
bindings/python/# 内容を完全にArrow化
src/            # 削除対象
```

### 実装手順
1. **Phase 1**: 準備（0.5日）
   - 依存関係追加: arrow = "56.0"
   - バックアップタグ作成

2. **Phase 2**: Core層Arrow化（2日）
   - `core/src/*`を削除
   - Arrow Computeカーネル実装
   - libm使用の数学関数

3. **Phase 3**: Bindings層Arrow化（1.5日）
   - `bindings/python/src/*`を削除
   - 最小限のFFI実装
   - Arrow直接API

4. **Phase 4**: 旧コード削除（0.5日）
   - `src/`ディレクトリ完全削除
   - バックアップ削除

5. **Phase 5**: 検証（1日）
   - 性能目標: 10,000要素<200μs
   - 正確性: Golden Master互換

## 🛠 技術的詳細

### Arrow計算の基本構造
```rust
// core/src/compute/black_scholes.rs
use arrow::array::{Float64Array, ArrayRef};

pub fn call_price(
    spots: &Float64Array,
    strikes: &Float64Array,
    times: &Float64Array,
    rates: &Float64Array,
    sigmas: &Float64Array,
) -> Result<ArrayRef, ArrowError> {
    // 直接Arrow配列で計算
}
```

### Python バインディング
```rust
// bindings/python/src/lib.rs
use numpy::{PyArray1, PyReadonlyArray1};

#[pyfunction]
fn call_price_numpy(
    spots: PyReadonlyArray1<f64>,
    // ...
) -> PyResult<Bound<PyArray1<f64>>> {
    // NumPy → Arrow → 計算 → NumPy
}
```

### 重要な最適化
- **並列化閾値**: 10,000要素
- **数学関数**: libm::erf使用
- **メモリ**: contiguous配列必須

## ⚠️ 注意事項

### やってはいけないこと
- 段階的移行（一気に置換）
- 互換性レイヤー作成
- レガシーコード残存
- NumPy優先設計

### 必ずやること
- Arrow-first設計
- ゼロコピー維持
- 単一データ表現
- テスト先行開発

## 📊 成功基準
- パフォーマンス: 10,000要素で<200μs
- メモリコピー: ゼロ
- コード削減: 67%（15,000→5,000行）
- テスト: 全Golden Master合格

## 🔗 参照資料
- プロトタイプ: `playground/arrow_prototype/`
- 移行計画: `plans/2025-09-01-arrow-native-migration.md`
- パフォーマンス分析: `playground/arrow_prototype/PERFORMANCE_ANALYSIS.md`
- プロジェクト原則: `.claude/critical-rules.xml`

## 💡 実装開始コマンド
```bash
# 新しいセッションで：
git checkout feature/arrow-native-migration
cat plans/2025-09-01-arrow-implementation-context.md  # この文書を確認
cat plans/2025-09-01-arrow-native-migration.md  # 詳細計画確認

# プロトタイプ確認
cd playground/arrow_prototype
cat PERFORMANCE_ANALYSIS.md  # 実証結果
cat src/lib.rs  # 実装参考

# 実装開始
cd ../..
# Phase 1から順次実装
```

## 🔍 要件定義が必要な場合

以下の点で不明瞭な部分があれば、実装前に明確化してください：

1. **API設計**
   - Arrow API と NumPy互換APIの優先度
   - エラーハンドリングの方針
   - 型システムの設計

2. **パフォーマンス目標**
   - 各データサイズでの具体的な目標値
   - メモリ使用量の制約
   - 並列化の詳細戦略

3. **互換性**
   - Golden Masterテストとの互換性レベル
   - 精度要件（相対誤差許容値）
   - 既存テストの扱い

## ✅ 実装進捗チェックリスト

実装を進める際は、以下のチェックリストを使用してください：

### Phase 1: 準備 ⬜
- [ ] feature/core-bindings-restructureブランチ確認
- [ ] バックアップタグ作成（`git tag pre-arrow-migration`）
- [ ] Cargo.tomlに arrow = "56.0" 追加
- [ ] 実装計画の最終確認

### Phase 2: Core層Arrow化 ⬜
- [ ] core/src/バックアップ作成
- [ ] 既存core/src/削除
- [ ] Arrow Computeカーネル実装
  - [ ] black_scholes.rs
  - [ ] black76.rs
  - [ ] merton.rs
  - [ ] american.rs
  - [ ] greeks.rs
- [ ] 数学関数移植（libm使用）
- [ ] Rustテスト作成・実行

### Phase 3: Bindings層Arrow化 ⬜
- [ ] bindings/python/src/バックアップ作成
- [ ] 既存bindings/python/src/削除
- [ ] 最小限FFI実装
- [ ] Arrow直接API実装
- [ ] NumPy互換レイヤー作成（オプション）
- [ ] Pythonテスト実行

### Phase 4: 旧コード削除 ⬜
- [ ] src/ディレクトリ削除
- [ ] バックアップディレクトリ削除
- [ ] Gitから完全削除
- [ ] ワークスペース設定更新

### Phase 5: 検証 ⬜
- [ ] パフォーマンステスト（10,000要素<200μs）
- [ ] 正確性テスト（Golden Master互換）
- [ ] メモリ使用量確認
- [ ] 最終ベンチマーク実行

---
このドキュメントは新しいセッションでの実装開始に必要な全文脈を含んでいます。
不明な点があれば、実装前に要件を明確化してください。