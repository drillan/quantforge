//! Benchmarks for option pricing models

use criterion::{black_box, criterion_group, criterion_main, Criterion};
use quantforge_core::models::{
    american::American, black76::Black76, black_scholes::BlackScholes, merton::Merton,
};
use quantforge_core::traits::OptionModel;

/// Benchmark Black-Scholes model
fn bench_black_scholes(c: &mut Criterion) {
    let model = BlackScholes;

    // Standard parameters
    let s = 100.0;
    let k = 100.0;
    let t = 1.0;
    let r = 0.05;
    let sigma = 0.2;

    let mut group = c.benchmark_group("black_scholes");

    group.bench_function("call_price", |b| {
        b.iter(|| {
            black_box(model.call_price(
                black_box(s),
                black_box(k),
                black_box(t),
                black_box(r),
                black_box(sigma),
            ))
        })
    });

    group.bench_function("put_price", |b| {
        b.iter(|| {
            black_box(model.put_price(
                black_box(s),
                black_box(k),
                black_box(t),
                black_box(r),
                black_box(sigma),
            ))
        })
    });

    group.bench_function("greeks_call", |b| {
        b.iter(|| {
            black_box(model.greeks(
                black_box(s),
                black_box(k),
                black_box(t),
                black_box(r),
                black_box(sigma),
                black_box(true),
            ))
        })
    });

    group.bench_function("greeks_put", |b| {
        b.iter(|| {
            black_box(model.greeks(
                black_box(s),
                black_box(k),
                black_box(t),
                black_box(r),
                black_box(sigma),
                black_box(false),
            ))
        })
    });

    group.bench_function("implied_volatility", |b| {
        let price = 10.45; // Approximate ATM price
        b.iter(|| {
            black_box(model.implied_volatility(
                black_box(price),
                black_box(s),
                black_box(k),
                black_box(t),
                black_box(r),
                black_box(true),
            ))
        })
    });

    group.finish();
}

/// Benchmark Black76 model
fn bench_black76(c: &mut Criterion) {
    let model = Black76;

    // Standard parameters
    let f = 100.0;
    let k = 100.0;
    let t = 1.0;
    let r = 0.05;
    let sigma = 0.2;

    let mut group = c.benchmark_group("black76");

    group.bench_function("call_price", |b| {
        b.iter(|| {
            black_box(model.call_price(
                black_box(f),
                black_box(k),
                black_box(t),
                black_box(r),
                black_box(sigma),
            ))
        })
    });

    group.bench_function("put_price", |b| {
        b.iter(|| {
            black_box(model.put_price(
                black_box(f),
                black_box(k),
                black_box(t),
                black_box(r),
                black_box(sigma),
            ))
        })
    });

    group.bench_function("greeks", |b| {
        b.iter(|| {
            black_box(model.greeks(
                black_box(f),
                black_box(k),
                black_box(t),
                black_box(r),
                black_box(sigma),
                black_box(true),
            ))
        })
    });

    group.finish();
}

/// Benchmark Merton model
fn bench_merton(c: &mut Criterion) {
    // Standard parameters
    let s = 100.0;
    let k = 100.0;
    let t = 1.0;
    let r = 0.05;
    let q = 0.02; // Dividend yield
    let sigma = 0.2;

    let mut group = c.benchmark_group("merton");

    group.bench_function("call_price_with_dividend", |b| {
        b.iter(|| {
            black_box(Merton::call_price_merton(
                black_box(s),
                black_box(k),
                black_box(t),
                black_box(r),
                black_box(q),
                black_box(sigma),
            ))
        })
    });

    group.bench_function("put_price_with_dividend", |b| {
        b.iter(|| {
            black_box(Merton::put_price_merton(
                black_box(s),
                black_box(k),
                black_box(t),
                black_box(r),
                black_box(q),
                black_box(sigma),
            ))
        })
    });

    group.bench_function("greeks_with_dividend", |b| {
        b.iter(|| {
            black_box(Merton::greeks_merton(
                black_box(s),
                black_box(k),
                black_box(t),
                black_box(r),
                black_box(q),
                black_box(sigma),
                black_box(true),
            ))
        })
    });

    // Benchmark trait implementation (no dividend)
    let model = Merton;
    group.bench_function("call_price_no_dividend", |b| {
        b.iter(|| {
            black_box(model.call_price(
                black_box(s),
                black_box(k),
                black_box(t),
                black_box(r),
                black_box(sigma),
            ))
        })
    });

    group.finish();
}

