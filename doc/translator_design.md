# Translator Design and Performance Notes

## Runtime pipeline

The translator executes the following phases in order:

1. Optional template copy.
2. `tree_copy` operations.
3. `data_copy` element processing.
4. Attribute updates.
5. Pruning (`prune_list`).
6. Link creation (`link_list`).

This order is preserved to maintain compatibility with existing configurations.

## Performance-oriented implementation choices

### 1. Single-write dataset updates

`write_dataset()` now avoids the previous double-write behavior for fresh datasets.

- Previous behavior: `require_dataset(..., data=...)` followed by `dset[...] = data`.
- Current behavior: one physical write when creating a dataset.
- Existing compatible datasets are updated in place when possible.
- Incompatible datasets are recreated.

### 2. Source file handle reuse

During translation and link phases, source HDF5 files are opened lazily and reused through a per-phase handle cache.

- Reduces repeated `h5py.File(...)` open/close overhead.
- Preserves processing order and output semantics.

### 3. Alternate source path resolution cache

`alternate_source_file` glob/path resolutions are cached per translation run.

- Avoids repeated filesystem glob operations for identical patterns.
- Applies across `data_copy` and `link_list` phases.

### 4. Optional source dataset cache

A guarded in-memory source dataset cache is available through:

- `HDF5TRANSLATOR_ENABLE_SOURCE_CACHE=1`

Behavior:

- Cache key: `(source_filename, source_dataset_path)`
- Cached arrays are copied on retrieval to avoid mutation side-effects.
- Disabled by default to preserve memory profile unless explicitly requested.

### 5. Copy-minimizing data adjustments

- Datatype conversion avoids copies when dtype already matches.
- Minimum dimensionality adjustment avoids no-op allocations and uses reshape-based views for ndarray inputs.

### 6. Logging cost reduction

Hot-path logging now avoids eager array stringification and logs compact payload summaries (shape/dtype/type).

## Testing strategy

### Unit tests

- `write_dataset` create/update/replace behavior.
- source data + attribute retrieval cache behavior.
- dimensionality and datatype conversion no-op/copy behavior.

### Integration tests

- Full translator pipeline validation: copy, transform, attributes, prune, links.
- Alternate source resolution cache behavior.

### Performance tests (`pytest -m perf`)

- Dataset write micro-benchmark against legacy reference implementation.
- Repeated source-read benchmark with and without source data cache.

Performance tests are configured as a soft gate in `tox` (`perf` env with `ignore_outcome=true`).
