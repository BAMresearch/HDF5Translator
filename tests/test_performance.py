from __future__ import annotations

import statistics
import time
from pathlib import Path

import h5py
import numpy as np
import pytest

from HDF5Translator.translator_elements import TranslationElement
from HDF5Translator.utils.hdf5_utils import get_data_and_attributes_from_source, write_dataset


@pytest.mark.perf
def test_write_dataset_is_faster_than_reference_double_write(tmp_path: Path) -> None:
    data = np.random.default_rng(0).integers(0, 2000, size=(12, 384, 384), dtype=np.int32)

    def reference_write_dataset(path: Path) -> float:
        start = time.perf_counter()
        with h5py.File(path, "w") as h5_file:
            chunking_shape = (1, data.shape[-2], data.shape[-1])
            dataset = h5_file.require_dataset(
                "/entry/data",
                shape=data.shape,
                dtype=data.dtype,
                data=data,
                compression="gzip",
                chunks=chunking_shape,
                exact=True,
            )
            dataset[...] = data
        return time.perf_counter() - start

    def optimized_write_dataset(path: Path) -> float:
        start = time.perf_counter()
        with h5py.File(path, "w") as h5_file:
            write_dataset(
                h5_file,
                "/entry/data",
                data,
                compression="gzip",
            )
        return time.perf_counter() - start

    reference_times: list[float] = []
    optimized_times: list[float] = []
    for iteration in range(3):
        reference_times.append(reference_write_dataset(tmp_path / f"reference_{iteration}.h5"))
        optimized_times.append(optimized_write_dataset(tmp_path / f"optimized_{iteration}.h5"))

    reference_median = statistics.median(reference_times)
    optimized_median = statistics.median(optimized_times)

    assert optimized_median <= reference_median * 1.10


@pytest.mark.perf
def test_source_data_cache_reduces_repeated_read_cost(tmp_path: Path) -> None:
    source_file = tmp_path / "source.h5"
    data = np.random.default_rng(1).integers(0, 1000, size=(10, 256, 256), dtype=np.int32)

    with h5py.File(source_file, "w") as h5_file:
        dataset = h5_file.create_dataset("/entry/data", data=data)
        dataset.attrs["units"] = "counts"

    element = TranslationElement(destination="/output/data", source="/entry/data", data_type="int32")

    with h5py.File(source_file, "r") as h5_file:
        start = time.perf_counter()
        for _ in range(4):
            get_data_and_attributes_from_source(h5_file, element, source_data_cache=None)
        uncached_duration = time.perf_counter() - start

    with h5py.File(source_file, "r") as h5_file:
        cache: dict[tuple[str, str], tuple[object, dict[str, object]]] = {}
        start = time.perf_counter()
        for _ in range(4):
            get_data_and_attributes_from_source(h5_file, element, source_data_cache=cache)
        cached_duration = time.perf_counter() - start

    assert cached_duration <= uncached_duration * 0.75
