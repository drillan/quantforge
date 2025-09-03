use quantforge_core::compute::american::*;

fn main() {
    let s = 100.0;
    let k = 100.0;
    let t = 1.0;
    let r = 0.05;
    let q = 0.03;
    let sigma = 0.2;
    
    println!("Testing American options:");
    println!("s={}, k={}, t={}, r={}, q={}, sigma={}", s, k, t, r, q, sigma);
    println!();
    
    // Test binomial tree first
    println!("Binomial tree:");
    let binomial_call = american_binomial(s, k, t, r, q, sigma, 100, true);
    let binomial_put = american_binomial(s, k, t, r, q, sigma, 100, false);
    println!("  Call: {:.6}", binomial_call);
    println!("  Put: {:.6}", binomial_put);
    
    // Test BS2002
    println!("\nBS2002 approximation:");
    let bs2002_call = american_call_scalar(s, k, t, r, q, sigma);
    let bs2002_put = american_put_scalar(s, k, t, r, q, sigma);
    println!("  Call: {:.6}", bs2002_call);
    println!("  Put: {:.6}", bs2002_put);
}