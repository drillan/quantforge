use quantforge_core::market_utils::*;

#[cfg(test)]
mod tests {
    use super::*;
    use approx::assert_relative_eq;

    mod mid_price_tests {
        use super::*;

        #[test]
        fn test_simple_mid_price() {
            let mid = mid_price(100.0, 100.2);
            assert_relative_eq!(mid, 100.1, epsilon = 1e-10);
        }

        #[test]
        fn test_mid_price_with_zero_bid() {
            // Zero bid with default config (50% threshold) - spread is 200%
            let mid = mid_price(0.0, 100.0);
            assert!(mid.is_nan()); // Exceeds default 50% threshold

            // With no threshold, zero is valid in options market
            let config_no_limit = MarketPricingConfig {
                max_spread_pct: None,
                ..Default::default()
            };
            let mid = mid_price_with_config(0.0, 100.0, &config_no_limit);
            assert_relative_eq!(mid, 50.0, epsilon = 1e-10);
        }

        #[test]
        fn test_mid_price_with_negative_values() {
            // Negative prices should return NaN
            assert!(mid_price(-100.0, 100.0).is_nan());
            assert!(mid_price(100.0, -100.0).is_nan());
            assert!(mid_price(-100.0, -100.0).is_nan());
        }

        #[test]
        fn test_mid_price_with_nan() {
            // NaN should propagate
            assert!(mid_price(f64::NAN, 100.0).is_nan());
            assert!(mid_price(100.0, f64::NAN).is_nan());
            assert!(mid_price(f64::NAN, f64::NAN).is_nan());
        }

        #[test]
        fn test_mid_price_with_infinity() {
            // Infinity should return NaN
            assert!(mid_price(f64::INFINITY, 100.0).is_nan());
            assert!(mid_price(100.0, f64::INFINITY).is_nan());
            assert!(mid_price(f64::NEG_INFINITY, 100.0).is_nan());
        }

        #[test]
        fn test_crossed_spread_default() {
            // Default config should return NaN for crossed spread
            let mid = mid_price(105.0, 100.0);
            assert!(mid.is_nan());
        }
    }

    mod mid_price_with_config_tests {
        use super::*;

        #[test]
        fn test_extreme_option_spread() {
            let config = MarketPricingConfig::default();

            // Deep OTM option: bid=1, ask=1000
            let mid = mid_price_with_config(1.0, 1000.0, &config);
            assert!(mid.is_nan()); // Default 50% threshold exceeded

            // No threshold
            let config_no_limit = MarketPricingConfig {
                max_spread_pct: None,
                ..Default::default()
            };
            let mid = mid_price_with_config(1.0, 1000.0, &config_no_limit);
            assert_relative_eq!(mid, 500.5, epsilon = 1e-10);

            // bid=0 case (actual options market) - spread is 200% so exceeds 50% default
            let mid = mid_price_with_config(0.0, 100.0, &config);
            assert!(mid.is_nan()); // Exceeds 50% threshold (200% spread)

            // bid=0 with no threshold should work
            let mid = mid_price_with_config(0.0, 100.0, &config_no_limit);
            assert_relative_eq!(mid, 50.0, epsilon = 1e-10); // 0 is a valid price
        }

        #[test]
        fn test_abnormal_spread_handling() {
            // Return NaN
            let config_nan = MarketPricingConfig {
                max_spread_pct: Some(0.1), // 10% threshold
                abnormal_handling: AbnormalSpreadHandling::ReturnNaN,
                ..Default::default()
            };
            let mid = mid_price_with_config(100.0, 120.0, &config_nan);
            assert!(mid.is_nan());

            // Log and continue
            let config_continue = MarketPricingConfig {
                max_spread_pct: Some(0.1),
                abnormal_handling: AbnormalSpreadHandling::LogAndContinue,
                ..Default::default()
            };
            let mid = mid_price_with_config(100.0, 120.0, &config_continue);
            assert_relative_eq!(mid, 110.0, epsilon = 1e-10);
        }

