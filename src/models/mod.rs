pub mod black_scholes;
pub mod black_scholes_parallel;

pub use black_scholes::{bs_call_price, bs_call_price_batch};
pub use black_scholes_parallel::{bs_call_price_batch_parallel, bs_call_price_batch_parallel_py};