# CKN Daemon for Inference model instrumentation using MQTT
CKN Daemon for extracting camera traps performance information from the Edge to the Edge Hub using MQTT. It includes the following components:

- `event-subscriber`: Subscribes to event data via MQTT and processes incoming messages.
- `image-subscriber`: Subscribes to image data via MQTT and stores the incoming files.
- `CKN Daemon`:  Publishes messages based on camera trap activities.

## 📦 Features

- 🧩 **Decoupled architecture** using MQTT for scalable communication.
- 🐳 **Dockerized services** for reproducible, portable deployment.
- 📷 **Automatic handling** of image and event data.
- 📝 **CSV-driven simulation** for dynamically triggering events.

## 🚀 Getting Started

 1. Clone the repository
      ```bash
      git clone https://github.com/Data-to-Insight-Center/cyberinfrastructure-knowledge-network.git
      cd plugins/ckn-mqtt-cameratraps
      ```
2. Start the MQTT broker (Mosquitto):
   ```bash
   docker run -it -p 1883:1883 --name mosquitto eclipse-mosquitto

   ```
3. To start ckn-mqtt-cameratraps Daemon, run:
   ```bash
   docker compose -f docker-compose.yml up -d --build
   ```

4. To run event and image subscriber, Go to the central_hub directory and run:
   ```bash
   docker compose -f docker-compose.yml up -d --build
   ```
5. Send a Test event, In the test/resources directory, write STORING or DETECTION events to the example.csv file:
   ```bash
   cd test/resources
   # Edit example.csv with appropriate events
   ```

6. To stop ckn-mqtt-cameratraps  Daemon, run:
   ```bash
   docker compose -f docker-compose.yml down
   ```

---

Docker image for the CKN Daemon for Cameratraps is available at:

[D2I Docker Repository](https://hub.docker.com/repository/docker/iud2i/ckn-daemon-cameratraps/general)

The following environment variables can be set during experiment execution time.

      - DETECTED_EVENTS_FILE=/logs/detected-events.csv
      - CKN_LOG_FILE=/logs/ckn.log
      - MQTT_BROKER=host.docker.internal
      - MQTT_PORT=1883
      - EVENTS_TOPIC=cameratrap/events
      - IMAGES_TOPIC=cameratrap/images
      - IMAGE_DIR=/images
      - CAMERA_TRAP_ID=MLEDGE_1
      - CONCURRENT_WORKERS=2
      - POWER_SUMMARY_FILE=/logs/power_summary_report.json
      - POWER_SUMMARY_TOPIC=cameratrap/power_summary
      - ENABLE_POWER_MONITORING=false
      - MQTT_QOS=1
