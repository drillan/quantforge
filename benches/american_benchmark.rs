use criterion::{black_box, criterion_group, criterion_main, Criterion};
use quantforge::models::american::{AmericanModel, AmericanParams};
use quantforge::models::PricingModel;

fn benchmark_american_call_single(c: &mut Criterion) {
    c.bench_function("american_call_single", |b| {
        let params = AmericanParams::new(100.0, 100.0, 0.5, 0.05, 0.02, 0.25).unwrap();
        b.iter(|| {
            black_box(AmericanModel::call_price(&params));
        });
    });
}

fn benchmark_american_put_single(c: &mut Criterion) {
    c.bench_function("american_put_single", |b| {
        let params = AmericanParams::new(100.0, 100.0, 0.5, 0.05, 0.02, 0.25).unwrap();
        b.iter(|| {
            black_box(AmericanModel::put_price(&params));
        });
    });
}

fn benchmark_american_greeks(c: &mut Criterion) {
    c.bench_function("american_greeks", |b| {
        let params = AmericanParams::new(100.0, 100.0, 0.5, 0.05, 0.02, 0.25).unwrap();
        b.iter(|| {
            black_box(AmericanModel::greeks(&params, true));
        });
    });
}

fn benchmark_american_implied_volatility(c: &mut Criterion) {
    c.bench_function("american_implied_volatility", |b| {
        let params = AmericanParams::new(100.0, 100.0, 0.5, 0.05, 0.02, 0.25).unwrap();
        let target_price = 10.0;
        b.iter(|| {
            let _ = black_box(AmericanModel::implied_volatility(
                target_price,
                &params,
                true,
                Some(0.25),
            ));
        });
    });
}

fn benchmark_american_batch_1000(c: &mut Criterion) {
    use quantforge::models::american::call_price_batch;

    c.bench_function("american_call_batch_1000", |b| {
        let spots: Vec<f64> = (1..=1000).map(|i| 50.0 + i as f64 * 0.1).collect();
        b.iter(|| {
            black_box(call_price_batch(&spots, 100.0, 0.5, 0.05, 0.02, 0.25));
        });
    });
}

fn benchmark_american_batch_10000(c: &mut Criterion) {
    use quantforge::models::american::call_price_batch;

    c.bench_function("american_call_batch_10000", |b| {
        let spots: Vec<f64> = (1..=10000).map(|i| 50.0 + i as f64 * 0.01).collect();
        b.iter(|| {
            black_box(call_price_batch(&spots, 100.0, 0.5, 0.05, 0.02, 0.25));
        });
    });
}

criterion_group!(
    benches,
    benchmark_american_call_single,
    benchmark_american_put_single,
    benchmark_american_greeks,
    benchmark_american_implied_volatility,
    benchmark_american_batch_1000,
    benchmark_american_batch_10000
);
criterion_main!(benches);
