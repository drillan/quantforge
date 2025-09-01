//! PyArrow Native Bindings
//!
//! 真のゼロコピーを実現するPyArrowネイティブバインディング。
//! PyArrow配列を直接受け取り、Arrow配列として処理。

use arrow::array::{ArrayRef, Float64Array};
use arrow::buffer::Buffer;
use arrow::ffi::{from_ffi, to_ffi, FFI_ArrowArray, FFI_ArrowSchema};
use numpy::{PyArray1, PyArrayMethods};
use pyo3::prelude::*;
use pyo3::types::{PyCapsule, PyTuple};
use quantforge_core::compute::ArrowNativeCompute;
use quantforge_core::error::QuantForgeError;
use std::sync::Arc;

/// PyArrowからArrow配列への変換（ゼロコピー）
///
/// PyArrowのC Data Interfaceを使用してゼロコピー変換を実現
fn pyarrow_to_arrow(py_array: &Bound<'_, PyAny>) -> PyResult<ArrayRef> {
    // PyArrowの__arrow_c_array__メソッドを呼び出し
    let capsule_tuple = py_array.call_method0("__arrow_c_array__")?;
    let capsule_tuple = capsule_tuple.downcast::<PyTuple>()?;
    
    // カプセルからFFIポインタを取得
    let array_capsule = capsule_tuple.get_item(0)?;
    let schema_capsule = capsule_tuple.get_item(1)?;
    
    let array_ptr = array_capsule
        .downcast::<PyCapsule>()?
        .pointer() as *mut FFI_ArrowArray;
    let schema_ptr = schema_capsule
        .downcast::<PyCapsule>()?
        .pointer() as *mut FFI_ArrowSchema;
    
    // Arrow配列として再構築（ゼロコピー）
    unsafe {
        let array = from_ffi(Arc::new(*schema_ptr), Arc::new(*array_ptr))
            .map_err(|e| PyErr::new::<pyo3::exceptions::PyTypeError, _>(format!("Arrow FFI error: {}", e)))?;
        Ok(array)
    }
}

/// ArrowからPyArrowへの変換（ゼロコピー）
fn arrow_to_pyarrow<'py>(py: Python<'py>, array: ArrayRef) -> PyResult<Bound<'py, PyAny>> {
    // ArrowをFFI形式にエクスポート
    let (array_ffi, schema_ffi) = to_ffi(&array.to_data())
        .map_err(|e| PyErr::new::<pyo3::exceptions::PyTypeError, _>(format!("Arrow FFI export error: {}", e)))?;
    
    // PyCapsuleとして包む
    let array_capsule = PyCapsule::new_bound(
        py,
        Box::into_raw(Box::new(array_ffi)) as *mut std::ffi::c_void,
        Some(c"arrow_array"),
    )?;
    
    let schema_capsule = PyCapsule::new_bound(
        py,
        Box::into_raw(Box::new(schema_ffi)) as *mut std::ffi::c_void,
        Some(c"arrow_schema"),
    )?;
    
    // pyarrowモジュールをインポート
    let pyarrow = py.import("pyarrow")?;
    let array_class = pyarrow.getattr("Array")?;
    
    // PyArrow配列を作成
    let py_array = array_class.call_method1(
        "_import_from_c_capsule",
        (array_capsule, schema_capsule),
    )?;
    
    Ok(py_array)
}

