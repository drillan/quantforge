//! Python bindings for QuantForge
//!
//! This module provides Python bindings for the QuantForge core library.

use pyo3::prelude::*;

mod converters;
mod error;
mod models;

use models::{american, black76, black_scholes, instrumented, merton};

/// Main Python module definition
#[pymodule]
fn quantforge(m: &Bound<'_, PyModule>) -> PyResult<()> {
    // Version information
    m.add("__version__", "0.1.0")?;

    // Create submodules at top level
    let black_scholes_module = PyModule::new_bound(m.py(), "black_scholes")?;
    black_scholes::register_functions(&black_scholes_module)?;
    m.add_submodule(&black_scholes_module)?;

    let black76_module = black76::create_module(m.py())?;
    m.add_submodule(&black76_module)?;

    let merton_module = merton::create_module(m.py())?;
    m.add_submodule(&merton_module)?;

    let american_module = american::create_module(m.py())?;
    m.add_submodule(&american_module)?;

    // Add instrumented module for profiling
    let instrumented_module = PyModule::new_bound(m.py(), "instrumented")?;
    instrumented::register_instrumented(&instrumented_module)?;
    m.add_submodule(&instrumented_module)?;
    
    // Ensure the module is available at the package level
    let sys_modules = m.py().import_bound("sys")?.getattr("modules")?;
    sys_modules.set_item("quantforge.instrumented", &instrumented_module)?;

    Ok(())
}
