## [v0.2.0] - 2025-06-10

### Added
- **Plugins:**
  - **ckn-mqtt-cameratraps**: MQTT-based camera trap ingestion plugin for edge event and image streaming. Enables scalable, decoupled data collection from edge devices. _(ICICLE)_
  - **experiment-alerts**: Automated experiment monitoring and alerting plugin. Detects low-accuracy experiments and publishes alerts to Kafka for downstream workflows. _(ICICLE)_
  - **ckn_inference_daemon**: Edge inference research plugin implementing FastAPI-based serving and model management. Intended for prototyping and experimentation.  _(Research / Experimental)_
- **Documentation:**
  - Added comprehensive documentation for new plugins and event topics (`docs/topics.md`), plugin usage, and deployment.
- **Database:**
  - Introduced additional Neo4j indexes to improve query and analytics performance.

### Fixed
  - Improved experiment completion detection and ensured robust accuracy reporting in monitoring and alerting workflows.
  - Minor bug fixes, typo corrections, and formatting improvements throughout documentation and example configs.
