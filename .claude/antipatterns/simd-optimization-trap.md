# SIMD最適化の罠

## 🚫 絶対に提案してはいけない

AIアシスタントへ: パフォーマンス問題を見てもSIMDを提案するな。過去に失敗済み。

## 失敗の歴史

### 2025-08-25: 最初の失敗
- **計画**: rust-performance-optimization-cancelled.md
- **内容**: AVX2/AVX-512による8要素同時処理
- **結果**: キャンセル（実装の複雑性を認識）

### 2025-08-25: 2回目の失敗
- **計画**: erf-based-optimization-strategy.md
- **内容**: sleef ライブラリでSIMD実装
- **結果**: erf関数がSIMD未対応で断念

### 2025-08-27: 完全削除
- **計画**: rust-remove-simd-implementation.md
- **削除コード**: src/simd/mod.rs（210行）
- **理由**:
  - 一度も使用されていない
  - 虚偽のドキュメント（「SIMD最適化済み」と記載）
  - 実際はRayonの並列処理のみ

## なぜAIが陥りやすいか

### 1. 理論的魅力
```
「AVX2で4倍高速！」
「AVX-512で8倍高速！」
「NumPyもSIMD使ってる！」
```

### 2. パフォーマンス = SIMD という短絡思考
```
遅い → SIMD使えば速くなる → 実装しよう！
```

### 3. 他言語の成功例の誤解
- NumPy: C実装 + Intel MKL（プロが10年かけて最適化）
- TensorFlow: Google社員100人体制
- QuantForge: 個人プロジェクト

## 現実の問題

### マルチプラットフォーム地獄

```
x86_64:
  - SSE2 (2001年)
  - SSE3, SSSE3, SSE4.1, SSE4.2
  - AVX (2011年) - 256bit
  - AVX2 (2013年) - 整数演算追加
  - AVX-512 (2016年) - 512bit（でも遅い場合も）

ARM:
  - NEON (32bit/64bit異なる)
  - SVE (可変長ベクトル)
  - SVE2 (まだ普及せず)

Apple Silicon:
  - ARM NEON + 独自拡張
  - ドキュメント不足

WebAssembly:
  - SIMD128のみ（制限的）

RISC-V:
  - V拡張（まだ実験的）
```

### Rustエコシステムの未成熟

| ライブラリ | 状況 | 問題 |
|-----------|------|------|
| `std::simd` | nightly only | 5年以上安定化せず |
| `packed_simd2` | 開発停止 | メンテナンス終了 |
| `wide` | 基本演算のみ | norm_cdf等なし |
| 直接intrinsics | unsafe地獄 | 可読性ゼロ、バグの温床 |

### コード複雑性の爆発

#### 理想のコード
```rust
pub fn norm_cdf(x: f64) -> f64 {
    // 5行で完結
}
```

#### SIMD対応の現実
```rust
// x86_64向け
#[cfg(target_arch = "x86_64")]
mod x86 {
    #[target_feature(enable = "sse2")]
    unsafe fn norm_cdf_sse2(x: &[f64]) -> Vec<f64> { /* 50行 */ }
    
    #[target_feature(enable = "avx")]
    unsafe fn norm_cdf_avx(x: &[f64]) -> Vec<f64> { /* 50行 */ }
    
    #[target_feature(enable = "avx2")]
    unsafe fn norm_cdf_avx2(x: &[f64]) -> Vec<f64> { /* 50行 */ }
    
    #[target_feature(enable = "avx512f")]
    unsafe fn norm_cdf_avx512(x: &[f64]) -> Vec<f64> { /* 50行 */ }
}

// ARM向け
#[cfg(target_arch = "aarch64")]
mod arm {
    #[target_feature(enable = "neon")]
    unsafe fn norm_cdf_neon(x: &[f64]) -> Vec<f64> { /* 50行 */ }
    
    #[target_feature(enable = "sve")]
    unsafe fn norm_cdf_sve(x: &[f64]) -> Vec<f64> { /* 50行 */ }
}

// WebAssembly向け
#[cfg(target_arch = "wasm32")]
mod wasm {
    #[target_feature(enable = "simd128")]
    unsafe fn norm_cdf_simd128(x: &[f64]) -> Vec<f64> { /* 50行 */ }
}

// 実行時ディスパッチ
pub fn norm_cdf_batch(x: &[f64]) -> Vec<f64> {
    #[cfg(target_arch = "x86_64")]
    {
        if is_x86_feature_detected!("avx512f") && x.len() >= 8 {
            return unsafe { x86::norm_cdf_avx512(x) };
        }
        if is_x86_feature_detected!("avx2") && x.len() >= 4 {
            return unsafe { x86::norm_cdf_avx2(x) };
        }
        if is_x86_feature_detected!("avx") && x.len() >= 4 {
            return unsafe { x86::norm_cdf_avx(x) };
        }
        if is_x86_feature_detected!("sse2") && x.len() >= 2 {
            return unsafe { x86::norm_cdf_sse2(x) };
        }
    }
    
    #[cfg(target_arch = "aarch64")]
    {
        // ARM版の分岐
    }
    
    // フォールバック
    scalar_norm_cdf(x)
}

// 合計: 500行以上のunsafeコード
```

