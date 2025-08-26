# パフォーマンスチューニング

環境とワークロードに応じた詳細なチューニングガイドです。

```{warning}
このページで説明されている高度なパフォーマンスチューニング機能（戦略選択、CPU固有最適化、NUMA設定など）は将来実装予定です。
現在は、QuantForgeが内部で自動的に最適化を行います。
```

## 環境別チューニング

### Linux

```bash
# CPU ガバナー設定
sudo cpupower frequency-set -g performance

# 巨大ページ有効化
echo 1024 | sudo tee /proc/sys/vm/nr_hugepages

# NUMA最適化
numactl --cpunodebind=0 --membind=0 python script.py
```

### macOS

```bash
# Apple Silicon最適化
export CARGO_BUILD_TARGET=aarch64-apple-darwin

# Rosetta回避（ネイティブ実行）
arch -arm64 python script.py
```

### Windows

```powershell
# 電源プラン
powercfg /setactive SCHEME_MIN

# プロセス優先度
Start-Process python.exe -ArgumentList "script.py" -Priority High
```

## CPU アーキテクチャ別設定

### Intel

```python
# AVX-512最適化
import quantforge as qf

if qf.has_avx512():
    qf.set_compute_strategy("avx512_optimized")
    qf.set_vector_width(16)  # 16要素並列
```

### AMD

```python
# Zen3以降の最適化
qf.set_compute_strategy("amd_zen3")
qf.enable_feature("avx2_256bit")  # 256ビット演算
```

### Apple Silicon

```python
# M1/M2最適化
qf.set_compute_strategy("apple_silicon")
qf.set_efficiency_cores(False)  # 高性能コアのみ使用
```

## ワークロード別設定

### リアルタイム処理

```python
# 低レイテンシ設定（将来実装予定）
# config APIは将来実装予定
# qf.config.set({
#     "strategy": "low_latency",
#     "batch_size": 100,
#     "prefetch": True,
#     "warm_cache": True
# })

# ウォームアップ（現在の使用方法）
import numpy as np
from quantforge.models import black_scholes
dummy_data = np.random.uniform(90, 110, 1000)
_ = black_scholes.call_price_batch(dummy_data, 100, 1.0, 0.05, 0.2)
```

### バッチ処理

```python
# 高スループット設定（将来実装予定）
# config APIは将来実装予定
# qf.config.set({
#     "strategy": "high_throughput",
#     "batch_size": 100_000,
#     "parallel_threshold": 10_000,
#     "memory_pool": True
# })

# 現在の大量バッチ処理
from quantforge.models import black_scholes
import numpy as np
spots = np.random.uniform(90, 110, 100_000)
prices = black_scholes.call_price_batch(spots, 100, 1.0, 0.05, 0.2)
```

### メモリ制限環境

```python
# 省メモリ設定（将来実装予定）
# config APIは将来実装予定
# qf.config.set({
#     "strategy": "memory_efficient",
#     "inplace_operations": True,
#     "streaming_mode": True,
#     "max_memory_mb": 512
# })

# 現在の省メモリ処理
from quantforge.models import black_scholes
# チャンク単位で処理
for chunk in np.array_split(spots, 10):
    prices = black_scholes.call_price_batch(chunk, 100, 1.0, 0.05, 0.2)
```

## バッチサイズ最適化

### 自動チューニング

```python
def find_optimal_batch_size(data_size, sample_rate=0.1):
    """最適なバッチサイズを自動検出"""
    
    sample_size = int(data_size * sample_rate)
    test_sizes = [100, 1000, 5000, 10000, 50000, 100000]
    
    best_time = float('inf')
    best_size = test_sizes[0]
    
    for size in test_sizes:
        if size > sample_size:
            break
        
        test_data = np.random.uniform(90, 110, size)
        
        start = time.perf_counter()
        _ = qf.calculate(test_data, 100, 0.05, 0.2, 1.0)
        elapsed = time.perf_counter() - start
        
        throughput = size / elapsed
        
        if throughput > best_time:
            best_time = throughput
            best_size = size
    
    return best_size

optimal = find_optimal_batch_size(1_000_000)
print(f"Optimal batch size: {optimal}")
```

## メモリ帯域幅最適化

### プリフェッチ

