# Research evidence

This page summarizes the controlled software results bundled with AURORA 0.4.0. See the [artifact guide](../artifact/README.md) for commands and expected checks.

## Why AURORA exists


A simulation can produce a reproducible-looking but invalid strategy comparison when:

- policy branching shifts a shared environmental random stream;
- later agents observe earlier agents' actions within the same nominal step;
- reset retains depleted fuel or hidden state;
- suppressed cells are counted as naturally burned;
- a final score cannot be traced to a versioned trajectory;
- benchmark values live only in an undocumented notebook.

AURORA treats these as executable systems requirements rather than documentation promises.

## Publication evidence

The bundled controlled study uses 8 scenario families and 20 seeds (160 matched cases):

| Controlled comparison | Correct design | Injected fault |
|---|---:|---:|
| Irrelevant policy draw changes trajectory | 0/160 | 160/160 with shared RNG |
| Reset changes matched rerun | 0/160 | 160/160 with retained fuel |
| Sequential timing leak in adversarial states | 0/1,000 | 1,000/1,000 |

Conflating suppressed cells with natural burnout:

- overstates natural burned area by **7.403 cells on average** (scenario-cluster bootstrap 95% interval **[4.761, 9.931]**);
- changes the reactive-benefit sign in **83/160** cases;
- changes the coordinated-benefit sign in **81/160** cases;
- changes the reactive-versus-coordinated ranking in **47/160 (29.4%)** cases.

The PettingZoo adapter and direct engine match after every no-op transition in **160/160** scenario-seed cases. These are controlled software results, not claims about defect prevalence in external simulators or real wildfire effectiveness.

## Reproduce the results

Follow the [reproducibility contract](../REPRODUCIBILITY.md) or the [artifact evaluation guide](../artifact/README.md). Expected hashes and numeric claims are versioned in [`artifact/expected/`](../artifact/expected/).

The software is associated with a JSys Tools/Benchmark submission. The anonymous manuscript is maintained separately from this public source tree.
