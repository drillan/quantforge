"""ゴールデンマスターテスト.

GBS_2025.pyから生成された参照値を使用してRust実装の正確性を検証します。
"""

import json
from pathlib import Path
from typing import Any

import numpy as np
import pytest


class TestGoldenMaster:
    """ゴールデンマスター参照値テスト."""

    @pytest.fixture(scope="class")
    def golden_data(self) -> dict[str, Any]:
        """参照値データをロード."""
        golden_file = Path(__file__).parent / "golden" / "golden_values.json"

        if not golden_file.exists():
            pytest.skip(
                "Golden values not generated. Run: pytest tests/golden/generate_golden_master.py --generate-golden"
            )

        with open(golden_file, encoding="utf-8") as f:
            data = json.load(f)
            assert isinstance(data, dict)
            return data

    def test_golden_values_exist(self, golden_data: dict[str, Any]) -> None:
        """参照値ファイルの存在と基本構造を確認."""
        assert golden_data["version"] == "1.0.0"
        assert "test_cases" in golden_data
        assert golden_data["total_cases"] > 50
        assert golden_data["tolerance"] == 1e-10

    def test_reference_atm_value(self, golden_data: dict[str, Any]) -> None:
        """既知のATM参照値との一致を確認."""
        from quantforge import calculate_call_price

        # Rustテストで使用されている参照値を探す
        for case in golden_data["test_cases"]:
            if "Reference ATM" in case["description"]:
                inputs = case["inputs"]
                expected_call = case["outputs"]["call_price"]

                # Rust実装を呼び出し
                actual_call = calculate_call_price(
                    s=inputs["s"], k=inputs["k"], t=inputs["t"], r=inputs["r"], v=inputs["v"]
                )

                # 許容誤差内での一致を確認
                tolerance = golden_data["tolerance"]
                assert abs(actual_call - expected_call) < tolerance, (
                    f"Call price mismatch: expected {expected_call}, got {actual_call}, "
                    f"diff={abs(actual_call - expected_call)}"
                )

                # 既知の値との一致も確認（二重チェック）
                known_value = 10.450583572185565
                assert abs(expected_call - known_value) < 1e-10, (
                    f"Golden value doesn't match known reference: {expected_call} vs {known_value}"
                )
                break
        else:
            pytest.fail("Reference ATM test case not found in golden values")

    def test_black_scholes_call_prices(self, golden_data: dict[str, Any]) -> None:
        """Black-Scholesコールオプション価格の検証."""
        from quantforge import calculate_call_price

        tolerance = golden_data["tolerance"]
        errors = []

        # 各テストケースを検証
        for case in golden_data["test_cases"]:
            if case["category"] != "black_scholes":
                continue

            inputs = case["inputs"]
            expected = case["outputs"]["call_price"]

            try:
                actual = calculate_call_price(s=inputs["s"], k=inputs["k"], t=inputs["t"], r=inputs["r"], v=inputs["v"])

                error = abs(actual - expected)
                if error >= tolerance:
                    errors.append(
                        {
                            "id": case["id"],
                            "description": case["description"],
                            "expected": expected,
                            "actual": actual,
                            "error": error,
                            "inputs": inputs,
                        }
                    )

            except Exception as e:
                errors.append(
                    {"id": case["id"], "description": case["description"], "exception": str(e), "inputs": inputs}
                )

        if errors:
            # エラーサマリーを表示
            print(f"\n❌ {len(errors)} test cases failed:")
            for err in errors[:5]:  # 最初の5件のみ表示
                if "exception" in err:
                    print(f"  - {err['id']}: {err['exception']}")
                else:
                    print(
                        f"  - {err['id']}: error={err['error']:.2e}, expected={err['expected']:.6f}, "
                        f"actual={err['actual']:.6f}"
                    )

            if len(errors) > 5:
                print(f"  ... and {len(errors) - 5} more")

            pytest.fail(f"{len(errors)} out of {len(golden_data['test_cases'])} test cases failed")

    def test_price_bounds(self, golden_data: dict[str, Any]) -> None:
        """価格境界条件の検証: max(S - K*e^(-rt), 0) <= C <= S."""
        from quantforge import calculate_call_price

        violations = []

        for case in golden_data["test_cases"]:
            if case["category"] != "black_scholes":
                continue

            inputs = case["inputs"]
            s = inputs["s"]
            k = inputs["k"]
            t = inputs["t"]
            r = inputs["r"]
            v = inputs["v"]

            # 価格計算
            call_price = calculate_call_price(s, k, t, r, v)

            # 境界条件
            intrinsic_value = max(s - k * np.exp(-r * t), 0)
            upper_bound = s

            # 検証
            if not (intrinsic_value <= call_price <= upper_bound):
                violations.append(
                    {
                        "id": case["id"],
                        "price": call_price,
                        "intrinsic": intrinsic_value,
                        "upper": upper_bound,
                        "inputs": inputs,
                    }
                )

        if violations:
            print(f"\n❌ {len(violations)} boundary violations found:")
            for v in violations[:3]:
                print(f"  - {v['id']}: price={v['price']:.4f} not in [{v['intrinsic']:.4f}, {v['upper']:.4f}]")
            pytest.fail(f"{len(violations)} price boundary violations")

    def test_moneyness_relationships(self, golden_data: dict[str, Any]) -> None:
        """モネネスによる価格関係の検証: OTM < ATM < ITM."""
        from quantforge import calculate_call_price

        # モネネスカテゴリ別にグループ化
        by_moneyness: dict[str, list[dict[str, Any]]] = {"OTM": [], "ATM": [], "ITM": []}

        for case in golden_data["test_cases"]:
            if case["category"] != "black_scholes":
                continue

            moneyness_cat = case["metadata"]["moneyness_category"]
            if moneyness_cat in by_moneyness:
                inputs = case["inputs"]
                price = calculate_call_price(s=inputs["s"], k=inputs["k"], t=inputs["t"], r=inputs["r"], v=inputs["v"])
                by_moneyness[moneyness_cat].append(
                    {"price": price, "moneyness": case["metadata"]["moneyness"], "id": case["id"]}
                )

        # 平均価格を計算
        avg_prices = {}
        for cat, prices in by_moneyness.items():
            if prices:
                avg_prices[cat] = np.mean([p["price"] for p in prices])

        # 関係性を検証
        if "OTM" in avg_prices and "ATM" in avg_prices and "ITM" in avg_prices:
            assert avg_prices["OTM"] < avg_prices["ATM"], (
                f"OTM avg ({avg_prices['OTM']:.4f}) should be < ATM avg ({avg_prices['ATM']:.4f})"
            )
            assert avg_prices["ATM"] < avg_prices["ITM"], (
                f"ATM avg ({avg_prices['ATM']:.4f}) should be < ITM avg ({avg_prices['ITM']:.4f})"
            )

    def test_edge_cases(self, golden_data: dict[str, Any]) -> None:
        """エッジケースの検証（Deep ITM/OTM、満期直前など）."""
        from quantforge import calculate_call_price

        edge_cases_tested = 0

        for case in golden_data["test_cases"]:
            if "EDGE" not in case["id"]:
                continue

            inputs = case["inputs"]
            expected = case["outputs"]["call_price"]

            actual = calculate_call_price(s=inputs["s"], k=inputs["k"], t=inputs["t"], r=inputs["r"], v=inputs["v"])

            tolerance = golden_data["tolerance"]
            assert abs(actual - expected) < tolerance, (
                f"Edge case {case['description']} failed: expected {expected:.10f}, got {actual:.10f}"
            )

            edge_cases_tested += 1

        assert edge_cases_tested > 0, "No edge cases found in golden values"
        print(f"✅ {edge_cases_tested} edge cases validated")

    def test_batch_consistency(self, golden_data: dict[str, Any]) -> None:
        """バッチ処理と単一処理の一致性を検証."""
        from quantforge import calculate_call_price, calculate_call_price_batch

        # テスト用のサンプルを選択
        test_cases = [c for c in golden_data["test_cases"] if c["category"] == "black_scholes"][:10]

        if not test_cases:
            pytest.skip("No test cases available")

        # 入力配列を準備
        spots = np.array([c["inputs"]["s"] for c in test_cases], dtype=np.float64)
        k = test_cases[0]["inputs"]["k"]  # 同じ権利行使価格を使用
        t = test_cases[0]["inputs"]["t"]
        r = test_cases[0]["inputs"]["r"]
        v = test_cases[0]["inputs"]["v"]

        # バッチ処理
        batch_results = calculate_call_price_batch(spots, k, t, r, v)

        # 個別処理と比較
        for i, spot in enumerate(spots):
            single_result = calculate_call_price(spot, k, t, r, v)
            assert abs(batch_results[i] - single_result) < 1e-10, (
                f"Batch and single results differ at index {i}: {batch_results[i]} vs {single_result}"
            )


@pytest.mark.parametrize(
    "s,k,expected_category",
    [
        (80.0, 100.0, "OTM"),
        (100.0, 100.0, "ATM"),
        (120.0, 100.0, "ITM"),
    ],
)
def test_moneyness_categorization(s: float, k: float, expected_category: str) -> None:
    """モネネスカテゴリ分類のユニットテスト."""
    moneyness = s / k

    if moneyness < 0.95:
        category = "OTM"
    elif moneyness <= 1.05:
        category = "ATM"
    else:
        category = "ITM"

    assert category == expected_category, (
        f"Moneyness {moneyness:.2f} should be categorized as {expected_category}, got {category}"
    )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
