//! パフォーマンス最適化モジュール

pub mod loop_unrolling;
pub mod parallel_strategy;

pub use parallel_strategy::{ParallelStrategy, ProcessingMode};