```python
# データプリフェッチ
def prefetch_calculate(spots, strikes, rate, vol, time):
    # 次のバッチをプリフェッチ
    qf.prefetch(spots[1000:2000])
    
    # 現在のバッチを処理
    result = qf.calculate(spots[:1000], strikes, rate, vol, time)
    
    return result
```

### NUMA対応

```python
import psutil

def numa_aware_processing(data):
    """NUMA最適化処理"""
    
    # CPUトポロジー取得
    cpu_count = psutil.cpu_count(logical=False)
    numa_nodes = psutil.cpu_count() // cpu_count
    
    if numa_nodes > 1:
        # NUMAノードごとに分割
        chunks = np.array_split(data, numa_nodes)
        results = []
        
        for node, chunk in enumerate(chunks):
            # ノードにバインド
            qf.set_numa_node(node)
            result = qf.calculate(chunk, ...)
            results.append(result)
        
        return np.concatenate(results)
    else:
        return qf.calculate(data, ...)
```

## 電力効率

### 省電力モード

```python
# バッテリー動作時の設定
def battery_optimized_config():
    # 将来実装予定の電力効率設定
    # qf.config.set({
    #     "power_mode": "efficiency",
    #     "max_threads": 4,
    #     "vector_width": 4,
    #     "frequency_scaling": "auto"
    # })
    pass  # 現在は内部で自動最適化
```

### 温度管理

```python
import psutil

def thermal_aware_processing(data):
    """温度を考慮した処理"""
    
    temp = psutil.sensors_temperatures()
    cpu_temp = temp['coretemp'][0].current if 'coretemp' in temp else 0
    
    if cpu_temp > 80:
        # 高温時はスロットリング
        qf.set_compute_strategy("thermal_throttle")
        qf.set_max_threads(2)
    elif cpu_temp > 60:
        # 中温時は控えめ
        qf.set_compute_strategy("balanced")
    else:
        # 低温時は最大性能
        qf.set_compute_strategy("maximum_performance")
    
    return qf.calculate(data, ...)
```

## ベンチマークとプロファイル

### 包括的ベンチマーク

```python
def comprehensive_benchmark():
    """詳細なベンチマーク"""
    
    sizes = [100, 1000, 10000, 100000, 1000000]
    strategies = ["sequential", "simd", "parallel", "hybrid"]
    
    results = {}
    
    for size in sizes:
        data = np.random.uniform(90, 110, size)
        results[size] = {}
        
        for strategy in strategies:
            qf.set_compute_strategy(strategy)
            
            times = []
            for _ in range(10):
                start = time.perf_counter()
                _ = qf.calculate(data, 100, 0.05, 0.2, 1.0)
                times.append(time.perf_counter() - start)
            
            results[size][strategy] = {
                'mean': np.mean(times),
                'std': np.std(times),
                'min': np.min(times),
                'max': np.max(times)
            }
    
    return results
```

## トラブルシューティング

### パフォーマンス診断

```python
def diagnose_performance():
    """パフォーマンス問題の診断"""
    
    print("System Information:")
    print(f"CPU: {psutil.cpu_count()} cores")
    print(f"Memory: {psutil.virtual_memory().total / 1e9:.1f} GB")
    print(f"AVX2: {qf.has_avx2()}")
    print(f"AVX-512: {qf.has_avx512()}")
    
    # テスト実行
    test_sizes = [100, 10000, 1000000]
    
    for size in test_sizes:
        data = np.random.uniform(90, 110, size)
        
        start = time.perf_counter()
        _ = qf.calculate(data, 100, 0.05, 0.2, 1.0)
        elapsed = time.perf_counter() - start
        
        throughput = size / elapsed
        latency = elapsed / size * 1e9
        
        print(f"\nSize {size}:")
        print(f"  Time: {elapsed*1000:.2f}ms")
        print(f"  Throughput: {throughput/1e6:.1f}M ops/sec")
        print(f"  Latency: {latency:.1f}ns/op")

diagnose_performance()
```

## まとめ

効果的なチューニングのポイント：

1. **環境理解**: ハードウェア特性を把握
2. **ワークロード分析**: データ特性とパターン理解
3. **段階的最適化**: ボトルネックから順に対処
4. **継続的測定**: 変更の効果を定量的に評価
5. **バランス**: 性能と消費電力のトレードオフ