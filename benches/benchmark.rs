use criterion::{black_box, criterion_group, criterion_main, BenchmarkId, Criterion, Throughput};

// 公開されている関数を直接使用するためのパス
use quantforge::models::black_scholes::{bs_call_price, bs_call_price_batch};

fn bench_black_scholes_single(c: &mut Criterion) {
    let mut group = c.benchmark_group("black_scholes_single");

    // ATM (At-The-Money) オプション
    group.bench_function("atm", |b| {
        b.iter(|| {
            bs_call_price(
                black_box(100.0), // S
                black_box(100.0), // K
                black_box(1.0),   // T
                black_box(0.05),  // r
                black_box(0.2),   // v
            )
        });
    });

    // ITM (In-The-Money) オプション
    group.bench_function("itm", |b| {
        b.iter(|| {
            bs_call_price(
                black_box(110.0),
                black_box(100.0),
                black_box(1.0),
                black_box(0.05),
                black_box(0.2),
            )
        });
    });

    // OTM (Out-of-The-Money) オプション
    group.bench_function("otm", |b| {
        b.iter(|| {
            bs_call_price(
                black_box(90.0),
                black_box(100.0),
                black_box(1.0),
                black_box(0.05),
                black_box(0.2),
            )
        });
    });

    group.finish();
}

fn bench_black_scholes_batch(c: &mut Criterion) {
    let mut group = c.benchmark_group("black_scholes_batch");

    let sizes = vec![100, 1000, 10000, 100000, 1000000];

    for size in sizes {
        group.throughput(Throughput::Elements(size as u64));
        group.bench_with_input(
            BenchmarkId::from_parameter(format!("{size}_spots")),
            &size,
            |b, &size| {
                let spots: Vec<f64> = (0..size)
                    .map(|i| 80.0 + (i as f64 / size as f64) * 40.0)
                    .collect();
                b.iter(|| {
                    bs_call_price_batch(
                        black_box(&spots),
                        black_box(100.0),
                        black_box(1.0),
                        black_box(0.05),
                        black_box(0.2),
                    )
                });
            },
        );
    }

    group.finish();
}

fn bench_comparison(c: &mut Criterion) {
    let mut group = c.benchmark_group("comparison");

    // 単一計算 vs バッチ（1要素）の比較
    group.bench_function("single_call", |b| {
        b.iter(|| {
            bs_call_price(
                black_box(100.0),
                black_box(100.0),
                black_box(1.0),
                black_box(0.05),
                black_box(0.2),
            )
        });
    });

    group.bench_function("batch_1_element", |b| {
        let spots = vec![100.0];
        b.iter(|| {
            bs_call_price_batch(
                black_box(&spots),
                black_box(100.0),
                black_box(1.0),
                black_box(0.05),
                black_box(0.2),
            )
        });
    });

    group.finish();
}

criterion_group!(
    benches,
    bench_black_scholes_single,
    bench_black_scholes_batch,
    bench_comparison
);
criterion_main!(benches);
