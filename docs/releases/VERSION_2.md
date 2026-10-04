# CacheScope Version 2

Release status: implemented and locally verified on 26 August 2026.

## Added since Version 1

- Compulsory, conflict, and capacity miss classification using an equally sized
  fully associative LRU shadow cache
- Reusable batch-experiment API
- Comparison across cache sizes, block sizes, associativities, and LRU/FIFO
- CSV serialization and file export
- CLI comparison tables and CSV output
- Interactive Streamlit application
- Synthetic and uploaded trace support in the application
- Hit-rate, miss-rate, AMAT, and writeback metric cards
- 3C miss bar chart
- Hit-rate comparison chart
- AMAT-versus-cache-size chart
- Experiment table and downloadable CSV
- Streamlit workflow tests

## Design boundaries

- Simulation logic remains independent of Streamlit, Pandas, and Plotly.
- Every comparison configuration receives the same materialized trace.
- Invalid cache geometries are skipped during a sweep.
- The 3C shadow cache classifies misses without affecting real cache state.
- Random traces remain reproducible through explicit seeds.

## Verification

Version 2 is accepted only when the unit suite, CLI comparison, CSV export,
Python compilation, and both Streamlit workflows pass.

## Still deferred

- MCP integration
- A custom CacheScope skill
- Real hardware trace integration
- Per-access animated cache-state visualization