/// Black-Scholesコール価格計算（PyArrowネイティブ）
#[pyfunction]
#[pyo3(name = "black_scholes_call_price_arrow")]
#[pyo3(signature = (spots, strikes, times, rates, sigmas))]
pub fn black_scholes_call_price_arrow<'py>(
    py: Python<'py>,
    spots: &Bound<'py, PyAny>,
    strikes: &Bound<'py, PyAny>,
    times: &Bound<'py, PyAny>,
    rates: &Bound<'py, PyAny>,
    sigmas: &Bound<'py, PyAny>,
) -> PyResult<Bound<'py, PyAny>> {
    // PyArrowからArrowへ変換（ゼロコピー）
    let spots_arrow = pyarrow_to_arrow(spots)?;
    let strikes_arrow = pyarrow_to_arrow(strikes)?;
    let times_arrow = pyarrow_to_arrow(times)?;
    let rates_arrow = pyarrow_to_arrow(rates)?;
    let sigmas_arrow = pyarrow_to_arrow(sigmas)?;
    
    // Float64Arrayにダウンキャスト
    let spots_f64 = spots_arrow
        .as_any()
        .downcast_ref::<Float64Array>()
        .ok_or_else(|| PyErr::new::<pyo3::exceptions::PyTypeError, _>("spots must be Float64Array"))?;
    let strikes_f64 = strikes_arrow
        .as_any()
        .downcast_ref::<Float64Array>()
        .ok_or_else(|| PyErr::new::<pyo3::exceptions::PyTypeError, _>("strikes must be Float64Array"))?;
    let times_f64 = times_arrow
        .as_any()
        .downcast_ref::<Float64Array>()
        .ok_or_else(|| PyErr::new::<pyo3::exceptions::PyTypeError, _>("times must be Float64Array"))?;
    let rates_f64 = rates_arrow
        .as_any()
        .downcast_ref::<Float64Array>()
        .ok_or_else(|| PyErr::new::<pyo3::exceptions::PyTypeError, _>("rates must be Float64Array"))?;
    let sigmas_f64 = sigmas_arrow
        .as_any()
        .downcast_ref::<Float64Array>()
        .ok_or_else(|| PyErr::new::<pyo3::exceptions::PyTypeError, _>("sigmas must be Float64Array"))?;
    
    // GILを解放して計算
    let result = py.allow_threads(|| {
        ArrowNativeCompute::black_scholes_call_price(
            spots_f64,
            strikes_f64,
            times_f64,
            rates_f64,
            sigmas_f64,
        )
    }).map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(format!("Computation error: {}", e)))?;
    
    // ArrowからPyArrowへ変換（ゼロコピー）
    arrow_to_pyarrow(py, result)
}

/// Black-Scholesプット価格計算（PyArrowネイティブ）
#[pyfunction]
#[pyo3(name = "black_scholes_put_price_arrow")]
#[pyo3(signature = (spots, strikes, times, rates, sigmas))]
pub fn black_scholes_put_price_arrow<'py>(
    py: Python<'py>,
    spots: &Bound<'py, PyAny>,
    strikes: &Bound<'py, PyAny>,
    times: &Bound<'py, PyAny>,
    rates: &Bound<'py, PyAny>,
    sigmas: &Bound<'py, PyAny>,
) -> PyResult<Bound<'py, PyAny>> {
    // PyArrowからArrowへ変換（ゼロコピー）
    let spots_arrow = pyarrow_to_arrow(spots)?;
    let strikes_arrow = pyarrow_to_arrow(strikes)?;
    let times_arrow = pyarrow_to_arrow(times)?;
    let rates_arrow = pyarrow_to_arrow(rates)?;
    let sigmas_arrow = pyarrow_to_arrow(sigmas)?;
    
    // Float64Arrayにダウンキャスト
    let spots_f64 = spots_arrow
        .as_any()
        .downcast_ref::<Float64Array>()
        .ok_or_else(|| PyErr::new::<pyo3::exceptions::PyTypeError, _>("spots must be Float64Array"))?;
    let strikes_f64 = strikes_arrow
        .as_any()
        .downcast_ref::<Float64Array>()
        .ok_or_else(|| PyErr::new::<pyo3::exceptions::PyTypeError, _>("strikes must be Float64Array"))?;
    let times_f64 = times_arrow
        .as_any()
        .downcast_ref::<Float64Array>()
        .ok_or_else(|| PyErr::new::<pyo3::exceptions::PyTypeError, _>("times must be Float64Array"))?;
    let rates_f64 = rates_arrow
        .as_any()
        .downcast_ref::<Float64Array>()
        .ok_or_else(|| PyErr::new::<pyo3::exceptions::PyTypeError, _>("rates must be Float64Array"))?;
    let sigmas_f64 = sigmas_arrow
        .as_any()
        .downcast_ref::<Float64Array>()
        .ok_or_else(|| PyErr::new::<pyo3::exceptions::PyTypeError, _>("sigmas must be Float64Array"))?;
    
    // GILを解放して計算
    let result = py.allow_threads(|| {
        ArrowNativeCompute::black_scholes_put_price(
            spots_f64,
            strikes_f64,
            times_f64,
            rates_f64,
            sigmas_f64,
        )
    }).map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(format!("Computation error: {}", e)))?;
    
    // ArrowからPyArrowへ変換（ゼロコピー）
    arrow_to_pyarrow(py, result)
}

