use crate::error::QuantForgeError;

pub struct InputLimits {
    pub min_price: f64,
    pub max_price: f64,
    pub min_time: f64,
    pub max_time: f64,
    pub min_vol: f64,
    pub max_vol: f64,
    pub min_rate: f64,
    pub max_rate: f64,
}

impl Default for InputLimits {
    fn default() -> Self {
        Self {
            min_price: 0.01,
            max_price: 2147483648.0, // 2^31
            min_time: 0.001,         // 1日
            max_time: 100.0,         // 100年
            min_vol: 0.005,          // 0.5%
            max_vol: 10.0,           // 1000%
            min_rate: -1.0,          // -100%
            max_rate: 1.0,           // 100%
        }
    }
}

pub fn validate_inputs(s: f64, k: f64, t: f64, r: f64, v: f64) -> Result<(), QuantForgeError> {
    let limits = InputLimits::default();

    // NaN/Inf チェック
    if !s.is_finite() || !k.is_finite() || !t.is_finite() || !r.is_finite() || !v.is_finite() {
        return Err(QuantForgeError::InvalidNumericValue);
    }

    // 価格チェック
    if s <= 0.0 || s < limits.min_price || s > limits.max_price {
        return Err(QuantForgeError::InvalidSpotPrice(s));
    }
    if k <= 0.0 || k < limits.min_price || k > limits.max_price {
        return Err(QuantForgeError::InvalidStrikePrice(k));
    }

    // 時間チェック
    if t <= 0.0 || t < limits.min_time || t > limits.max_time {
        return Err(QuantForgeError::InvalidTime(t));
    }

    // ボラティリティチェック
    if v <= 0.0 || v < limits.min_vol || v > limits.max_vol {
        return Err(QuantForgeError::InvalidVolatility(v));
    }

    // 金利チェック
    if r < limits.min_rate || r > limits.max_rate {
        return Err(QuantForgeError::InvalidInput(format!(
            "Interest rate {} is out of range [{}, {}]",
            r, limits.min_rate, limits.max_rate
        )));
    }

    Ok(())
}
