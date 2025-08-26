use criterion::{black_box, criterion_group, criterion_main, BenchmarkId, Criterion};
use quantforge::models::black76::{Black76, Black76Params};
use quantforge::models::black_scholes_model::{BlackScholes, BlackScholesParams};
use quantforge::models::merton::{MertonModel, MertonParams};
use quantforge::models::PricingModel;

/// Generate test data for benchmarking
fn generate_spot_prices(size: usize) -> Vec<f64> {
    (0..size)
        .map(|i| 80.0 + 40.0 * (i as f64 / size as f64))
        .collect()
}

/// Benchmark Black-Scholes batch processing
fn bench_black_scholes_batch(c: &mut Criterion) {
    let mut group = c.benchmark_group("black_scholes_batch");

    // Test parameters
    const K: f64 = 100.0;
    const T: f64 = 1.0;
    const R: f64 = 0.05;
    const SIGMA: f64 = 0.2;

    for size in [100, 1000, 10000, 100000].iter() {
        let spots = generate_spot_prices(*size);

        group.bench_with_input(BenchmarkId::new("call_price", size), &spots, |b, spots| {
            b.iter(|| {
                let results = BlackScholes::call_price_batch(
                    black_box(spots),
                    black_box(K),
                    black_box(T),
                    black_box(R),
                    black_box(SIGMA),
                );
                black_box(results)
            })
        });

        group.bench_with_input(BenchmarkId::new("put_price", size), &spots, |b, spots| {
            b.iter(|| {
                let results = BlackScholes::put_price_batch(
                    black_box(spots),
                    black_box(K),
                    black_box(T),
                    black_box(R),
                    black_box(SIGMA),
                );
                black_box(results)
            })
        });
    }

    group.finish();
}

/// Benchmark Black76 batch processing
fn bench_black76_batch(c: &mut Criterion) {
    let mut group = c.benchmark_group("black76_batch");

    const K: f64 = 100.0;
    const T: f64 = 1.0;
    const R: f64 = 0.05;
    const SIGMA: f64 = 0.2;

    for size in [100, 1000, 10000, 100000].iter() {
        let forwards = generate_spot_prices(*size);

        group.bench_with_input(
            BenchmarkId::new("call_price", size),
            &forwards,
            |b, forwards| {
                b.iter(|| {
                    let results: Vec<f64> = forwards
                        .iter()
                        .map(|&f| {
                            let params = Black76Params::new(f, K, T, R, SIGMA);
                            Black76::call_price(&params)
                        })
                        .collect();
                    black_box(results)
                })
            },
        );
    }

    group.finish();
}

/// Benchmark single vs batch processing comparison
fn bench_single_vs_batch(c: &mut Criterion) {
    let mut group = c.benchmark_group("single_vs_batch");

    const SIZE: usize = 10000;
    const K: f64 = 100.0;
    const T: f64 = 1.0;
    const R: f64 = 0.05;
    const SIGMA: f64 = 0.2;

    let spots = generate_spot_prices(SIZE);

    // Benchmark single calls in a loop
    group.bench_function("single_calls", |b| {
        b.iter(|| {
            let results: Vec<f64> = spots
                .iter()
                .map(|&s| {
                    let params = BlackScholesParams {
                        spot: s,
                        strike: K,
                        time: T,
                        rate: R,
                        sigma: SIGMA,
                    };
                    BlackScholes::call_price(&params)
                })
                .collect();
            black_box(results)
        })
    });

    // Benchmark batch processing
    group.bench_function("batch_processing", |b| {
        b.iter(|| {
            let results = BlackScholes::call_price_batch(
                black_box(&spots),
                black_box(K),
                black_box(T),
                black_box(R),
                black_box(SIGMA),
            );
            black_box(results)
        })
    });

    group.finish();
}

/// Benchmark Greeks calculation
fn bench_greeks(c: &mut Criterion) {
    let mut group = c.benchmark_group("greeks");

    const S: f64 = 100.0;
    const K: f64 = 100.0;
    const T: f64 = 1.0;
    const R: f64 = 0.05;
    const SIGMA: f64 = 0.2;

    group.bench_function("black_scholes_greeks", |b| {
        b.iter(|| {
            let params = BlackScholesParams {
                spot: black_box(S),
                strike: black_box(K),
                time: black_box(T),
                rate: black_box(R),
                sigma: black_box(SIGMA),
            };
            let greeks = BlackScholes::greeks(&params, true);
            black_box(greeks)
        })
    });

    group.bench_function("black76_greeks", |b| {
        b.iter(|| {
            let params = Black76Params::new(
                black_box(S),
                black_box(K),
                black_box(T),
                black_box(R),
                black_box(SIGMA),
            );
            let greeks = Black76::greeks(&params, true);
            black_box(greeks)
        })
    });

    group.bench_function("merton_greeks", |b| {
        b.iter(|| {
            let params = MertonParams {
                spot: black_box(S),
                strike: black_box(K),
                time: black_box(T),
                rate: black_box(R),
                div_yield: black_box(0.02),
                sigma: black_box(SIGMA),
            };
            let greeks = MertonModel::greeks(&params, true);
            black_box(greeks)
        })
    });

    group.finish();
}

/// Benchmark implied volatility calculation
fn bench_implied_volatility(c: &mut Criterion) {
    let mut group = c.benchmark_group("implied_volatility");

    const S: f64 = 100.0;
    const K: f64 = 100.0;
    const T: f64 = 1.0;
    const R: f64 = 0.05;
    const TRUE_SIGMA: f64 = 0.2;

    // Calculate true option prices
    let params_bs = BlackScholesParams {
        spot: S,
        strike: K,
        time: T,
        rate: R,
        sigma: TRUE_SIGMA,
    };
    let call_price = BlackScholes::call_price(&params_bs);

    group.bench_function("black_scholes_iv", |b| {
        b.iter(|| {
            let params = BlackScholesParams {
                spot: black_box(S),
                strike: black_box(K),
                time: black_box(T),
                rate: black_box(R),
                sigma: 0.0,
            };
            let iv = BlackScholes::implied_volatility(&params, black_box(call_price), true, None);
            black_box(iv)
        })
    });

    group.finish();
}

criterion_group!(
    benches,
    bench_black_scholes_batch,
    bench_black76_batch,
    bench_single_vs_batch,
    bench_greeks,
    bench_implied_volatility
);
criterion_main!(benches);
