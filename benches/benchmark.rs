use criterion::{black_box, criterion_group, criterion_main, BenchmarkId, Criterion, Throughput};

// 公開されている関数を直接使用するためのパス
use quantforge::models::black_scholes::{bs_call_price, bs_call_price_batch};

// 共通パラメータモジュール
mod common;
use common::test_params::{atm_params, generate_spot_range, itm_params, otm_params};

fn bench_black_scholes_single(c: &mut Criterion) {
    let mut group = c.benchmark_group("black_scholes_single");

    // パラメータ化されたテストケース
    let test_cases = vec![
        ("atm", atm_params(100.0)),
        ("itm", itm_params(0.1)), // 10% ITM
        ("otm", otm_params(0.1)), // 10% OTM
    ];

    for (name, params) in test_cases {
        group.bench_function(name, |b| {
            let (s, k, t, r, v) = params;
            b.iter(|| {
                bs_call_price(
                    black_box(s),
                    black_box(k),
                    black_box(t),
                    black_box(r),
                    black_box(v),
                )
            });
        });
    }

    group.finish();
}

fn bench_black_scholes_batch(c: &mut Criterion) {
    let mut group = c.benchmark_group("black_scholes_batch");

    let sizes = vec![100, 1000, 10000, 100000, 1000000];

    // 共通パラメータ使用
    let (_, k, t, r, v) = atm_params(100.0);

    for size in sizes {
        group.throughput(Throughput::Elements(size as u64));
        group.bench_with_input(
            BenchmarkId::from_parameter(format!("{size}_spots")),
            &size,
            |b, &size| {
                // 共通関数でスポット価格生成
                let spots = generate_spot_range(size, 80.0, 120.0);
                b.iter(|| {
                    bs_call_price_batch(
                        black_box(&spots),
                        black_box(k),
                        black_box(t),
                        black_box(r),
                        black_box(v),
                    )
                });
            },
        );
    }

    group.finish();
}

fn bench_comparison(c: &mut Criterion) {
    let mut group = c.benchmark_group("comparison");

    // 共通パラメータ使用
    let (s, k, t, r, v) = atm_params(100.0);

    // 単一計算 vs バッチ（1要素）の比較
    group.bench_function("single_call", |b| {
        b.iter(|| {
            bs_call_price(
                black_box(s),
                black_box(k),
                black_box(t),
                black_box(r),
                black_box(v),
            )
        });
    });

    group.bench_function("batch_1_element", |b| {
        let spots = vec![s];
        b.iter(|| {
            bs_call_price_batch(
                black_box(&spots),
                black_box(k),
                black_box(t),
                black_box(r),
                black_box(v),
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
