use criterion::{criterion_group, criterion_main, Criterion};
use rust_crate::add;
use std::hint::black_box;

fn benchmark_add(c: &mut Criterion) {
    c.bench_function("add_two_numbers", |b| {
        b.iter(|| add(black_box(2), black_box(2)))
    });
}

criterion_group!(benches, benchmark_add);
criterion_main!(benches);
