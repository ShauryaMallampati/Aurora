# Scenario reference

The reference suite contains eight abstract scenario families:

| Scenario | Purpose |
|---|---|
| `calm_humid` | lower-spread baseline |
| `warm_crosswind` | moderate directional spread |
| `hot_dry` | hotter and drier conditions |
| `strong_northwind` | stronger directional pressure |
| `constrained_water` | reduced responder capacity |
| `dual_front` | multiple simultaneous ignition clusters |
| `single_responder` | limited team size |
| `large_grid_high_wind` | larger rectangular domain and high wind |

A `Scenario` validates dimensions, probabilities, resource values, weather bounds, and ignition coordinates. Ignitions must be in bounds and cannot be duplicated. Terrain generation is deterministic for a given scenario and seed.

These profiles are not calibrated representations of named real fires. They are regression and experimental-plumbing cases. New scientific studies should define domain-justified scenarios, preserve manifests, and report sensitivity to scenario assumptions.