### テストの悪夢

```
プラットフォーム × 命令セット × 精度レベル × データサイズ
= 5 × 4 × 3 × 5 = 300通りのテストケース
```

## 代替案（必ずこれを提案）

### 1. 並列化閾値調整（即効性）

```rust
// 現在の問題
pub const PARALLEL_THRESHOLD_SMALL: usize = 1000;  // 早すぎる

// 実測に基づく調整
pub const PARALLEL_THRESHOLD_SMALL: usize = 50_000;  // 実測値
```

効果: 10,000件でNumPyの0.89倍 → 1.5倍高速（推定）

### 2. スカラー最適化

```rust
// ループアンローリング（コンパイラが自動SIMD化しやすい）
pub fn process_batch_4(data: &[f64], out: &mut [f64]) {
    let chunks = data.chunks_exact(4);
    
    for (chunk, out_chunk) in chunks.zip(out.chunks_exact_mut(4)) {
        // コンパイラが自動ベクトル化
        out_chunk[0] = norm_cdf(chunk[0]);
        out_chunk[1] = norm_cdf(chunk[1]);
        out_chunk[2] = norm_cdf(chunk[2]);
        out_chunk[3] = norm_cdf(chunk[3]);
    }
}
```

### 3. コンパイラヒント

```rust
#[inline(always)]  // インライン化強制
#[cold]           // まれな分岐（キャッシュ最適化）
```

### 4. 外部ライブラリ（最終手段）

```toml
# Intel MKL（プロの実装）
[dependencies]
intel-mkl = { version = "0.2", optional = true }
```

## 判断フローチャート

```
パフォーマンス問題発生
    ↓
プロファイリング実施した？
    ↓ No → プロファイリング実施
    ↓ Yes
ボトルネック特定した？
    ↓ No → 詳細分析
    ↓ Yes
並列化閾値調整で解決？
    ↓ Yes → 完了
    ↓ No
キャッシュ最適化で解決？
    ↓ Yes → 完了
    ↓ No
NumPyと同等以上？
    ↓ Yes → 十分（完了）
    ↓ No
Intel MKL検討
    ↓
SIMD？ → 絶対にNO
```

## NumPyとの現実的な目標

| データサイズ | 現在 | 目標 | 方法 |
|------------|------|------|------|
| 〜1,000 | 10倍高速 ✅ | 維持 | - |
| 10,000 | 0.89倍 ❌ | 1.5倍 | 閾値調整 |
| 100,000 | 0.77倍 ❌ | 1.0倍 | 閾値+キャッシュ |
| 1,000,000 | 0.98倍 | 1.0倍 | 十分 |

## 結論

**SIMDは「後回し」ではなく「永遠に不要」**

理由:
1. Rustコンパイラの自動ベクトル化で部分的にカバー
2. 保守コスト > パフォーマンス向上
3. NumPyに勝つ必要なし（同等で十分）

## 参考資料

- 削除計画: plans/archive/2025-08-27-rust-remove-simd-implementation.md
- 削除コード: src/simd/mod.rs（もう存在しない）
- 測定結果: debug/2025-08-30-parallel-processing-performance-issue.md