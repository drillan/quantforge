//! 数値解法モジュール
//!
//! インプライドボラティリティ計算のための数値解法を提供。
//! Newton-Raphson法（高速）とBrent法（確実）のハイブリッド実装。

use crate::constants::{
    BRENT_MAX_ITERATIONS, IV_TOLERANCE_VOL, NEWTON_MAX_ATTEMPTS, VEGA_MIN_THRESHOLD,
};
use crate::error::QuantForgeError;

/// Newton-Raphson法による根の探索
///
/// # Arguments
/// * `f` - 目的関数 f(x) = 0 を解く
/// * `df` - 導関数 f'(x)
/// * `x0` - 初期推定値
/// * `tol` - 収束判定閾値
/// * `max_iter` - 最大反復回数
///
/// # Returns
/// * `Ok(x)` - 収束した解
/// * `Err` - 収束失敗
pub fn newton_raphson<F, DF>(
    f: F,
    df: DF,
    x0: f64,
    tol: f64,
    max_iter: usize,
) -> Result<f64, QuantForgeError>
where
    F: Fn(f64) -> f64,
    DF: Fn(f64) -> f64,
{
    let mut x = x0;
    let mut prev_delta: Option<f64> = None;

    for i in 0..max_iter {
        let fx = f(x);

        // 収束判定
        if fx.abs() < tol {
            return Ok(x);
        }

        let dfx = df(x);

        // 導関数が小さすぎる場合は数値的に不安定
        if dfx.abs() < VEGA_MIN_THRESHOLD {
            return Err(QuantForgeError::NumericalInstability);
        }

        let delta = fx / dfx;

        // 振動検出
        if let Some(prev) = prev_delta {
            if delta * prev < 0.0 && (delta.abs() - prev.abs()).abs() < 1e-8 {
                return Err(QuantForgeError::ConvergenceFailed(i));
            }
        }

        x -= delta;
        prev_delta = Some(delta);

        // 変化量による収束判定
        if delta.abs() < IV_TOLERANCE_VOL {
            return Ok(x);
        }
    }

    Err(QuantForgeError::ConvergenceFailed(max_iter))
}

/// Brent法による根の探索
///
/// ブラケット[a, b]内で f(x) = 0 の解を探す。
/// 収束が保証されているが、Newton法より遅い。
///
/// # Arguments
/// * `f` - 目的関数 f(x) = 0 を解く
/// * `a` - 区間の下限
/// * `b` - 区間の上限
/// * `tol` - 収束判定閾値
/// * `max_iter` - 最大反復回数
///
/// # Returns
/// * `Ok(x)` - 収束した解
/// * `Err` - ブラケット不正または収束失敗
pub fn brent<F>(
    f: F,
    mut a: f64,
    mut b: f64,
    tol: f64,
    max_iter: usize,
) -> Result<f64, QuantForgeError>
where
    F: Fn(f64) -> f64,
{
    let mut fa = f(a);
    let mut fb = f(b);

    // ブラケット条件の確認
    if fa * fb > 0.0 {
        return Err(QuantForgeError::BracketingFailed);
    }

    // |f(a)| > |f(b)| となるように並び替え
    if fa.abs() < fb.abs() {
        std::mem::swap(&mut a, &mut b);
        std::mem::swap(&mut fa, &mut fb);
    }

    let mut c = a;
    let mut fc = fa;
    let mut d = b - a;
    let _e = d;
    let mut mflag = true;

    for _ in 0..max_iter {
        // 収束判定
        if fb.abs() < tol {
            return Ok(b);
        }

        let mut s = if (fa - fc).abs() > f64::EPSILON && (fb - fc).abs() > f64::EPSILON {
            // 逆二次補間
            a * fb * fc / ((fa - fb) * (fa - fc))
                + b * fa * fc / ((fb - fa) * (fb - fc))
                + c * fa * fb / ((fc - fa) * (fc - fb))
        } else {
            // 割線法
            b - fb * (b - a) / (fb - fa)
        };

        // Brent条件のチェック
        let condition1 =
            !((3.0 * a + b) / 4.0..=b).contains(&s) && !((b..=(3.0 * a + b) / 4.0).contains(&s));

        let condition2 = mflag && (s - b).abs() >= (b - c).abs() / 2.0;
        let condition3 = !mflag && (s - b).abs() >= (c - d).abs() / 2.0;
        let condition4 = mflag && (b - c).abs() < tol;
        let condition5 = !mflag && (c - d).abs() < tol;

        if condition1 || condition2 || condition3 || condition4 || condition5 {
            // 二分法
            s = (a + b) / 2.0;
            mflag = true;
        } else {
            mflag = false;
        }

        let fs = f(s);
        d = c;
        c = b;
        fc = fb;

        if fa * fs < 0.0 {
            b = s;
            fb = fs;
        } else {
            a = s;
            fa = fs;
        }

        // |f(a)| > |f(b)| を保証
        if fa.abs() < fb.abs() {
            std::mem::swap(&mut a, &mut b);
            std::mem::swap(&mut fa, &mut fb);
        }
    }

    Err(QuantForgeError::ConvergenceFailed(max_iter))
}

