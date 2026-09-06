# Release archiving for JSys

JSys recommends publishing artifacts in a repository that provides a persistent identifier, such as Zenodo. A DOI is recommended for the camera-ready artifact, although the initial double-blind submission may use a private single-blind artifact package.

## Release sequence

1. Push this exact package to the public default branch.
2. Confirm public CI passes on all declared Python versions.
3. Tag the release as `v0.4.0`.
4. Publish a GitHub release from that tag.
5. Archive the tagged source through Zenodo or an equivalent preservation service.
6. Record the version-specific DOI in `CITATION.cff`, `docs/codemeta.json`, the camera-ready manuscript, and release metadata.
7. Build and inspect the camera-ready manuscript with the official `jsys_camera_ready` style.
8. Recompute release checksums and compare the archive with the tagged repository tree.

The anonymous submission manuscript must not link directly to the author-identifying public repository. Use an anonymized paper-review mirror and submit the full artifact separately through the JSys artifact portal.
