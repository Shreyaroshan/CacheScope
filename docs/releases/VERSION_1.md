# CacheScope Version 1

Release status: completed and locally verified on 26 August 2026.

## Purpose

Version 1 establishes a correct, explainable CPU-cache simulation core before
adding visualization or integration layers.

## Included

- Direct-mapped, set-associative, and fully associative cache configurations
- LRU and FIFO replacement policies
- Write-back and write-allocate behavior
- Sequential, strided, seeded-random, and file-based traces
- Decimal and hexadecimal address parsing
- Read and write operations in trace files
- Hit, miss, eviction, and writeback counters
- Hit rate, miss rate, and AMAT calculations
- Human-readable and JSON command-line reports
- Configuration and address validation
- Python packaging and a console entry point
- GitHub Actions test workflow
- Repository guidance in `AGENTS.md`
- Sample trace and project documentation

## Verification evidence

The Version 1 verification loop completed successfully:

```text
20 automated tests passed
Editable package installation passed
CLI text output passed
CLI JSON output passed
Python compilation passed
Git whitespace validation passed
```

## Deferred from Version 1

- Batch experiment comparison
- CSV export
- Comparison charts
- Interactive Streamlit interface
- Compulsory, conflict, and capacity miss classification
- MCP integration
- A custom CacheScope skill

The first five items are planned for Version 2. MCP and a custom skill remain
conditional: they should be introduced only when the application has a stable
external tool contract or a genuinely repeated workflow.
