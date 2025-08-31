use quantforge_core::models::american::boundary::calculate_exercise_boundary;
use quantforge_core::models::american::pricing::AmericanParams;

fn main() {
    // Test ATM case for put
    let params = AmericanParams {
        s: 100.0,
        k: 100.0,
        t: 1.0,
        r: 0.05,
        q: 0.0,
        sigma: 0.2,
    };
    
    println!("Testing early exercise boundary:");
    println!("Parameters: s={}, k={}, t={}, r={}, q={}, sigma={}", 
             params.s, params.k, params.t, params.r, params.q, params.sigma);
    
    let put_boundary = calculate_exercise_boundary(&params, false).unwrap();
    println!("Put exercise boundary: {}", put_boundary);
    
    if put_boundary < params.k {
        println!("✓ Boundary is below strike (early exercise possible)");
    } else {
        println!("⚠️ Boundary is at or above strike");
    }
}
