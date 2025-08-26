#![allow(clippy::useless_conversion)]

use pyo3::prelude::*;

pub mod constants;
pub mod error;
pub mod math;
pub mod models;
pub mod python_modules;
pub mod validation;

/// Main Python module
#[pymodule]
fn quantforge(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add("__version__", "0.1.0")?;

    // Add models submodule only - this is the only API
    let models = PyModule::new_bound(m.py(), "models")?;
    python_modules::black_scholes(&models)?;

    // Add black76 as a submodule of models
    let black76 = PyModule::new_bound(m.py(), "black76")?;
    python_modules::black76(&black76)?;
    models.add_submodule(&black76)?;

    m.add_submodule(&models)?;

    Ok(())
}
