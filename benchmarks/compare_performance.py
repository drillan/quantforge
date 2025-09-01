#!/usr/bin/env python
"""パフォーマンス改善の検証スクリプト"""

import json
import sys
from pathlib import Path

def load_benchmark_results(file_path):
    """ベンチマーク結果をロード"""
    with open(file_path, 'r') as f:
        return json.load(f)

def extract_metrics(data):
    """ベンチマーク結果から重要なメトリクスを抽出"""
    metrics = {}
    
    # 新しいフォーマット（pytest-benchmark）
    if 'benchmarks' in data and data['benchmarks']:
        for benchmark in data.get('benchmarks', []):
            name = benchmark['name']
            # グループ名とパラメータを解析
            if '[' in name:
                base_name = name[:name.index('[')]
                param = name[name.index('[') + 1:name.index(']')]
                key = f"{base_name}[{param}]"
            else:
                key = name
            
            metrics[key] = {
                'mean': benchmark['stats']['mean'],
                'min': benchmark['stats']['min'],
                'max': benchmark['stats']['max'],
                'stddev': benchmark['stats']['stddev'],
            }
    
    # レガシーフォーマット（カスタムJSON）
    elif 'single' in data or 'batch' in data:
        # シングル計算（値は秒単位で格納されている）
        if 'single' in data and 'quantforge' in data['single']:
            value = data['single']['quantforge']
            metrics['test_quantforge_single'] = {
                'mean': value,  # すでに秒単位
                'min': value,
                'max': value,
                'stddev': 0,
            }
        
        # バッチ計算（リスト形式）
        if 'batch' in data and isinstance(data['batch'], list):
            for batch_result in data['batch']:
                if 'size' in batch_result and 'quantforge' in batch_result:
                    size = batch_result['size']
                    value = batch_result['quantforge']
                    metrics[f'test_quantforge_batch[{size}]'] = {
                        'mean': value,  # すでに秒単位
                        'min': value,
                        'max': value,
                        'stddev': 0,
                    }
    
    return metrics

def compare_results(baseline_path, optimized_path):
    """ベースラインと最適化後の結果を比較"""
    
    # ファイルの存在確認
    if not Path(baseline_path).exists():
        print(f"❌ ベースラインファイルが見つかりません: {baseline_path}")
        return
    
    if not Path(optimized_path).exists():
        print(f"❌ 最適化後ファイルが見つかりません: {optimized_path}")
        return
    
    # データをロード
    baseline = load_benchmark_results(baseline_path)
    optimized = load_benchmark_results(optimized_path)
    
    # メトリクスを抽出
    baseline_metrics = extract_metrics(baseline)
    optimized_metrics = extract_metrics(optimized)
    
    # 結果を比較
    print("=" * 80)
    print("📊 パフォーマンス改善の検証結果")
    print("=" * 80)
    print()
    
    # 重要なベンチマークに焦点を当てる
    key_benchmarks = [
        'test_quantforge_single',
        'test_quantforge_batch[100]',
        'test_quantforge_batch[1000]',
        'test_quantforge_batch[10000]',
    ]
    
    improvements = []
    degradations = []
    
    for key in key_benchmarks:
        if key in baseline_metrics and key in optimized_metrics:
            baseline_mean = baseline_metrics[key]['mean']
            optimized_mean = optimized_metrics[key]['mean']
            
            # 改善率を計算（負の値は改善を示す）
            improvement = ((optimized_mean - baseline_mean) / baseline_mean) * 100
            
            # 結果を表示
            if improvement < 0:
                status = "✅ 改善"
                improvements.append((key, improvement))
            elif improvement > 5:
                status = "❌ 劣化"
                degradations.append((key, improvement))
            else:
                status = "➡️  同等"
            
            print(f"{key:40} {status:10} {improvement:+.1f}%")
            print(f"  Baseline:  {baseline_mean*1e9:10.2f} ns")
            print(f"  Optimized: {optimized_mean*1e9:10.2f} ns")
            print()
    
    # サマリー
    print("=" * 80)
    print("📝 サマリー")
    print("=" * 80)
    
    if improvements:
        print("\n✅ 改善されたケース:")
        for key, imp in improvements:
            print(f"  - {key}: {-imp:.1f}% 高速化")
    
    if degradations:
        print("\n❌ 劣化したケース:")
        for key, deg in degradations:
            print(f"  - {key}: {deg:.1f}% 遅延")
    
    # 全体評価
    print("\n🎯 全体評価:")
    if len(improvements) > len(degradations):
        print("  最適化は全体的に成功しました！")
    elif degradations:
        print("  一部のケースで性能劣化が見られます。追加の調査が必要です。")
    else:
        print("  最適化により性能が維持されています。")
    
    # 10,000要素のケースに特別な注意
    if 'test_quantforge_batch[10000]' in baseline_metrics and 'test_quantforge_batch[10000]' in optimized_metrics:
        baseline_10k = baseline_metrics['test_quantforge_batch[10000]']['mean'] * 1e9
        optimized_10k = optimized_metrics['test_quantforge_batch[10000]']['mean'] * 1e9
        improvement_10k = ((optimized_10k - baseline_10k) / baseline_10k) * 100
        
        print("\n📌 並列化閾値変更の効果（10,000要素）:")
        if improvement_10k < -20:
            print(f"  ✅ 大幅な改善: {-improvement_10k:.1f}% 高速化")
            print(f"  並列化閾値を50,000に変更したことで、不要な並列化オーバーヘッドが削減されました。")
        elif improvement_10k < 0:
            print(f"  ✅ 改善: {-improvement_10k:.1f}% 高速化")
        else:
            print(f"  ⚠️  期待された改善が見られません: {improvement_10k:+.1f}%")
            print(f"  追加の調査が必要です。")

if __name__ == "__main__":
    # ベースラインと最新の結果を比較
    baseline_path = "/home/driller/work/quantforge/benchmarks/results/latest.json"
    
    # 最新の最適化結果を探す
    results_dir = Path("benchmarks/results")
    optimized_files = sorted(results_dir.glob("optimized_*.json"))
    
    if optimized_files:
        optimized_path = optimized_files[-1]  # 最新のファイル
        print(f"比較対象:")
        print(f"  Baseline:  {baseline_path}")
        print(f"  Optimized: {optimized_path}")
        print()
        
        compare_results(baseline_path, optimized_path)
    else:
        print("❌ 最適化後のベンチマーク結果が見つかりません")
        sys.exit(1)