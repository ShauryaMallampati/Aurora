# Contributing

1. Open an issue describing the scientific or software problem and a minimal reproduction.
2. Create a focused branch and add or update tests with every behavioral change.
3. Run `pytest -q` and `aurora validate` locally.
4. Regenerate benchmark outputs only when the simulator, policy, scenarios, or statistics change.
5. Document changed assumptions and update `CHANGELOG.md`.

Contributions that affect published metrics must include raw outputs, configuration, seed lists, and a justification of the statistical unit. Do not commit secrets, private location data, model caches, virtual environments, or unlicensed assets.
