from __future__ import annotations

from pathlib import Path

import h5py
import numpy as np
import yaml

import HDF5Translator.translator as translator_module


def _write_yaml(path: Path, payload: dict) -> None:
    with path.open("w", encoding="utf-8") as handle:
        yaml.safe_dump(payload, handle)


def test_translate_runs_full_pipeline(tmp_path: Path) -> None:
    source_file = tmp_path / "source.h5"
    output_file = tmp_path / "output.h5"
    config_file = tmp_path / "config.yaml"

    with h5py.File(source_file, "w") as h5_file:
        entry = h5_file.require_group("/entry")
        entry.create_dataset("value", data=np.array([42], dtype=np.int32))
        entry.create_dataset("matrix", data=np.arange(4, dtype=np.int32).reshape(2, 2))

        copied_group = entry.require_group("copied")
        copied_group.create_dataset("keep_me", data=np.array([1], dtype=np.int32))
        copied_group.create_dataset("remove_me", data=np.array([2], dtype=np.int32))

    config = {
        "tree_copy": [{"source": "/entry/copied", "destination": "/entry1/"}],
        "data_copy": [
            {
                "source": "/entry/value",
                "destination": "/entry1/value",
                "data_type": "int32",
                "minimum_dimensionality": 1,
            },
            {
                "source": "/entry/matrix",
                "destination": "/entry1/data",
                "data_type": "int32",
                "minimum_dimensionality": 3,
                "transformation": "lambda x: x + 1",
                "compression": "gzip",
            },
        ],
        "attributes": {
            "/entry1": {
                "NX_class": "NXentry",
                "default": "data",
            }
        },
        "prune_list": ["/entry1/copied/remove_me"],
        "link_list": [
            {
                "source_path": "/entry1/value",
                "destination_path": "/entry1/value_link",
                "internal_or_external": "internal",
                "soft_or_hard_link": "soft",
            }
        ],
    }
    _write_yaml(config_file, config)

    translator_module.translate(
        source_file=source_file,
        dest_file=output_file,
        config_file=config_file,
        template_file=None,
        overwrite=True,
    )

    with h5py.File(output_file, "r") as h5_file:
        assert np.array_equal(h5_file["/entry1/value"][()], np.array([42], dtype=np.int32))
        assert h5_file["/entry1/data"].shape == (1, 2, 2)
        assert np.array_equal(h5_file["/entry1/data"][()], np.arange(4, dtype=np.int32).reshape(1, 2, 2) + 1)
        assert h5_file["/entry1"].attrs["NX_class"] == "NXentry"

        assert "/entry1/copied/keep_me" in h5_file
        assert "/entry1/copied/remove_me" not in h5_file

        link = h5_file.get("/entry1/value_link", getlink=True)
        assert isinstance(link, h5py.SoftLink)
        assert link.path == "/entry1/value"


def test_translate_caches_alternate_source_resolution(tmp_path: Path, monkeypatch) -> None:
    source_file = tmp_path / "source.h5"
    alternate_source_file = tmp_path / "alternate.h5"
    output_file = tmp_path / "output.h5"
    config_file = tmp_path / "config.yaml"

    with h5py.File(source_file, "w") as h5_file:
        h5_file.create_dataset("/entry/unused", data=np.array([0], dtype=np.int32))

    with h5py.File(alternate_source_file, "w") as h5_file:
        h5_file.create_dataset("/entry/value", data=np.array([5], dtype=np.int32))
        h5_file.create_dataset("/entry/link_source", data=np.array([7], dtype=np.int32))

    alternate_pattern = "alternate*.h5"
    config = {
        "tree_copy": [],
        "data_copy": [
            {
                "source": "/entry/value",
                "destination": "/entry1/value_one",
                "data_type": "int32",
                "alternate_source_file": alternate_pattern,
            },
            {
                "source": "/entry/value",
                "destination": "/entry1/value_two",
                "data_type": "int32",
                "alternate_source_file": alternate_pattern,
            },
        ],
        "attributes": {},
        "prune_list": [],
        "link_list": [
            {
                "source_path": "/entry/link_source",
                "destination_path": "/entry1/external_link",
                "internal_or_external": "external",
                "soft_or_hard_link": "soft",
                "alternate_source_file": alternate_pattern,
            }
        ],
    }
    _write_yaml(config_file, config)

    calls: list[str] = []

    def fake_resolve(pattern: str | Path, dest: Path) -> Path | None:
        del dest
        calls.append(Path(pattern).as_posix())
        return alternate_source_file

    monkeypatch.setattr(translator_module, "resolve_alternate_sourcefile", fake_resolve)

    translator_module.translate(
        source_file=source_file,
        dest_file=output_file,
        config_file=config_file,
        template_file=None,
        overwrite=True,
    )

    assert calls == [alternate_pattern]

    with h5py.File(output_file, "r") as h5_file:
        assert np.array_equal(h5_file["/entry1/value_one"][()], np.array([5], dtype=np.int32))
        assert np.array_equal(h5_file["/entry1/value_two"][()], np.array([5], dtype=np.int32))
        link = h5_file.get("/entry1/external_link", getlink=True)
        assert isinstance(link, h5py.ExternalLink)
