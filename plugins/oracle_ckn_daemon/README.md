# CKN Daemon - Tapis Camera Traps
CKN Daemon for extracting camera traps performance information from the Edge to the Cloud. 

### Usage

1. Follow the steps [here](../../README.md) to start CKN.

2. To Build CKN-Oracle Daemon, run:
   ```bash
   docker compose -f plugins/oracle_ckn_daemon/docker-compose.yml up -d --build
   ```

3. To produce events, run:
   ```bash
   docker exec ckn-oracle-daemon touch /oracle_logs/image_mapping_final.json
   ```

4. Access the [Dashboard](http://localhost:8502/Camera_Traps) to view streamed data or Check the [local Neo4j instance](http://localhost:7474/browser/) with username `neo4j` and password `PWD_HERE`.

5. Follow the steps [here](../../README.md) to stop CKN.

---

Docker image for the CKN Daemon for Cameratraps is available at:

[D2I Docker Repository](https://hub.docker.com/repository/docker/iud2i/ckn-daemon-cameratraps/general)

The following environment variables can be set during experiment execution time.

      - ORACLE_CSV_PATH=/oracle_logs/image_mapping_final.json
      - CKN_LOG_FILE=/oracle_logs/ckn.log
      - CKN_KAFKA_BROKER=localhost:9092
      - CKN_KAFKA_TOPIC=oracle-events
      - CAMERA_TRAPS_DEVICE_ID=device_1
      - USER_ID=swithana
      - EXPERIMENT_ID=experiment_1
      - EXPERIMENT_END_SIGNAL = 6e153711-9823-4ee6-b608-58e2e801db51
      - POWER_SUMMARY_FILE=/power_logs/power_summary_report.json
      - POWER_SUMMARY_TOPIC=cameratraps-power-summary
      - POWER_SUMMARY_TIMOUT=10
      - POWER_SUMMARY_MAX_TRIES=5
