# Contributing

1. Open an issue describing the scientific or software problem and a minimal reproduction.
2. Create a focused branch and add or update tests with every behavioral change.
3. Run `pytest -q` and `aurora validate` locally.
4. Regenerate benchmark outputs only when the simulator, policy, scenarios, or statistics change.
5. Document changed assumptions and update [the changelog](../docs/CHANGELOG.md).

Contributions that affect published metrics must include raw outputs, configuration, seed lists, and a justification of the statistical unit. Do not commit secrets, private location data, model caches, virtual environments, or unlicensed assets.

## Support

Use the GitHub issue tracker for reproducible bugs, documentation gaps, or feature proposals. Include the AURORA version, Python version, operating system, command, traceback, and smallest scenario that reproduces the issue. This project does not provide operational wildfire advice or emergency-response support.

## Review process

AURORA currently uses a maintainer-led model. The lead maintainer reviews changes for scientific validity, test coverage, licensing, and scope. Major changes to simulator semantics, metrics, or public APIs require an issue, a documented rationale, regression tests, and an entry in [the changelog](../docs/CHANGELOG.md). Governance should be revisited if external maintainers join.
