# Controlled Fault-Injection Study

This study demonstrates what happens when four experimental-control defects are deliberately introduced into the same deterministic workloads. It is **not** a claim that other simulators contain these defects or an estimate of their prevalence.

## Run

```bash
aurora ablation \
  --output-dir fault_output \
  --num-seeds 20 \
  --bootstrap-draws 2000
```

Outputs:

- `fault_ablation_cases.csv` — one row per matched scenario-seed case;
- `fault_ablation_summary.json` — counts, rates, intervals, and interpretation metadata.

## Faults

### Random-stream drift

The correct implementation derives environmental spread values from a stable event key. The injected implementation shares one stateful stream between policy-side and environmental draws. A policy no-op consumes one random value per step.

Expected release result:

- keyed environmental randomness: 0/160 divergent outcomes;
- shared global stream: 160/160 divergent outcomes.

### Reset contamination

The correct reset restores fuel, state, burn age, affected-cell history, counters, and deterministic transition behavior. The injected reset retains depleted fuel while clearing visible fire state.

Expected release result:

- complete reset: 0/160 divergent matched reruns;
- incomplete reset: 160/160 divergent matched reruns.

### Within-step information leakage

The correct coordinator computes every agent proposal from one immutable start-of-step snapshot. The injected variant lets later agents observe earlier actions.

The eight-family benchmark does not naturally expose the difference (0/160), so the artifact also includes 1,000 deliberately adversarial two-agent states. The injected sequential variant differs in 1,000/1,000 and gains exactly one extra suppression per state.

### State conflation

The injected analysis counts suppressed cells as naturally burned. Across the release workload, this:

- overstates natural burned area by 7.403 cells on average;
- changes the reactive-benefit sign in 83/160 cases;
- changes the coordinated-benefit sign in 81/160 cases;
- changes the reactive-versus-coordinated ranking in 47/160 cases.

## Statistics

Binary proportions use Wilson 95% intervals. Mean state-conflation bias uses a deterministic scenario-cluster bootstrap with 2,000 draws. Scenario families, rather than individual cells, are the outer resampling unit.

## Interpretation boundary

The study validates the framework's experimental-isolation mechanisms and quantifies the consequences of specific injected defects. It does not validate physical fire behavior, operational response effectiveness, or defect rates in third-party software.
