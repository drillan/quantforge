//! Benchmarks for mathematical functions

use criterion::{black_box, criterion_group, criterion_main, Criterion};
use quantforge_core::math::distributions::{norm_cdf, norm_pdf};
use quantforge_core::math::solvers::{brent, newton_raphson};

/// Benchmark distribution functions
fn bench_distributions(c: &mut Criterion) {
    c.bench_function("norm_cdf_zero", |b| {
        b.iter(|| black_box(norm_cdf(black_box(0.0))))
    });
    
    c.bench_function("norm_cdf_positive", |b| {
        b.iter(|| black_box(norm_cdf(black_box(1.96))))
    });
    
    c.bench_function("norm_cdf_negative", |b| {
        b.iter(|| black_box(norm_cdf(black_box(-1.96))))
    });
    
    c.bench_function("norm_cdf_extreme", |b| {
        b.iter(|| black_box(norm_cdf(black_box(5.0))))
    });
    
    c.bench_function("norm_pdf_zero", |b| {
        b.iter(|| black_box(norm_pdf(black_box(0.0))))
    });
    
    c.bench_function("norm_pdf_standard", |b| {
        b.iter(|| black_box(norm_pdf(black_box(1.0))))
    });
    
    c.bench_function("norm_pdf_extreme", |b| {
        b.iter(|| black_box(norm_pdf(black_box(5.0))))
    });
}

/// Benchmark various values for norm_cdf
fn bench_norm_cdf_range(c: &mut Criterion) {
    let values = vec![-3.0, -2.0, -1.0, 0.0, 1.0, 2.0, 3.0];
    
    c.bench_function("norm_cdf_range", |b| {
        b.iter(|| {
            for &x in &values {
                black_box(norm_cdf(black_box(x)));
            }
        })
    });
}

/// Benchmark solver functions
fn bench_solvers(c: &mut Criterion) {
    // Quadratic function: f(x) = x^2 - 2
    let objective = |x: f64| x * x - 2.0;
    let derivative = |x: f64| 2.0 * x;
    
    c.bench_function("newton_raphson_quadratic", |b| {
        b.iter(|| {
            black_box(newton_raphson(
                objective,
                derivative,
                black_box(1.0),
                black_box(1e-10),
                black_box(100),
            ))
        })
    });
    
    c.bench_function("brent_quadratic", |b| {
        b.iter(|| {
            black_box(brent(
                objective,
                black_box(0.0),
                black_box(2.0),
                black_box(1e-10),
                black_box(100),
            ))
        })
    });
    
    // More complex function: f(x) = cos(x) - x
    let complex_objective = |x: f64| x.cos() - x;
    let complex_derivative = |x: f64| -x.sin() - 1.0;
    
    c.bench_function("newton_raphson_complex", |b| {
        b.iter(|| {
            black_box(newton_raphson(
                complex_objective,
                complex_derivative,
                black_box(0.5),
                black_box(1e-10),
                black_box(100),
            ))
        })
    });
    
    c.bench_function("brent_complex", |b| {
        b.iter(|| {
            black_box(brent(
                complex_objective,
                black_box(0.0),
                black_box(1.0),
                black_box(1e-10),
                black_box(100),
            ))
        })
    });
}

/// Benchmark batch norm_cdf calculations
fn bench_batch_norm_cdf(c: &mut Criterion) {
    let n = 1000;
    let values: Vec<f64> = (0..n).map(|i| -3.0 + 6.0 * (i as f64) / (n as f64)).collect();
    
    c.bench_function("norm_cdf_batch_1000", |b| {
        b.iter(|| {
            let mut results = Vec::with_capacity(n);
            for &x in &values {
                results.push(black_box(norm_cdf(black_box(x))));
            }
            black_box(results)
        })
    });
}

criterion_group!(
    benches,
    bench_distributions,
    bench_norm_cdf_range,
    bench_solvers,
    bench_batch_norm_cdf
);
criterion_main!(benches);