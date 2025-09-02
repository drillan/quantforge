use arrow::array::{Float64Array, Float64Builder};
use criterion::{black_box, criterion_group, criterion_main, Criterion};

fn benchmark_vec_approach(size: usize) -> Float64Array {
    let mut vec = Vec::with_capacity(size);
    for i in 0..size {
        vec.push(i as f64 * 0.5);
    }
    Float64Array::from(vec)
}

fn benchmark_builder_approach(size: usize) -> Float64Array {
    let mut builder = Float64Builder::with_capacity(size);
    for i in 0..size {
        builder.append_value(i as f64 * 0.5);
    }
    builder.finish()
}

fn criterion_benchmark(c: &mut Criterion) {
    let sizes = vec![100, 1_000, 10_000, 100_000];
    
    for size in sizes {
        c.bench_function(&format!("vec_{}", size), |b| {
            b.iter(|| benchmark_vec_approach(black_box(size)))
        });
        
        c.bench_function(&format!("builder_{}", size), |b| {
            b.iter(|| benchmark_builder_approach(black_box(size)))
        });
    }
}

criterion_group!(benches, criterion_benchmark);
criterion_main!(benches);
