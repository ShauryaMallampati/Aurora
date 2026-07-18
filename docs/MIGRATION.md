# Migration from the historical repository

The historical AURORA repository combined a web application, training scripts, checkpoints, notebooks, and experimental claims. Version 0.4.0 extracts a small verified Python research-software core.

There is no guaranteed API compatibility with historical `env/`, training, LLM, or web-dashboard modules. Historical checkpoints are not part of this release and are not evidence for the current paper. Migrate new experiments by expressing scenarios through `Scenario`, controllers through the strategy interface or `run_episode`, and outputs through `EpisodeResult` and trace JSON.
