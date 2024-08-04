# CKN Daemon - Tapis Camera Traps
CKN Daemon for extracting camera traps performance information from the Edge to the Cloud. 

### How to run

##### Using Docker image:
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

CKN Daemon reads the log files through volume mounting as follows:
```
volumes:
- /camera-traps/releases/0.3.3/oracle_plugin_dir:/oracle_logs:r
- /camera-traps/releases/0.3.3/power_output_dir:/power_logs:r
```


##### Using docker compose:
1. Set the environment variables on the docker-compose file
2. Run the following command to start up the container with the env variables
```shell
docker-compose up -d
```
3. This should start the container and read the oracle-plugin output file and send the events to a hosted broker.
