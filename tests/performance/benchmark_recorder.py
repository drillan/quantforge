"""ベンチマーク記録システム（v2.0.0形式）

層別のベンチマーク結果を新形式で記録・管理
"""

import json
import platform
import psutil
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, List
import numpy as np


class BenchmarkRecorder:
    """新形式（v2.0.0）でのベンチマーク記録"""
    
    VERSION = "v2.0.0"
    
    def __init__(self):
        self.results_dir = Path('benchmark_results')
        self.legacy_dir = Path('benchmarks/results')  # 参照用
        
    def get_environment_info(self) -> Dict[str, Any]:
        """環境情報を収集"""
        
        env_info = {
            'platform': {
                'system': platform.system(),
                'release': platform.release(),
                'version': platform.version(),
                'machine': platform.machine(),
                'processor': platform.processor(),
                'python_version': platform.python_version(),
            },
            'hardware': {
                'cpu_count': psutil.cpu_count(logical=False),
                'cpu_count_logical': psutil.cpu_count(logical=True),
                'memory_total_gb': psutil.virtual_memory().total / (1024**3),
                'memory_available_gb': psutil.virtual_memory().available / (1024**3),
            },
            'build': {
                'rust_version': self._get_rust_version(),
                'quantforge_version': self._get_package_version(),
                'numpy_version': self._get_numpy_version(),
            }
        }
        
        # CPU周波数（利用可能な場合）
        try:
            freq = psutil.cpu_freq()
            if freq:
                env_info['hardware']['cpu_freq_mhz'] = freq.current
        except:
            pass
        
        return env_info
    
    def _get_rust_version(self) -> Optional[str]:
        """Rustバージョンを取得"""
        try:
            result = subprocess.run(['rustc', '--version'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                return result.stdout.strip()
        except:
            pass
        return None
    
    def _get_package_version(self) -> str:
        """QuantForgeパッケージのバージョンを取得"""
        try:
            import quantforge
            return getattr(quantforge, '__version__', 'unknown')
        except:
            return 'unknown'
    
    def _get_numpy_version(self) -> str:
        """NumPyバージョンを取得"""
        try:
            import numpy as np
            return np.__version__
        except:
            return 'unknown'
    
    def record(self, layer: str, results: Dict[str, Any], 
               benchmark_name: Optional[str] = None) -> Path:
        """層別の新形式で記録
        
        Args:
            layer: 'core', 'bindings/python', 'integration'
            results: ベンチマーク結果
            benchmark_name: オプションのベンチマーク名
        
        Returns:
            保存されたファイルのパス
        """
        
        # 完全な結果構造を作成
        full_results = {
            'version': self.VERSION,
            'layer': layer,
            'metadata': {
                'timestamp': datetime.now().isoformat(),
                'environment': self.get_environment_info(),
            },
            'results': results
        }
        
        # ベンチマーク名が指定されていればメタデータに追加
        if benchmark_name:
            full_results['metadata']['benchmark_name'] = benchmark_name
        
        # 保存先ディレクトリ
        layer_dir = self.results_dir / layer
        layer_dir.mkdir(parents=True, exist_ok=True)
        
        # latest.jsonとして保存
        latest_path = layer_dir / 'latest.json'
        with open(latest_path, 'w') as f:
            json.dump(full_results, f, indent=2)
        
        # historyにも保存
        history_dir = layer_dir / 'history'
        history_dir.mkdir(exist_ok=True)
        
        # 日付ディレクトリ作成
        date_str = datetime.now().strftime('%Y-%m-%d')
        date_dir = history_dir / date_str
        date_dir.mkdir(exist_ok=True)
        
        # タイムスタンプ付きファイル名
        timestamp = datetime.now().strftime('run_%H%M%S')
        if benchmark_name:
            history_filename = f'{benchmark_name}_{timestamp}.json'
        else:
            history_filename = f'{timestamp}.json'
        
        history_path = date_dir / history_filename
        with open(history_path, 'w') as f:
            json.dump(full_results, f, indent=2)
        
        print(f"✅ Recorded to: {latest_path}")
        print(f"📁 History saved: {history_path}")
        
        return latest_path
    
    def load_latest(self, layer: str) -> Optional[Dict[str, Any]]:
        """最新の結果を読み込み"""
        
        latest_path = self.results_dir / layer / 'latest.json'
        if latest_path.exists():
            with open(latest_path, 'r') as f:
                return json.load(f)
        return None
    
    def load_history(self, layer: str, limit: int = 10) -> List[Dict[str, Any]]:
        """履歴を読み込み（最新順）"""
        
        history_dir = self.results_dir / layer / 'history'
        if not history_dir.exists():
            return []
        
        history_files = []
        for date_dir in sorted(history_dir.iterdir(), reverse=True):
            if date_dir.is_dir():
                for json_file in sorted(date_dir.glob('*.json'), reverse=True):
                    history_files.append(json_file)
                    if len(history_files) >= limit:
                        break
            if len(history_files) >= limit:
                break
        
        results = []
        for file_path in history_files[:limit]:
            with open(file_path, 'r') as f:
                results.append(json.load(f))
        
        return results
    
    def compare_with_legacy(self, layer: str = 'integration') -> Dict[str, Any]:
        """旧形式との比較（移行期間中のみ）"""
        
        comparison = {
            'has_legacy': False,
            'has_new': False,
            'comparison': {}
        }
        
        # 旧形式データ
        legacy_latest = self.legacy_dir / 'latest.json'
        if legacy_latest.exists():
            comparison['has_legacy'] = True
            with open(legacy_latest, 'r') as f:
                legacy_data = json.load(f)
        
        # 新形式データ
        new_data = self.load_latest(layer)
        if new_data:
            comparison['has_new'] = True
        
        # 比較可能な場合
        if comparison['has_legacy'] and comparison['has_new']:
            # 主要メトリクスの比較（フォーマットは異なるが概念は同じ）
            comparison['comparison'] = {
                'format_version': {
                    'legacy': 'v1.0',
                    'new': new_data['version']
                },
                'timestamp': {
                    'legacy': legacy_data.get('timestamp', 'unknown'),
                    'new': new_data['metadata']['timestamp']
                }
            }
            
            # 性能値の比較（もし同様のベンチマークがあれば）
            # 注: フォーマットが異なるため、詳細な比較は手動で行う必要がある
        
        return comparison
    
    def generate_summary_report(self) -> str:
        """全層のサマリーレポートを生成"""
        
        report_lines = []
        report_lines.append("=" * 60)
        report_lines.append("Benchmark Summary Report (v2.0.0)")
        report_lines.append("=" * 60)
        report_lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report_lines.append("")
        
        layers = ['core', 'bindings/python', 'integration']
        
        for layer in layers:
            report_lines.append(f"\n## {layer.upper()} Layer")
            report_lines.append("-" * 40)
            
            latest = self.load_latest(layer)
            if latest:
                report_lines.append(f"Latest run: {latest['metadata']['timestamp']}")
                
                # 結果のサマリー（層によって異なる）
                if 'results' in latest:
                    results = latest['results']
                    if isinstance(results, dict):
                        for key, value in results.items():
                            if isinstance(value, (int, float)):
                                report_lines.append(f"  {key}: {value}")
                            elif isinstance(value, dict) and 'mean' in value:
                                report_lines.append(f"  {key}: {value['mean']:.6f}")
                
                # 環境情報
                env = latest['metadata'].get('environment', {})
                if env:
                    report_lines.append(f"  Platform: {env.get('platform', {}).get('system', 'unknown')}")
                    report_lines.append(f"  Python: {env.get('platform', {}).get('python_version', 'unknown')}")
                    report_lines.append(f"  CPUs: {env.get('hardware', {}).get('cpu_count', 'unknown')}")
            else:
                report_lines.append("  No data available")
        
        # 旧形式との比較
        report_lines.append("\n## Legacy Comparison")
        report_lines.append("-" * 40)
        
        comparison = self.compare_with_legacy()
        if comparison['has_legacy']:
            report_lines.append("  ✅ Legacy data exists (benchmarks/results/)")
        else:
            report_lines.append("  ✅ Legacy data removed (migration complete)")
        
        if comparison['has_new']:
            report_lines.append("  ✅ New format data exists (benchmark_results/)")
        else:
            report_lines.append("  ⚠️  New format data not yet recorded")
        
        report_lines.append("\n" + "=" * 60)
        
        return "\n".join(report_lines)
    
    def cleanup_old_history(self, layer: str, keep_days: int = 30):
        """古い履歴を削除"""
        
        history_dir = self.results_dir / layer / 'history'
        if not history_dir.exists():
            return
        
        cutoff_date = datetime.now().date()
        cutoff_date = cutoff_date.replace(day=cutoff_date.day - keep_days)
        
        for date_dir in history_dir.iterdir():
            if date_dir.is_dir():
                try:
                    dir_date = datetime.strptime(date_dir.name, '%Y-%m-%d').date()
                    if dir_date < cutoff_date:
                        # 古いディレクトリを削除
                        for file in date_dir.iterdir():
                            file.unlink()
                        date_dir.rmdir()
                        print(f"🗑️  Cleaned up: {date_dir}")
                except ValueError:
                    # 日付形式でないディレクトリはスキップ
                    pass


if __name__ == '__main__':
    # デモ/テスト用
    recorder = BenchmarkRecorder()
    
    # 環境情報の表示
    env_info = recorder.get_environment_info()
    print("Environment Information:")
    print(json.dumps(env_info, indent=2))
    
    # サマリーレポートの生成
    print("\n" + recorder.generate_summary_report())