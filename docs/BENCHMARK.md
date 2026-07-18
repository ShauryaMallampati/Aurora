# Reference Benchmark

## Purpose

The benchmark validates matched execution, state accounting, traceable result generation, and statistical summaries. It is not a claim of real-world wildfire effectiveness or controller superiority.

## Design

- 8 scenario families
- 20 seeds
- 3 methods: no response, reactive, coordinated
- 160 matched cases per method
- 480 total episodes

Each scenario-seed case shares initial conditions, resources, terrain generation, and event-keyed environmental opportunities across methods.

## Metrics

- affected area
- naturally burned area
- suppressed area
- final active burning
- steps
- suppressions
- water used
- distance travelled

`fire_inactive_at_end` is a diagnostic, not a containment claim, because no-response fires can become inactive through fuel exhaustion.

## Statistics

The independent unit is a matched scenario-seed case. Summaries are reported overall and by scenario. Paired differences use a hierarchical bootstrap that resamples scenario families and then matched seeds within the sampled families.

An interval containing zero is not interpreted as equivalence.

## Release result

Mean affected cells:

- no response: 408.575
- reactive: 407.700
- coordinated: 407.588

Mean coordinated-minus-reactive difference: -0.113 cells; the paired interval includes zero. The benchmark therefore does not establish coordinated superiority.

## Run

```bash
aurora benchmark --output-dir benchmark_output --num-seeds 20
```

Outputs:

- `reference_benchmark.csv`
- `reference_benchmark_summary.json`
