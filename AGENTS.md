# CacheScope repository instructions

## Product goal

CacheScope is an educational CPU-cache simulator. Prefer correctness, deterministic
experiments, and explainable output over premature optimization.

## Development rules

- Support Python 3.11 or newer.
- Keep simulator logic independent from the CLI and any future UI.
- Represent addresses as non-negative byte addresses.
- Validate cache configurations before simulation.
- Preserve deterministic behavior in tests and generated random traces.
- Add or update tests whenever cache semantics change.
- Never weaken a test or alter cache semantics solely to make a check pass.

## Cache semantics

- Cache size and block size are measured in bytes.
- Associativity is the number of lines per set.
- Address mapping uses `block = address // block_size`,
  `set = block % number_of_sets`, and `tag = block // number_of_sets`.
- Writes use write-allocate and write-back behavior.
- AMAT is `hit_time + miss_rate * miss_penalty`.

## Verification

Run these commands before considering work complete:

```bash
python -m pytest
python -m cachescope --help
python -m streamlit run app.py --server.headless true
```
