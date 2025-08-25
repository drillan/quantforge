"""Black-Scholesモデル実装（GBS_2025.pyから抽出）.

MIT License - Copyright (c) 2025 Davis William Edwards
ゴールデンマスター生成専用 - 本番コードでは使用しないこと
"""

import math
from typing import Tuple
from scipy.stats import norm


class BlackScholesReference:
    """GBS_2025.pyから抽出したBlack-Scholesモデル参照実装."""
    
    @staticmethod
    def _gbs(option_type: str, fs: float, x: float, t: float, 
             r: float, b: float, v: float) -> Tuple[float, float, float, float, float, float]:
        """一般化Black-Scholesモデル（内部実装）.
        
        Args:
            option_type: "c" for call, "p" for put
            fs: スポット/フォワード価格
            x: 権利行使価格
            t: 満期までの時間（年）
            r: リスクフリーレート
            b: コスト・オブ・キャリー
            v: インプライドボラティリティ
            
        Returns:
            (価格, デルタ, ガンマ, シータ, ベガ, ロー)のタプル
        """
        # 基本計算
        t_sqrt = math.sqrt(t)
        d1 = (math.log(fs / x) + (b + (v * v) / 2) * t) / (v * t_sqrt)
        d2 = d1 - v * t_sqrt
        
        if option_type == "c":
            # コールオプション
            value = fs * math.exp((b - r) * t) * norm.cdf(d1) - x * math.exp(-r * t) * norm.cdf(d2)
            delta = math.exp((b - r) * t) * norm.cdf(d1)
            gamma = math.exp((b - r) * t) * norm.pdf(d1) / (fs * v * t_sqrt)
            theta = -(fs * v * math.exp((b - r) * t) * norm.pdf(d1)) / (2 * t_sqrt) - \
                    (b - r) * fs * math.exp((b - r) * t) * norm.cdf(d1) - \
                    r * x * math.exp(-r * t) * norm.cdf(d2)
            vega = math.exp((b - r) * t) * fs * t_sqrt * norm.pdf(d1)
            rho = x * t * math.exp(-r * t) * norm.cdf(d2)
        else:
            # プットオプション
            value = x * math.exp(-r * t) * norm.cdf(-d2) - fs * math.exp((b - r) * t) * norm.cdf(-d1)
            delta = -math.exp((b - r) * t) * norm.cdf(-d1)
            gamma = math.exp((b - r) * t) * norm.pdf(d1) / (fs * v * t_sqrt)
            theta = -(fs * v * math.exp((b - r) * t) * norm.pdf(d1)) / (2 * t_sqrt) + \
                    (b - r) * fs * math.exp((b - r) * t) * norm.cdf(-d1) + \
                    r * x * math.exp(-r * t) * norm.cdf(-d2)
            vega = math.exp((b - r) * t) * fs * t_sqrt * norm.pdf(d1)
            rho = -x * t * math.exp(-r * t) * norm.cdf(-d2)
        
        return value, delta, gamma, theta, vega, rho
    
    @staticmethod
    def black_scholes(option_type: str, fs: float, x: float, 
                     t: float, r: float, v: float) -> Tuple[float, float, float, float, float, float]:
        """標準Black-Scholesモデル（配当なし株式）.
        
        Args:
            option_type: "c" for call, "p" for put
            fs: スポット価格
            x: 権利行使価格
            t: 満期までの時間（年）
            r: リスクフリーレート
            v: インプライドボラティリティ
            
        Returns:
            (価格, デルタ, ガンマ, シータ, ベガ, ロー)のタプル
        """
        b = r  # 配当なしの場合、b = r
        return BlackScholesReference._gbs(option_type, fs, x, t, r, b, v)
    
    @staticmethod
    def merton(option_type: str, fs: float, x: float, t: float, 
               r: float, q: float, v: float) -> Tuple[float, float, float, float, float, float]:
        """Mertonモデル（連続配当付き株式/インデックス）.
        
        Args:
            option_type: "c" for call, "p" for put
            fs: スポット価格
            x: 権利行使価格
            t: 満期までの時間（年）
            r: リスクフリーレート
            q: 連続配当率
            v: インプライドボラティリティ
            
        Returns:
            (価格, デルタ, ガンマ, シータ, ベガ, ロー)のタプル
        """
        b = r - q  # 配当がある場合、b = r - q
        return BlackScholesReference._gbs(option_type, fs, x, t, r, b, v)
    
    @staticmethod
    def black_76(option_type: str, fs: float, x: float, 
                 t: float, r: float, v: float) -> Tuple[float, float, float, float, float, float]:
        """Black 76モデル（商品先物）.
        
        Args:
            option_type: "c" for call, "p" for put
            fs: フォワード価格
            x: 権利行使価格
            t: 満期までの時間（年）
            r: リスクフリーレート
            v: インプライドボラティリティ
            
        Returns:
            (価格, デルタ, ガンマ, シータ, ベガ, ロー)のタプル
        """
        b = 0  # 先物の場合、b = 0
        return BlackScholesReference._gbs(option_type, fs, x, t, r, b, v)