/// Black76コール価格計算（PyArrowネイティブ）
#[pyfunction]
#[pyo3(name = "black76_call_price_arrow")]
#[pyo3(signature = (forwards, strikes, times, rates, sigmas))]
pub fn black76_call_price_arrow<'py>(
    py: Python<'py>,
    forwards: &Bound<'py, PyAny>,
    strikes: &Bound<'py, PyAny>,
    times: &Bound<'py, PyAny>,
    rates: &Bound<'py, PyAny>,
    sigmas: &Bound<'py, PyAny>,
) -> PyResult<Bound<'py, PyAny>> {
    // PyArrowからArrowへ変換（ゼロコピー）
    let forwards_arrow = pyarrow_to_arrow(forwards)?;
    let strikes_arrow = pyarrow_to_arrow(strikes)?;
    let times_arrow = pyarrow_to_arrow(times)?;
    let rates_arrow = pyarrow_to_arrow(rates)?;
    let sigmas_arrow = pyarrow_to_arrow(sigmas)?;
    
    // Float64Arrayにダウンキャスト
    let forwards_f64 = forwards_arrow
        .as_any()
        .downcast_ref::<Float64Array>()
        .ok_or_else(|| PyErr::new::<pyo3::exceptions::PyTypeError, _>("forwards must be Float64Array"))?;
    let strikes_f64 = strikes_arrow
        .as_any()
        .downcast_ref::<Float64Array>()
        .ok_or_else(|| PyErr::new::<pyo3::exceptions::PyTypeError, _>("strikes must be Float64Array"))?;
    let times_f64 = times_arrow
        .as_any()
        .downcast_ref::<Float64Array>()
        .ok_or_else(|| PyErr::new::<pyo3::exceptions::PyTypeError, _>("times must be Float64Array"))?;
    let rates_f64 = rates_arrow
        .as_any()
        .downcast_ref::<Float64Array>()
        .ok_or_else(|| PyErr::new::<pyo3::exceptions::PyTypeError, _>("rates must be Float64Array"))?;
    let sigmas_f64 = sigmas_arrow
        .as_any()
        .downcast_ref::<Float64Array>()
        .ok_or_else(|| PyErr::new::<pyo3::exceptions::PyTypeError, _>("sigmas must be Float64Array"))?;
    
    // GILを解放して計算
    let result = py.allow_threads(|| {
        ArrowNativeCompute::black76_call_price(
            forwards_f64,
            strikes_f64,
            times_f64,
            rates_f64,
            sigmas_f64,
        )
    }).map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(format!("Computation error: {}", e)))?;
    
    // ArrowからPyArrowへ変換（ゼロコピー）
    arrow_to_pyarrow(py, result)
}