/// ハイブリッドソルバー
///
/// Newton-Raphson法で高速収束を試み、失敗したらBrent法にフォールバック。
///
/// # Arguments
/// * `f` - 目的関数
/// * `df` - 導関数（Newton法用）
/// * `initial_guess` - 初期推定値
/// * `bracket_low` - ブラケット下限
/// * `bracket_high` - ブラケット上限
/// * `tol` - 収束判定閾値
///
/// # Returns
/// * `Ok(x)` - 収束した解
/// * `Err` - 収束失敗
pub fn hybrid_solver<F, DF>(
    f: F,
    df: DF,
    initial_guess: f64,
    bracket_low: f64,
    bracket_high: f64,
    tol: f64,
) -> Result<f64, QuantForgeError>
where
    F: Fn(f64) -> f64 + Clone,
    DF: Fn(f64) -> f64,
{
    // まずNewton-Raphson法を試す
    match newton_raphson(&f, df, initial_guess, tol, NEWTON_MAX_ATTEMPTS) {
        Ok(result) => {
            // 解が妥当な範囲内か確認
            if result >= bracket_low && result <= bracket_high {
                Ok(result)
            } else {
                // 範囲外ならBrent法にフォールバック
                brent(f, bracket_low, bracket_high, tol, BRENT_MAX_ITERATIONS)
            }
        }
        Err(_) => {
            // Newton法が失敗したらBrent法を使用
            brent(f, bracket_low, bracket_high, tol, BRENT_MAX_ITERATIONS)
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_newton_raphson_quadratic() {
        // f(x) = x^2 - 4, 解は x = 2
        let f = |x: f64| x * x - 4.0;
        let df = |x: f64| 2.0 * x;

        let result = newton_raphson(f, df, 3.0, 1e-9, 100).unwrap();
        assert!((result - 2.0).abs() < 1e-9);
    }

    #[test]
    fn test_brent_quadratic() {
        // f(x) = x^2 - 4, 解は x = 2
        let f = |x: f64| x * x - 4.0;

        let result = brent(f, 0.0, 3.0, 1e-9, 100).unwrap();
        assert!((result - 2.0).abs() < 1e-9);
    }

    #[test]
    fn test_hybrid_solver() {
        // f(x) = x^3 - x - 2, 解は約 x = 1.5214
        let f = |x: f64| x * x * x - x - 2.0;
        let df = |x: f64| 3.0 * x * x - 1.0;

        let result = hybrid_solver(f, df, 1.5, 0.0, 3.0, 1e-9).unwrap();
        assert!((result - 1.5213797068045675).abs() < 1e-9);
    }

    #[test]
    fn test_newton_numerical_instability() {
        // f(x) = x, f'(x) = 0 に近い（数値的に不安定）
        let f = |x: f64| x;
        let df = |_x: f64| 1e-15; // 非常に小さい導関数

        let result = newton_raphson(f, df, 1.0, 1e-9, 100);
        assert!(matches!(result, Err(QuantForgeError::NumericalInstability)));
    }

    #[test]
    fn test_brent_invalid_bracket() {
        // f(x) = x^2 + 1, 実数解なし
        let f = |x: f64| x * x + 1.0;

        let result = brent(f, -1.0, 1.0, 1e-9, 100);
        assert!(matches!(result, Err(QuantForgeError::BracketingFailed)));
    }
}