        #[test]
        fn test_crossed_spread_handling() {
            // Return NaN
            let config_nan = MarketPricingConfig {
                crossed_handling: CrossedSpreadHandling::ReturnNaN,
                ..Default::default()
            };
            let mid = mid_price_with_config(105.0, 100.0, &config_nan);
            assert!(mid.is_nan());

            // Swap and continue
            let config_swap = MarketPricingConfig {
                crossed_handling: CrossedSpreadHandling::SwapAndContinue,
                ..Default::default()
            };
            let mid = mid_price_with_config(105.0, 100.0, &config_swap);
            assert_relative_eq!(mid, 102.5, epsilon = 1e-10);
        }

        #[test]
        fn test_spread_threshold_boundary() {
            let config = MarketPricingConfig {
                max_spread_pct: Some(0.1), // Exactly 10%
                ..Default::default()
            };

            // Just under threshold: (110 - 100) / 105 = 10/105 ≈ 0.0952 < 10%
            let mid = mid_price_with_config(100.0, 110.0, &config);
            assert!(mid.is_finite());

            // Just over threshold: (111.2 - 100) / 105.6 = 11.2/105.6 ≈ 0.106 > 10%
            let mid = mid_price_with_config(100.0, 111.2, &config);
            assert!(mid.is_nan());
        }
    }

    mod weighted_mid_price_tests {
        use super::*;

        #[test]
        fn test_weighted_mid_equal_quantities() {
            // Equal quantities should give simple mid
            let weighted = weighted_mid_price(100.0, Some(1000.0), 100.2, Some(1000.0));
            assert_relative_eq!(weighted, 100.1, epsilon = 1e-10);
        }

        #[test]
        fn test_weighted_mid_different_quantities() {
            // Heavy bid side
            let weighted = weighted_mid_price(100.0, Some(2000.0), 100.2, Some(1000.0));
            let expected = (100.0 * 1000.0 + 100.2 * 2000.0) / 3000.0;
            assert_relative_eq!(weighted, expected, epsilon = 1e-10);
        }

        #[test]
        fn test_weighted_mid_zero_quantity() {
            // Zero quantity should fall back to simple mid
            let weighted = weighted_mid_price(100.0, Some(0.0), 100.2, Some(1000.0));
            assert_relative_eq!(weighted, 100.1, epsilon = 1e-10);

            let weighted = weighted_mid_price(100.0, Some(1000.0), 100.2, Some(0.0));
            assert_relative_eq!(weighted, 100.1, epsilon = 1e-10);
        }

        #[test]
        fn test_weighted_mid_missing_quantities() {
            // None quantities should fall back to simple mid
            let weighted = weighted_mid_price(100.0, None, 100.2, None);
            assert_relative_eq!(weighted, 100.1, epsilon = 1e-10);

            let weighted = weighted_mid_price(100.0, Some(1000.0), 100.2, None);
            assert_relative_eq!(weighted, 100.1, epsilon = 1e-10);
        }

        #[test]
        fn test_weighted_mid_with_extreme_spread() {
            let config = MarketPricingConfig::default();

            // Should check spread first
            let weighted =
                weighted_mid_price_with_config(1.0, Some(1000.0), 1000.0, Some(1000.0), &config);
            assert!(weighted.is_nan()); // Spread check fails
        }
    }

    mod spread_tests {
        use super::*;

        #[test]
        fn test_spread_absolute() {
            assert_relative_eq!(spread(100.0, 100.2), 0.2, epsilon = 1e-10);
            assert_relative_eq!(spread(99.8, 100.2), 0.4, epsilon = 1e-10);
        }

        #[test]
        fn test_spread_percentage() {
            // Note: spread_pct = (ask - bid) / mid, so 0.2 / 100.1 ≈ 0.001998...
            assert_relative_eq!(spread_pct(100.0, 100.2), 0.001998, epsilon = 1e-5); // ~0.2%
            assert_relative_eq!(spread_pct(99.0, 101.0), 0.02, epsilon = 1e-10);
            // 2%
        }

