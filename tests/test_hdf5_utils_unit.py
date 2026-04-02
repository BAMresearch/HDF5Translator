from __future__ import annotations

from pathlib import Path

import h5py
import numpy as np

from HDF5Translator.translator_elements import TranslationElement
from HDF5Translator.utils.hdf5_utils import (
    get_data_and_attributes_from_source,
    write_dataset,
)


def test_write_dataset_creates_dataset_and_updates_attributes(tmp_path: Path) -> None:
    output_file = tmp_path / "output.h5"
    data = np.arange(12, dtype=np.int32).reshape(3, 4)

    with h5py.File(output_file, "w") as h5_file:
        write_dataset(
            h5_file,
            "/entry/data",
            data,
            compression="gzip",
            attributes={"units": "counts", "long_name": "detector data"},
        )

        written = h5_file["/entry/data"]
        assert isinstance(written, h5py.Dataset)
        assert np.array_equal(written[()], data)
        assert written.compression == "gzip"
        assert written.attrs["units"] == "counts"
        assert written.attrs["long_name"] == "detector data"


def test_write_dataset_replaces_incompatible_dataset_shape(tmp_path: Path) -> None:
    output_file = tmp_path / "replace.h5"
    first_data = np.arange(6, dtype=np.int16).reshape(2, 3)
    second_data = np.arange(20, dtype=np.int16).reshape(4, 5)

    with h5py.File(output_file, "w") as h5_file:
        write_dataset(h5_file, "/entry/data", first_data)
        write_dataset(h5_file, "/entry/data", second_data)

        written = h5_file["/entry/data"]
        assert written.shape == (4, 5)
        assert written.dtype == np.dtype(np.int16)
        assert np.array_equal(written[()], second_data)


def test_get_data_and_attributes_from_source_uses_cache_when_available(tmp_path: Path) -> None:
    source_file = tmp_path / "source.h5"
    with h5py.File(source_file, "w") as h5_file:
        dataset = h5_file.create_dataset("/entry/value", data=np.array([1, 2, 3], dtype=np.int32))
        dataset.attrs["units"] = "counts"

    element = TranslationElement(destination="/output/value", source="/entry/value", data_type="int32")
    source_cache: dict[tuple[str, str], tuple[object, dict[str, object]]] = {}

    with h5py.File(source_file, "r+") as h5_file:
        first_data, first_attrs = get_data_and_attributes_from_source(
            h5_file,
            element,
            source_data_cache=source_cache,
        )
        h5_file["/entry/value"][...] = np.array([9, 9, 9], dtype=np.int32)
        second_data, second_attrs = get_data_and_attributes_from_source(
            h5_file,
            element,
            source_data_cache=source_cache,
        )

    assert np.array_equal(first_data, np.array([1, 2, 3], dtype=np.int32))
    assert np.array_equal(second_data, np.array([1, 2, 3], dtype=np.int32))
    assert first_attrs == second_attrs == {"units": "counts"}