/// Black76プット価格計算（PyArrowネイティブ）
#[pyfunction]
#[pyo3(name = "black76_put_price_arrow")]
#[pyo3(signature = (forwards, strikes, times, rates, sigmas))]
pub fn black76_put_price_arrow<'py>(
    py: Python<'py>,
    forwards: &Bound<'py, PyAny>,
    strikes: &Bound<'py, PyAny>,
    times: &Bound<'py, PyAny>,
    rates: &Bound<'py, PyAny>,
    sigmas: &Bound<'py, PyAny>,
) -> PyResult<Bound<'py, PyAny>> {
    // PyArrowからArrowへ変換（ゼロコピー）
    let forwards_arrow = pyarrow_to_arrow(forwards)?;
    let strikes_arrow = pyarrow_to_arrow(strikes)?;
    let times_arrow = pyarrow_to_arrow(times)?;
    let rates_arrow = pyarrow_to_arrow(rates)?;
    let sigmas_arrow = pyarrow_to_arrow(sigmas)?;
    
    // Float64Arrayにダウンキャスト
    let forwards_f64 = forwards_arrow
        .as_any()
        .downcast_ref::<Float64Array>()
        .ok_or_else(|| PyErr::new::<pyo3::exceptions::PyTypeError, _>("forwards must be Float64Array"))?;
    let strikes_f64 = strikes_arrow
        .as_any()
        .downcast_ref::<Float64Array>()
        .ok_or_else(|| PyErr::new::<pyo3::exceptions::PyTypeError, _>("strikes must be Float64Array"))?;
    let times_f64 = times_arrow
        .as_any()
        .downcast_ref::<Float64Array>()
        .ok_or_else(|| PyErr::new::<pyo3::exceptions::PyTypeError, _>("times must be Float64Array"))?;
    let rates_f64 = rates_arrow
        .as_any()
        .downcast_ref::<Float64Array>()
        .ok_or_else(|| PyErr::new::<pyo3::exceptions::PyTypeError, _>("rates must be Float64Array"))?;
    let sigmas_f64 = sigmas_arrow
        .as_any()
        .downcast_ref::<Float64Array>()
        .ok_or_else(|| PyErr::new::<pyo3::exceptions::PyTypeError, _>("sigmas must be Float64Array"))?;
    
    // GILを解放して計算
    let result = py.allow_threads(|| {
        ArrowNativeCompute::black76_put_price(
            forwards_f64,
            strikes_f64,
            times_f64,
            rates_f64,
            sigmas_f64,
        )
    }).map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(format!("Computation error: {}", e)))?;
    
    // ArrowからPyArrowへ変換（ゼロコピー）
    arrow_to_pyarrow(py, result)
}

/// Mertonコール価格計算（配当付き、PyArrowネイティブ）
#[pyfunction]
#[pyo3(name = "merton_call_price_arrow")]
#[pyo3(signature = (spots, strikes, times, rates, dividend_yields, sigmas))]
pub fn merton_call_price_arrow<'py>(
    py: Python<'py>,
    spots: &Bound<'py, PyAny>,
    strikes: &Bound<'py, PyAny>,
    times: &Bound<'py, PyAny>,
    rates: &Bound<'py, PyAny>,
    dividend_yields: &Bound<'py, PyAny>,
    sigmas: &Bound<'py, PyAny>,
) -> PyResult<Bound<'py, PyAny>> {
    // PyArrowからArrowへ変換（ゼロコピー）
    let spots_arrow = pyarrow_to_arrow(spots)?;
    let strikes_arrow = pyarrow_to_arrow(strikes)?;
    let times_arrow = pyarrow_to_arrow(times)?;
    let rates_arrow = pyarrow_to_arrow(rates)?;
    let dividend_yields_arrow = pyarrow_to_arrow(dividend_yields)?;
    let sigmas_arrow = pyarrow_to_arrow(sigmas)?;
    
    // Float64Arrayにダウンキャスト
    let spots_f64 = spots_arrow
        .as_any()
        .downcast_ref::<Float64Array>()
        .ok_or_else(|| PyErr::new::<pyo3::exceptions::PyTypeError, _>("spots must be Float64Array"))?;
    let strikes_f64 = strikes_arrow
        .as_any()
        .downcast_ref::<Float64Array>()
        .ok_or_else(|| PyErr::new::<pyo3::exceptions::PyTypeError, _>("strikes must be Float64Array"))?;
    let times_f64 = times_arrow
        .as_any()
        .downcast_ref::<Float64Array>()
        .ok_or_else(|| PyErr::new::<pyo3::exceptions::PyTypeError, _>("times must be Float64Array"))?;
    let rates_f64 = rates_arrow
        .as_any()
        .downcast_ref::<Float64Array>()
        .ok_or_else(|| PyErr::new::<pyo3::exceptions::PyTypeError, _>("rates must be Float64Array"))?;
    let dividend_yields_f64 = dividend_yields_arrow
        .as_any()
        .downcast_ref::<Float64Array>()
        .ok_or_else(|| PyErr::new::<pyo3::exceptions::PyTypeError, _>("dividend_yields must be Float64Array"))?;
    let sigmas_f64 = sigmas_arrow
        .as_any()
        .downcast_ref::<Float64Array>()
        .ok_or_else(|| PyErr::new::<pyo3::exceptions::PyTypeError, _>("sigmas must be Float64Array"))?;
    
    // GILを解放して計算
    let result = py.allow_threads(|| {
        ArrowNativeCompute::merton_call_price(
            spots_f64,
            strikes_f64,
            times_f64,
            rates_f64,
            dividend_yields_f64,
            sigmas_f64,
        )
    }).map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(format!("Computation error: {}", e)))?;
    
    // ArrowからPyArrowへ変換（ゼロコピー）
    arrow_to_pyarrow(py, result)
}

