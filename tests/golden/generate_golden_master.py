"""ゴールデンマスター参照値生成スクリプト.

使用方法:
    初回生成: pytest tests/golden/generate_golden_master.py --generate-golden
    再生成: pytest tests/golden/generate_golden_master.py --regenerate-golden
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any

import pytest
from gbs_reference.models import BlackScholesReference  # type: ignore[import-not-found]


class GoldenMasterGenerator:
    """ゴールデンマスター参照値生成クラス."""

    def __init__(self) -> None:
        """初期化."""
        self.output_dir = Path(__file__).parent
        self.flag_file = self.output_dir / ".golden_generated"
        self.output_file = self.output_dir / "golden_values.json"
        self.reference = BlackScholesReference()

    def is_generated(self) -> bool:
        """生成済みフラグをチェック."""
        return self.flag_file.exists()

    def create_flag(self) -> None:
        """生成済みフラグを作成."""
        self.flag_file.touch()

    def _create_test_case(
        self,
        test_id: str,
        category: str,
        description: str,
        s: float,
        k: float,
        t: float,
        r: float,
        v: float,
        q: float | None = None,
    ) -> dict[str, Any]:
        """単一のテストケースを生成.

        Args:
            test_id: テストケースID
            category: カテゴリ（black_scholes, merton, black_76）
            description: 説明
            s: スポット/フォワード価格
            k: 権利行使価格
            t: 満期までの時間
            r: リスクフリーレート
            v: ボラティリティ
            q: 配当率（Mertonモデルの場合）

        Returns:
            テストケース辞書
        """
        # 計算実行
        if category == "black_scholes":
            call_result = self.reference.black_scholes("c", s, k, t, r, v)
            put_result = self.reference.black_scholes("p", s, k, t, r, v)
        elif category == "merton" and q is not None:
            call_result = self.reference.merton("c", s, k, t, r, q, v)
            put_result = self.reference.merton("p", s, k, t, r, q, v)
        elif category == "black_76":
            call_result = self.reference.black_76("c", s, k, t, r, v)
            put_result = self.reference.black_76("p", s, k, t, r, v)
        else:
            raise ValueError(f"Unknown category: {category}")

        # モネネス計算
        moneyness = s / k

        # 結果を構造化
        test_case = {
            "id": test_id,
            "category": category,
            "description": description,
            "inputs": {"s": s, "k": k, "t": t, "r": r, "v": v},
            "outputs": {
                "call_price": call_result[0],
                "call_delta": call_result[1],
                "call_gamma": call_result[2],
                "call_theta": call_result[3],
                "call_vega": call_result[4],
                "call_rho": call_result[5],
                "put_price": put_result[0],
                "put_delta": put_result[1],
                "put_gamma": put_result[2],
                "put_theta": put_result[3],
                "put_vega": put_result[4],
                "put_rho": put_result[5],
            },
            "metadata": {"moneyness": moneyness, "moneyness_category": self._categorize_moneyness(moneyness)},
        }

        if q is not None:
            inputs = test_case["inputs"]
            assert isinstance(inputs, dict)
            inputs["q"] = q

        return test_case

    def _categorize_moneyness(self, moneyness: float) -> str:
        """モネネスのカテゴリ分類."""
        if moneyness < 0.95:
            return "OTM"  # Out of the money
        elif moneyness <= 1.05:
            return "ATM"  # At the money
        else:
            return "ITM"  # In the money

    def generate_test_cases(self) -> list[dict[str, Any]]:
        """包括的なテストケースを生成."""
        test_cases = []
        case_id = 0

        # 基本パラメータセット
        base_s = 100.0

        # 1. ATM/ITM/OTMケース（モネネス別）
        moneyness_levels = [0.8, 0.9, 1.0, 1.1, 1.2]  # OTM, slight OTM, ATM, slight ITM, ITM
        maturities = [0.01, 0.1, 0.25, 0.5, 1.0, 2.0]  # 様々な満期
        volatilities = [0.05, 0.1, 0.2, 0.3, 0.5]  # 低〜高ボラティリティ
        # rates = [-0.01, 0.0, 0.02, 0.05, 0.1]  # 負金利含む（現在未使用）

        # Black-Scholesモデルのテストケース
        for moneyness in moneyness_levels:
            k = base_s / moneyness
            for t in maturities:
                for v in volatilities:
                    # 代表的な金利でのみテスト（組み合わせ爆発を防ぐ）
                    r = 0.05
                    case_id += 1
                    test_cases.append(
                        self._create_test_case(
                            test_id=f"BS_{case_id:03d}",
                            category="black_scholes",
                            description=f"Moneyness={moneyness:.1f}, T={t:.2f}Y, Vol={v:.0%}",
                            s=base_s,
                            k=k,
                            t=t,
                            r=r,
                            v=v,
                        )
                    )

        # 2. エッジケース
        edge_cases: list[dict[str, Any]] = [
            # Deep ITM
            {"s": 200.0, "k": 100.0, "t": 1.0, "r": 0.05, "v": 0.2, "desc": "Deep ITM"},
            # Deep OTM
            {"s": 50.0, "k": 100.0, "t": 1.0, "r": 0.05, "v": 0.2, "desc": "Deep OTM"},
            # 満期直前
            {"s": 100.0, "k": 100.0, "t": 0.001, "r": 0.05, "v": 0.2, "desc": "Near expiry"},
            # 高ボラティリティ
            {"s": 100.0, "k": 100.0, "t": 1.0, "r": 0.05, "v": 1.0, "desc": "High volatility"},
            # 負金利
            {"s": 100.0, "k": 100.0, "t": 1.0, "r": -0.02, "v": 0.2, "desc": "Negative rate"},
        ]

        for edge in edge_cases:
            case_id += 1
            test_cases.append(
                self._create_test_case(
                    test_id=f"BS_EDGE_{case_id:03d}",
                    category="black_scholes",
                    description=str(edge["desc"]),
                    s=float(edge["s"]),
                    k=float(edge["k"]),
                    t=float(edge["t"]),
                    r=float(edge["r"]),
                    v=float(edge["v"]),
                )
            )

        # 3. 重要な参照値（既存テストとの整合性確認用）
        reference_cases: list[dict[str, Any]] = [
            # Rustテストで使用されている値
            {"s": 100.0, "k": 100.0, "t": 1.0, "r": 0.05, "v": 0.2, "desc": "Reference ATM (used in Rust tests)"},
            {"s": 90.0, "k": 100.0, "t": 1.0, "r": 0.05, "v": 0.2, "desc": "Reference OTM"},
            {"s": 110.0, "k": 100.0, "t": 1.0, "r": 0.05, "v": 0.2, "desc": "Reference ITM"},
        ]

        for ref in reference_cases:
            case_id += 1
            test_cases.append(
                self._create_test_case(
                    test_id=f"BS_REF_{case_id:03d}",
                    category="black_scholes",
                    description=str(ref["desc"]),
                    s=float(ref["s"]),
                    k=float(ref["k"]),
                    t=float(ref["t"]),
                    r=float(ref["r"]),
                    v=float(ref["v"]),
                )
            )

        return test_cases

    def generate_golden_values(self) -> dict[str, Any]:
        """ゴールデンマスター値を生成."""
        test_cases = self.generate_test_cases()

        golden_data = {
            "version": "1.0.0",
            "generated_at": datetime.utcnow().isoformat() + "Z",
            "source": "GBS_2025.py (MIT License) - Davis William Edwards",
            "description": "Golden master reference values for QuantForge option pricing tests",
            "test_cases": test_cases,
            "tolerance": 1e-3,
            "total_cases": len(test_cases),
            "categories": {
                "black_scholes": len([tc for tc in test_cases if tc["category"] == "black_scholes"]),
                "merton": len([tc for tc in test_cases if tc["category"] == "merton"]),
                "black_76": len([tc for tc in test_cases if tc["category"] == "black_76"]),
            },
        }

        return golden_data

    def save_golden_values(self, golden_data: dict[str, Any]) -> None:
        """ゴールデンマスター値をJSONファイルに保存."""
        with open(self.output_file, "w", encoding="utf-8") as f:
            json.dump(golden_data, f, indent=2, ensure_ascii=False)
        print(f"✅ Golden values saved to {self.output_file}")

        # 統計情報を表示
        print(f"📊 Generated {golden_data['total_cases']} test cases:")
        for category, count in golden_data["categories"].items():
            if count > 0:
                print(f"   - {category}: {count} cases")

    def run(self, force_regenerate: bool = False) -> None:
        """ゴールデンマスター生成を実行.

        Args:
            force_regenerate: 強制再生成フラグ
        """
        if self.is_generated() and not force_regenerate:
            print("⚠️  Golden values already generated. Use --regenerate-golden to force regeneration.")
            return

        print("🔧 Generating golden master values...")
        golden_data = self.generate_golden_values()
        self.save_golden_values(golden_data)
        self.create_flag()
        print("✅ Golden master generation complete!")


# pytestフック
def pytest_addoption(parser: Any) -> None:
    """pytestコマンドラインオプションを追加."""
    parser.addoption("--generate-golden", action="store_true", default=False, help="Generate golden master values")
    parser.addoption(
        "--regenerate-golden", action="store_true", default=False, help="Force regenerate golden master values"
    )


def test_generate_golden_master(request: Any) -> None:
    """ゴールデンマスター生成テスト."""
    generate_flag = request.config.getoption("--generate-golden")
    regenerate_flag = request.config.getoption("--regenerate-golden")

    if not generate_flag and not regenerate_flag:
        pytest.skip("Golden master generation skipped. Use --generate-golden or --regenerate-golden to run.")

    generator = GoldenMasterGenerator()
    generator.run(force_regenerate=regenerate_flag)

    # 生成されたファイルの検証
    assert generator.output_file.exists(), "Golden values file was not created"

    # JSONファイルの妥当性チェック
    with open(generator.output_file) as f:
        data = json.load(f)

    assert data["version"] == "1.0.0"
    assert data["total_cases"] > 50  # 最低50ケース以上
    assert "test_cases" in data
    assert len(data["test_cases"]) == data["total_cases"]

    # 参照値の妥当性チェック（ATMケースの既知の値）
    for case in data["test_cases"]:
        if case["description"] == "Reference ATM (used in Rust tests)":
            # 既知の値との比較
            expected_call = 10.450583572185565
            actual_call = case["outputs"]["call_price"]
            assert abs(actual_call - expected_call) < 1e-3, (
                f"Call price mismatch: expected {expected_call}, got {actual_call}"
            )
            break
    else:
        pytest.fail("Reference ATM test case not found")

    print("✅ All validation checks passed!")


if __name__ == "__main__":
    # 直接実行時の処理
    import sys

    if len(sys.argv) > 1 and sys.argv[1] in ["--generate", "--regenerate"]:
        generator = GoldenMasterGenerator()
        generator.run(force_regenerate=(sys.argv[1] == "--regenerate"))
    else:
        print("Usage:")
        print("  python generate_golden_master.py --generate     # Initial generation")
        print("  python generate_golden_master.py --regenerate   # Force regeneration")
        print()
        print("Or use pytest:")
        print("  pytest generate_golden_master.py --generate-golden")
        print("  pytest generate_golden_master.py --regenerate-golden")
