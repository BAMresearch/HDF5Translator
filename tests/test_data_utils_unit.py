from __future__ import annotations

import numpy as np

from HDF5Translator.translator_elements import TranslationElement
from HDF5Translator.utils.data_utils import add_dimensions_if_needed, cast_to_datatype


def _element(**overrides: object) -> TranslationElement:
    params: dict[str, object] = {
        "destination": "/entry/data/value",
        "data_type": "float32",
        "minimum_dimensionality": None,
    }
    params.update(overrides)
    return TranslationElement(**params)


def test_add_dimensions_does_not_copy_when_dimensionality_is_sufficient() -> None:
    input_data = np.arange(6, dtype=np.float32).reshape(2, 3)
    element = _element(minimum_dimensionality=2)

    output_data = add_dimensions_if_needed(input_data, element)

    assert output_data is input_data


def test_add_dimensions_prepends_singleton_dimensions_without_copying_array_values() -> None:
    input_data = np.arange(6, dtype=np.float32).reshape(2, 3)
    element = _element(minimum_dimensionality=4)

    output_data = add_dimensions_if_needed(input_data, element)

    assert isinstance(output_data, np.ndarray)
    assert output_data.shape == (1, 1, 2, 3)
    assert np.shares_memory(output_data, input_data)


def test_cast_to_datatype_reuses_array_when_dtype_matches() -> None:
    input_data = np.arange(6, dtype=np.float32).reshape(2, 3)
    element = _element(data_type="float32")

    output_data = cast_to_datatype(input_data, element)

    assert output_data is input_data


def test_cast_to_datatype_converts_array_when_dtype_differs() -> None:
    input_data = np.arange(6, dtype=np.float32).reshape(2, 3)
    element = _element(data_type="int32")

    output_data = cast_to_datatype(input_data, element)

    assert isinstance(output_data, np.ndarray)
    assert output_data.dtype == np.dtype(np.int32)
    assert np.array_equal(output_data, input_data.astype(np.int32))