/// Mertonプット価格計算（配当付き、PyArrowネイティブ）
#[pyfunction]
#[pyo3(name = "merton_put_price_arrow")]
#[pyo3(signature = (spots, strikes, times, rates, dividend_yields, sigmas))]
pub fn merton_put_price_arrow<'py>(
    py: Python<'py>,
    spots: &Bound<'py, PyAny>,
    strikes: &Bound<'py, PyAny>,
    times: &Bound<'py, PyAny>,
    rates: &Bound<'py, PyAny>,
    dividend_yields: &Bound<'py, PyAny>,
    sigmas: &Bound<'py, PyAny>,
) -> PyResult<Bound<'py, PyAny>> {
    // PyArrowからArrowへ変換（ゼロコピー）
    let spots_arrow = pyarrow_to_arrow(spots)?;
    let strikes_arrow = pyarrow_to_arrow(strikes)?;
    let times_arrow = pyarrow_to_arrow(times)?;
    let rates_arrow = pyarrow_to_arrow(rates)?;
    let dividend_yields_arrow = pyarrow_to_arrow(dividend_yields)?;
    let sigmas_arrow = pyarrow_to_arrow(sigmas)?;
    
    // Float64Arrayにダウンキャスト
    let spots_f64 = spots_arrow
        .as_any()
        .downcast_ref::<Float64Array>()
        .ok_or_else(|| PyErr::new::<pyo3::exceptions::PyTypeError, _>("spots must be Float64Array"))?;
    let strikes_f64 = strikes_arrow
        .as_any()
        .downcast_ref::<Float64Array>()
        .ok_or_else(|| PyErr::new::<pyo3::exceptions::PyTypeError, _>("strikes must be Float64Array"))?;
    let times_f64 = times_arrow
        .as_any()
        .downcast_ref::<Float64Array>()
        .ok_or_else(|| PyErr::new::<pyo3::exceptions::PyTypeError, _>("times must be Float64Array"))?;
    let rates_f64 = rates_arrow
        .as_any()
        .downcast_ref::<Float64Array>()
        .ok_or_else(|| PyErr::new::<pyo3::exceptions::PyTypeError, _>("rates must be Float64Array"))?;
    let dividend_yields_f64 = dividend_yields_arrow
        .as_any()
        .downcast_ref::<Float64Array>()
        .ok_or_else(|| PyErr::new::<pyo3::exceptions::PyTypeError, _>("dividend_yields must be Float64Array"))?;
    let sigmas_f64 = sigmas_arrow
        .as_any()
        .downcast_ref::<Float64Array>()
        .ok_or_else(|| PyErr::new::<pyo3::exceptions::PyTypeError, _>("sigmas must be Float64Array"))?;
    
    // GILを解放して計算
    let result = py.allow_threads(|| {
        ArrowNativeCompute::merton_put_price(
            spots_f64,
            strikes_f64,
            times_f64,
            rates_f64,
            dividend_yields_f64,
            sigmas_f64,
        )
    }).map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(format!("Computation error: {}", e)))?;
    
    // ArrowからPyArrowへ変換（ゼロコピー）
    arrow_to_pyarrow(py, result)
}

/// モジュールを登録
pub fn register_arrow_functions(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(black_scholes_call_price_arrow, m)?)?;
    m.add_function(wrap_pyfunction!(black_scholes_put_price_arrow, m)?)?;
    m.add_function(wrap_pyfunction!(black76_call_price_arrow, m)?)?;
    m.add_function(wrap_pyfunction!(black76_put_price_arrow, m)?)?;
    m.add_function(wrap_pyfunction!(merton_call_price_arrow, m)?)?;
    m.add_function(wrap_pyfunction!(merton_put_price_arrow, m)?)?;
    Ok(())
}