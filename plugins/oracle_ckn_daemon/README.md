# CKN Daemon for TAPIS Camera Traps Application
CKN Daemon for extracting camera traps performance information from the Edge to the Cloud. 

This daemon includes both Oracle event processing and experiment metrics computation in a single integrated service:
- **Oracle CKN Daemon**: Processes image events and sends them to Kafka
- **Experiment Metrics Service**: Runs in a background thread, periodically computing comprehensive object detection metrics and updating Experiment nodes in Neo4j 

### Usage

1. Go to the root directory and run `make up`. Refer [here](../../README.md) for more details.

2. To start the integrated CKN-Oracle Daemon (includes experiment metrics service), run:
   ```bash
   docker compose -f docker-compose.yml up -d --build
   ```
   
   This will start one container:
   - `ckn-oracle-daemon`: Processes image events and runs experiment metrics computation in background

3. To produce events, run:
   ```bash
   docker exec ckn-oracle-daemon touch /oracle_logs/image_mapping_final.json
   ```

4. View streamed data on the [CKN dashboard](http://localhost:8502/Camera_Traps) or via the [Neo4j Browser](http://localhost:7474/browser/). Use `neo4j` as the username and replace `PWD_HERE` with your password, then run:
   ```cypher
   MATCH (n) RETURN n
   ```

5. To stop the integrated service, run:
   ```bash
   docker compose -f docker-compose.yml down
   ```
   Follow the steps [here](../../README.md) to stop CKN.

---

Docker image for the CKN Daemon for Cameratraps is available at:

[D2I Docker Repository](https://hub.docker.com/repository/docker/iud2i/ckn-daemon-cameratraps/general)

### Environment Variables

The following environment variables can be set during experiment execution time:

**Oracle CKN Daemon:**
- `ORACLE_CSV_PATH=/oracle_logs/image_mapping_final.json`
- `CKN_LOG_FILE=/oracle_logs/ckn.log`
- `CKN_KAFKA_BROKER=localhost:9092`
- `CKN_KAFKA_TOPIC=oracle-events`
- `CAMERA_TRAPS_DEVICE_ID=device_1`
- `USER_ID=swithana`
- `EXPERIMENT_ID=experiment_1`
- `EXPERIMENT_END_SIGNAL=6e153711-9823-4ee6-b608-58e2e801db51`
- `POWER_SUMMARY_FILE=/power_logs/power_summary_report.json`
- `POWER_SUMMARY_TOPIC=cameratraps-power-summary`
- `POWER_SUMMARY_TIMOUT=10`
- `POWER_SUMMARY_MAX_TRIES=5`


### Experiment Metrics

The integrated Experiment Metrics Service automatically computes and updates Experiment nodes with comprehensive object detection metrics every 5 minutes:

- `total_images`: Number of images processed
- `mean_iou`: Mean Intersection over Union (using confidence scores as proxy)
- `total_ground_truth_objects`: Number of ground truth objects
- `total_predictions`: Total number of predictions made
- `false_positives`: Number of false positive predictions
- `true_positives`: Number of true positive predictions
- `false_negatives`: Number of false negative predictions
- `precision`: Precision score
- `recall`: Recall score
- `f1_score`: F1 score
- `map_50`: Mean Average Precision at IoU=0.5
- `map_50_95`: Mean Average Precision averaged over IoU thresholds 0.5-0.95