/// Benchmark American model
fn bench_american(c: &mut Criterion) {
    // Standard parameters
    let s = 100.0;
    let k = 100.0;
    let t = 1.0;
    let r = 0.05;
    let q = 0.02; // Dividend yield
    let sigma = 0.2;

    let mut group = c.benchmark_group("american");

    group.bench_function("call_price_with_dividend", |b| {
        b.iter(|| {
            black_box(American::call_price_american(
                black_box(s),
                black_box(k),
                black_box(t),
                black_box(r),
                black_box(q),
                black_box(sigma),
            ))
        })
    });

    group.bench_function("put_price_with_dividend", |b| {
        b.iter(|| {
            black_box(American::put_price_american(
                black_box(s),
                black_box(k),
                black_box(t),
                black_box(r),
                black_box(q),
                black_box(sigma),
            ))
        })
    });

    group.bench_function("greeks_with_dividend", |b| {
        b.iter(|| {
            black_box(American::greeks_american(
                black_box(s),
                black_box(k),
                black_box(t),
                black_box(r),
                black_box(q),
                black_box(sigma),
                black_box(true),
            ))
        })
    });

    // Benchmark early exercise boundary calculation
    use quantforge_core::models::american::boundary::calculate_exercise_boundary;
    use quantforge_core::models::american::pricing::AmericanParams;

    group.bench_function("exercise_boundary_call", |b| {
        let params = AmericanParams {
            s,
            k,
            t,
            r,
            q,
            sigma,
        };
        b.iter(|| black_box(calculate_exercise_boundary(&params, true)))
    });

    group.bench_function("exercise_boundary_put", |b| {
        let params = AmericanParams {
            s,
            k,
            t,
            r,
            q,
            sigma,
        };
        b.iter(|| black_box(calculate_exercise_boundary(&params, false)))
    });

    // Benchmark trait implementation (no dividend)
    let model = American;
    group.bench_function("call_price_no_dividend", |b| {
        b.iter(|| {
            black_box(model.call_price(
                black_box(s),
                black_box(k),
                black_box(t),
                black_box(r),
                black_box(sigma),
            ))
        })
    });

    group.finish();
}

/// Benchmark batch processing
fn bench_batch_processing(c: &mut Criterion) {
    let model = BlackScholes;

    let mut group = c.benchmark_group("batch_processing");

    // Test different batch sizes
    for size in &[100, 1000, 10000] {
        let n = *size;
        let spots: Vec<f64> = (0..n).map(|i| 90.0 + (i as f64) * 0.02).collect();
        let strikes: Vec<f64> = vec![100.0; n];
        let times: Vec<f64> = vec![1.0; n];
        let rates: Vec<f64> = vec![0.05; n];
        let sigmas: Vec<f64> = vec![0.2; n];

        group.bench_function(format!("sequential_{n}"), |b| {
            b.iter(|| {
                for i in 0..n {
                    let _ = black_box(
                        model.call_price(spots[i], strikes[i], times[i], rates[i], sigmas[i]),
                    );
                }
            })
        });

        group.bench_function(format!("parallel_{n}"), |b| {
            b.iter(|| black_box(model.call_price_batch(&spots, &strikes, &times, &rates, &sigmas)))
        });
    }

    group.finish();
}

criterion_group!(
    benches,
    bench_black_scholes,
    bench_black76,
    bench_merton,
    bench_american,
    bench_batch_processing
);
criterion_main!(benches);
