# Analysis Report Contract v1

Phase-Space Identity Validator v0.7.0 introduces one versioned report for parsing,
dimensional analysis, tensor/index analysis, and bounded symbolic falsification.

The report is deliberately conservative. It does not claim to prove identities.

## Command line

```bash
psiv-analyze --text "nabla_x cross nabla_p = hbar^2/(2*pi)"
psiv-analyze --file examples/text/cross-gradient-zero.txt
psiv-analyze --text "nabla_x cross nabla_p = 0" --format text
```

JSON is the default output. `--compact` removes indentation. `--format text` emits a
brief human-readable rendering while preserving the same exit-code semantics.

## Top-level contract

Every JSON report contains:

- `schema_version`: report contract version, currently `1.0`;
- `tool_version`: PSIV implementation version;
- `input`: source identity and source name;
- `parse`: parser status and relation metadata;
- `ast`: canonical expression AST, or `null` when parsing fails;
- `dimensions`: dimensional-analysis section;
- `tensor_analysis`: tensor-rank and free-index section;
- `symbolic_evidence`: bounded symbolic-falsification section;
- `metadata`: declaration-metadata section;
- `diagnostics`: normalized diagnostics from all stages;
- `assumptions`: explicit analysis assumptions and limitations;
- `overall_status`: conservative aggregate result;
- `exit_code`: stable process status.

The packaged Draft 2020-12 schema is available at
`phase_space_validator/schemas/analysis-report-v1.schema.json` and through:

```python
from phase_space_validator import load_analysis_report_schema

schema = load_analysis_report_schema()
```

## Overall statuses

| Status | Meaning |
| --- | --- |
| `input_error` | The submitted text could not enter the identity-analysis pipeline. |
| `invalid` | At least one stage found a decisive error or counterexample. |
| `inconclusive` | No decisive error was found, but one or more stages could not complete. |
| `no_inconsistency_found` | Every configured stage completed without finding an inconsistency. This is not a proof. |

## Exit codes

| Code | Symbol | Meaning |
| ---: | --- | --- |
| `0` | `NO_INCONSISTENCY_FOUND` | All configured stages completed without finding an inconsistency. |
| `1` | `INVALID_IDENTITY` | A decisive structural, dimensional, tensor, or symbolic failure was found. |
| `2` | `INPUT_ERROR` | Parsing, file reading, or identity-contract input failed. |
| `3` | `ANALYSIS_INCONCLUSIVE` | The report is valid but at least one stage could not complete. |
| `4` | `INTERNAL_ERROR` | The CLI encountered an unexpected implementation failure. |

## Diagnostics

Every diagnostic has these fields:

- `code`: stable machine identifier;
- `severity`: `error`, `warning`, or `information`;
- `message`: human-readable explanation;
- `stage`: `parse`, `contract`, `dimensions`, `tensor`, `symbolic`, or `metadata`;
- `evidence`: evidence classification;
- `path`: canonical AST path when available;
- `span`: start and end offsets, lines, and columns in the submitted text.

Parser diagnostics use the parser's exact position. The v1 contract does not yet retain
per-node source ranges in the AST, so downstream diagnostics conservatively use the full
submitted identity as their source span. This avoids invented precision. More exact
AST-to-source mapping is reserved for a later schema version.

## Evidence levels

| Evidence | Meaning |
| --- | --- |
| `declared` | Directly determined from submitted syntax or declared metadata. |
| `inferred` | Derived by structural or tensor inference. |
| `computed` | Produced by deterministic dimension or symbolic computation. |
| `counterexample` | A concrete witness falsifies a universal claim. |
| `inconclusive` | The configured stage could not establish a result. |

## Partial reports

The report contract remains intact when a stage fails or cannot run. For example, a parse
error returns:

- `parse.status = "failed"`;
- `ast = null`;
- downstream sections with `status = "not_run"`;
- a position-aware parse diagnostic;
- `overall_status = "input_error"`.

A supported parse with unsupported symbolic semantics retains the successful parse,
dimension, and tensor results while marking symbolic analysis and the aggregate result as
`inconclusive`.

## Diagnostic compatibility

The report layer freezes its own v1 diagnostic identifiers through
`REPORT_DIAGNOSTIC_CODES_V1`. Diagnostics emitted by the parser, dimension engine, tensor
engine, and symbolic engine are passed through without renaming. Their module-level tests
remain the authority for those engine-specific identifiers.

A future breaking change to required fields, status semantics, diagnostic structure, or
exit-code meaning requires a new report schema version.

## Mathematical boundary

The pipeline currently uses:

- the controlled PSIV text grammar;
- the default dimension registry;
- the default three-dimensional position and momentum tensor contexts;
- a deterministic, bounded bilinear symbolic witness search.

A counterexample disproves a universal claim. Failure to find one within the configured
search space is not proof that the claim is true.
