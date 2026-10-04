# CacheScope

CacheScope is an explainable CPU-cache simulator and interactive analysis app
written in Python. It models
byte-addressed memory accesses and compares how cache geometry, access patterns,
and LRU/FIFO replacement affect hit rate, miss rate, evictions, writebacks, and
average memory access time (AMAT).

## Current capabilities

- Direct-mapped, set-associative, and fully associative configurations
- LRU and FIFO replacement policies
- Write-back, write-allocate writes
- Sequential, strided, and seeded-random synthetic traces
- Text-file traces with decimal or hexadecimal addresses
- Text and JSON reports
- Compulsory, conflict, and capacity miss classification
- Batch comparison across cache sizes, block sizes, associativities, and policies
- CSV experiment export
- Interactive Streamlit charts and downloadable results
- Deterministic unit tests for address mapping, replacement, dirty evictions,
  trace parsing, and metrics

## Install

CacheScope requires Python 3.11 or newer.

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev,app]"
```

## Quick start

Run 1,000 sequential byte accesses through a 1 KiB direct-mapped cache:

```bash
python -m cachescope \
  --cache-size 1024 \
  --block-size 64 \
  --associativity 1 \
  --policy lru \
  --pattern sequential \
  --count 1000
```

Compare a strided pattern with a four-way FIFO cache:

```bash
python -m cachescope \
  --cache-size 4096 \
  --block-size 64 \
  --associativity 4 \
  --policy fifo \
  --pattern strided \
  --stride 256 \
  --count 500
```

Run a trace file and request machine-readable output:

```bash
python -m cachescope --trace examples/sample.trace --format json
```

Compare several configurations over exactly the same trace and export the
results:

```bash
python -m cachescope \
  --pattern strided \
  --count 1000 \
  --stride 64 \
  --compare-cache-sizes 256,512,1024,2048 \
  --compare-block-sizes 32,64 \
  --compare-associativities 1,2,4 \
  --compare-policies lru,fifo \
  --csv comparison.csv
```

## Interactive application

Start the Streamlit interface:

```bash
streamlit run app.py
```

The app provides:

- Synthetic or uploaded traces
- Configurable cache geometry and timing
- Hit-rate, miss-rate, AMAT, and writeback summary cards
- Compulsory, conflict, and capacity miss charts
- Multi-configuration hit-rate and AMAT comparisons
- A complete experiment table and CSV download

Trace lines use either `ADDRESS` or `R|W ADDRESS`:

```text
R 0x0000
W 64
128
```

Blank lines, commas, and comments beginning with `#` are supported.

## Cache model

For every byte address, CacheScope computes:

```text
block = address // block_size
set   = block % number_of_sets
tag   = block // number_of_sets
```

The number of sets is:

```text
number_of_sets = cache_size // (block_size * associativity)
```

AMAT uses:

```text
AMAT = hit_time + miss_rate * miss_penalty
```

`miss_penalty` is treated as additional time paid after the cache lookup.

### 3C miss classification

- **Compulsory:** the referenced block has never appeared before.
- **Conflict:** the block would still be present in an equally sized fully
  associative LRU cache, so set placement caused the miss.
- **Capacity:** even the fully associative shadow cache would have evicted the
  block.

The shadow cache is used only for classification; it does not change the
configured cache's replacement behavior.

## Development and verification loop

Each change should follow this loop:

1. Define an observable behavior and a small acceptance test.
2. Implement the smallest coherent change.
3. Run `python -m pytest`.
4. Exercise the CLI on a hand-checkable trace.
5. Inspect failures, correct the cause, and repeat until both checks pass.

Run the full local verification:

```bash
python -m pytest
python -m cachescope --help
python -m cachescope --trace examples/sample.trace
streamlit run app.py
```

## Next milestones

1. Add per-access cache-state visualization.
2. Add experiment presets and saved sessions.
3. Import larger real-world memory traces.
4. Add benchmark reports suitable for project presentations.
5. Evaluate whether a stable CacheScope tool API merits MCP integration.

MCP integration and a reusable CacheScope skill remain deliberately postponed
until the simulator interface and repeated analysis workflow become stable.

See the [Version 1 notes](docs/releases/VERSION_1.md) for the verified baseline
before the analysis app was added, and the [Version 2 notes](docs/releases/VERSION_2.md)
for the interactive analysis release.