        #[test]
        fn test_spread_with_crossed() {
            // Negative spread for crossed market
            assert_relative_eq!(spread(105.0, 100.0), -5.0, epsilon = 1e-10);
            // Percentage undefined for crossed spread
            assert!(spread_pct(105.0, 100.0).is_nan());
        }

        #[test]
        fn test_spread_with_zero() {
            assert_relative_eq!(spread(0.0, 100.0), 100.0, epsilon = 1e-10);
            // Percentage with zero mid is undefined
            let pct = spread_pct(0.0, 0.0);
            assert!(pct.is_nan());
        }
    }

    mod property_tests {
        use super::*;

        #[test]
        fn property_mid_price_is_between_bid_ask_when_valid() {
            // When spread is normal: bid <= mid <= ask
            let bid = 100.0;
            let ask = 100.2;
            let mid = mid_price(bid, ask);
            assert!(mid >= bid);
            assert!(mid <= ask);
        }

        #[test]
        fn property_nan_propagation() {
            // NaN input should always produce NaN output
            assert!(mid_price(f64::NAN, 100.0).is_nan());
            assert!(mid_price(100.0, f64::NAN).is_nan());
            assert!(weighted_mid_price(f64::NAN, Some(100.0), 100.0, Some(100.0)).is_nan());
        }

        #[test]
        fn property_weighted_mid_bounds() {
            // Weighted mid should also be between bid and ask
            let bid = 100.0;
            let ask = 100.2;
            let weighted = weighted_mid_price(bid, Some(1500.0), ask, Some(1000.0));
            assert!(weighted >= bid);
            assert!(weighted <= ask);
        }

        #[test]
        fn property_spread_non_negative_for_normal_market() {
            // For normal market (ask >= bid), spread is non-negative
            let bid = 100.0;
            let ask = 100.2;
            assert!(spread(bid, ask) >= 0.0);
            assert!(spread_pct(bid, ask) >= 0.0);
        }
    }

    mod extreme_cases {
        use super::*;

        #[test]
        fn test_option_market_extremes() {
            let config = MarketPricingConfig::default();

            // Real examples from options market
            struct TestCase {
                bid: f64,
                ask: f64,
                description: &'static str,
            }

            let cases = vec![
                TestCase {
                    bid: 1.0,
                    ask: 1000.0,
                    description: "Deep OTM",
                },
                TestCase {
                    bid: 0.0,
                    ask: 100.0,
                    description: "No bid",
                },
                TestCase {
                    bid: 5000.0,
                    ask: 5001.0,
                    description: "Deep ITM",
                },
                TestCase {
                    bid: 100.0,
                    ask: 100.0,
                    description: "Locked market",
                },
            ];

            for case in cases {
                let mid = mid_price_with_config(case.bid, case.ask, &config);
                println!(
                    "{}: bid={}, ask={}, mid={:?}",
                    case.description, case.bid, case.ask, mid
                );

                if case.bid == case.ask {
                    assert_relative_eq!(mid, case.bid, epsilon = 1e-10);
                }
            }
        }

        #[test]
        fn test_numerical_precision() {
            // Very small differences
            let bid = 100.0;
            let ask = 100.0 + f64::EPSILON;
            let mid = mid_price(bid, ask);
            assert!(mid.is_finite());

            // Very large values
            let bid = 1e15;
            let ask = 1e15 + 1.0;
            let mid = mid_price(bid, ask);
            assert_relative_eq!(mid, 1e15 + 0.5, epsilon = 1e-10);
        }

        #[test]
        fn test_zero_spread() {
            // Locked market (bid == ask)
            let mid = mid_price(100.0, 100.0);
            assert_relative_eq!(mid, 100.0, epsilon = 1e-10);

            let s = spread(100.0, 100.0);
            assert_relative_eq!(s, 0.0, epsilon = 1e-10);

            let pct = spread_pct(100.0, 100.0);
            assert_relative_eq!(pct, 0.0, epsilon = 1e-10);
        }
    }
}
