# Reuse Patterns

AURORA is intended as an experimental-control layer, not a replacement for physically calibrated fire simulators.

## 1. Controller regression testing

Record a trace for a strategy and seed, then rerun it after implementation changes. A changed digest identifies a behavioral change; the versioned frames reveal where it begins.

## 2. Fair strategy comparison

Use identical scenarios and seeds across methods. Event-keyed environmental randomness prevents unrelated policy branching from shifting environmental opportunities. Keep the no-response method so natural burnout is not mislabeled as response success.

## 3. Testing another environment's semantics

Adapt the controlled faults in `aurora.diagnostics` to a different simulator:

- insert an irrelevant policy-side random draw;
- compare reset with fresh construction;
- compare snapshot and sequential action timing;
- separate intervention states from natural terminal states.

The study design is reusable even when the wildfire-inspired engine is not.

## 4. New strategies

Implement the public `Strategist` protocol and run it through `run_strategy_episode`. This preserves scenario construction, synchronous execution, resource accounting, and result schemas without editing built-in policy code.

## 5. Multi-agent learning

Install `.[interfaces]` and use `WildfireParallelEnv`. The adapter exposes simultaneous action dictionaries, declared observation/action spaces, centralized state, deterministic seeding, and standard PettingZoo terminations/truncations.

## 6. Teaching

The codebase supports exercises on:

- state-machine design;
- common random numbers and event-keyed randomness;
- simultaneous versus sequential multi-agent semantics;
- reset invariants;
- paired and scenario-stratified analysis;
- artifact evaluation and executable paper claims.

## Not appropriate for

Do not use AURORA for real-fire forecasting, responder dispatch, aviation control, incident command, or claims about physical suppression effectiveness.
