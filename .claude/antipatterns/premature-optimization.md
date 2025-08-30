# 早すぎる最適化

## 🚫 測定前の最適化は絶対禁止

AIアシスタントへ: プロファイリング前に「ここが遅そう」と推測するな。データで語れ。

## Donald Knuthの警告

> "早すぎる最適化は諸悪の根源である"
> 
> "我々はプログラムの重要でない部分の速度について考えたり悩んだりして、
> 膨大な時間を無駄にすべきではない"

## 禁止行為

### ❌ 推測による最適化

```
「このループが遅そうだから...」
「ここでメモリアロケーションが多そう...」
「おそらくこの関数がボトルネック...」
「きっとキャッシュミスが...」
```

### ❌ 測定なしの判断

```rust
// 推測: 「平方根は重い計算だから事前計算しよう」
let sqrt_t = t.sqrt();  // 実際: 全体の0.01%

// 推測: 「割り算は遅いから乗算に変換」
let x = y * 0.5;  // 実際: コンパイラが最適化済み

// 推測: 「関数呼び出しのオーバーヘッドが...」
#[inline(always)]  // 実際: インライン化で逆に遅くなる場合も
```

## 実際の失敗例

### 例1: norm_cdf最適化の迷走
```
推測: 「Taylor展開の項数を減らせば速くなる」
実装: 4次から3次に削減
結果: 速度 1%向上、精度 1000倍悪化 → 使い物にならない
```

### 例2: 並列化閾値の推測
```
推測: 「1,000要素あれば並列化が有効」
実装: PARALLEL_THRESHOLD_SMALL = 1000
結果: 10,000要素でNumPyより遅い → 逆効果
真実: 50,000要素以上で有効（実測により判明）
```

### 例3: メモリレイアウト最適化
```
推測: 「Structure of Arrays（SoA）の方が速い」
実装: 大規模リファクタリング（2週間）
結果: 3%高速化 → 労力に見合わない
```

## 正しいアプローチ

### 1. 測定 → 分析 → 最適化

```bash
# Step 1: プロファイリング
cargo install flamegraph
cargo flamegraph --bench benchmarks

# Step 2: ボトルネック特定
# flamegraph.svgを確認
# 上位3つの関数をメモ

# Step 3: 仮説立案
# 「norm_cdfが全体の40%」→ ここを最適化

# Step 4: 最適化実施
# 具体的なデータに基づく改善

# Step 5: 再測定
# 改善を確認
```

### 2. 80-20ルール（パレートの法則）

```
実行時間の80% = コードの20%
最適化すべき箇所 = その20%のみ
```

実例:
```
全体の実行時間: 100ms
├─ norm_cdf: 40ms (40%) ← ここを最適化
├─ exp: 30ms (30%) ← 次の候補
├─ その他1000関数: 30ms (30%) ← 無視
```

### 3. ベンチマーク駆動開発

```rust
#[bench]
fn bench_before_optimization(b: &mut Bencher) {
    b.iter(|| current_implementation());
    // 結果: 100ns/iter
}

// 最適化実施

#[bench]
fn bench_after_optimization(b: &mut Bencher) {
    b.iter(|| optimized_implementation());
    // 結果: 80ns/iter → 20%改善を確認
}
```

## よくある誤解

### 誤解1: 「複雑な実装 = 遅い」
```rust
// シンプル（でも遅い）
for i in 0..n {
    for j in 0..n {
        result[i][j] = a[i] * b[j];
    }
}

// 複雑（でも速い: キャッシュ効率的）
for i in (0..n).step_by(BLOCK) {
    for j in (0..n).step_by(BLOCK) {
        // ブロック処理
    }
}
```

### 誤解2: 「unsafe = 速い」
```rust
// unsafe（危険で遅い場合も）
unsafe {
    *ptr.add(i) = value;
}

// safe（コンパイラが最適化）
vec[i] = value;  // 境界チェックは最適化で除去される
```

### 誤解3: 「アロケーション = 悪」
```rust
// 過度な事前アロケーション
let mut huge_buffer = Vec::with_capacity(1_000_000);
// 実際は100要素しか使わない → メモリの無駄

// 適切なサイズ
let mut buffer = Vec::with_capacity(expected_size);
```

## プロファイリングツール

### Rust用
```bash
# CPU プロファイリング
cargo install flamegraph
cargo flamegraph

# 詳細プロファイリング
cargo install cargo-profiling
cargo profiling

# ベンチマーク
cargo bench
cargo install criterion
```

### システムレベル
```bash
# Linux
perf record ./target/release/quantforge
perf report

# macOS
instruments -t "Time Profiler" ./target/release/quantforge
```

## 最適化の判断基準

```
最適化を検討すべきか？
    ↓
実際に遅いか？
    ↓ No → 最適化不要
    ↓ Yes
測定したか？
    ↓ No → プロファイリング実施
    ↓ Yes
全体の10%以上を占めるか？
    ↓ No → 最適化不要
    ↓ Yes
簡単に改善できるか？
    ↓ No → 費用対効果を検討
    ↓ Yes
最適化実施
```

## 実際に効果的な最適化

### 測定で証明された改善

1. **並列化閾値調整**
   - 測定: 10,000要素でNumPyより遅い
   - 原因: オーバーヘッド > 利益
   - 改善: 閾値を50,000に
   - 結果: 1.5倍高速化

2. **キャッシュ最適化**
   - 測定: L1キャッシュミス率40%
   - 原因: データレイアウト
   - 改善: チャンクサイズ調整
   - 結果: 30%高速化

3. **関数インライン化**
   - 測定: 小関数の呼び出しが20%
   - 改善: `#[inline]`追加
   - 結果: 15%高速化

## チェックリスト

最適化前に必ず確認:

- [ ] 実際に遅いことを体感したか
- [ ] プロファイリングを実施したか
- [ ] ボトルネックを特定したか
- [ ] 全体の10%以上を占めるか
- [ ] 改善案の効果を見積もったか
- [ ] 複雑性の増加を評価したか

## 結論

**推測するな、測定せよ**

最適化は科学。データなき最適化は迷信。

## 参考資料

- The Art of Computer Programming, Vol.1 - Donald Knuth
- 実測データ: benchmarks/results/
- プロファイリング結果: target/profiling/