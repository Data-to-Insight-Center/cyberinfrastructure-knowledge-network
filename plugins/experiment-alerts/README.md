# Camera Traps Experiment Monitor & Alerter

## Overview

This service monitors camera traps experiments stored in a Neo4j database. It performs two primary functions periodically:

1.  **Completion Processing:** Identifies experiments that have recently finished (based on linked `Deployment` nodes having an `end_time`), calculates their duration and accuracy, and updates the corresponding `Experiment` node properties (`end_time`, `duration`, `average_accuracy`).
2.  **Low Accuracy Alerting:** Checks for experiments whose calculated accuracy falls below a configurable threshold and sends alert messages containing experiment details (including ID, accuracy, model ID, and metadata) to a specified Kafka topic. It uses Redis to ensure alerts for a specific experiment are sent only once.

The service is designed to be run as a containerized application using Docker.

## Features

* Periodically checks for newly completed experiments based on deployment end times.
* Calculates experiment duration (`end_time` - `start_time`).
* Calculates experiment accuracy based on processed `RawImage` nodes and ground truth.
* Updates `Experiment` nodes in Neo4j with `end_time`, `duration`, and calculated `average_accuracy` (rounded percentage).
* Periodically checks for experiments with `average_accuracy` below a defined threshold.
* Uses a persistent timestamp cursor (`start_time`) stored in Redis to incrementally check for low-accuracy experiments across runs.
* Sends alerts for low-accuracy experiments to a configured Kafka topic.
* Uses a Redis set to track alerted experiments, preventing duplicate alerts.
* Configurable via environment variables (database connections, Kafka settings, thresholds, schedule).
* Includes Dockerfile and Docker Compose file for easy deployment.

## Prerequisites

* **Docker & Docker Compose:** Required to build and run the service container and its dependencies.
* **Neo4j Instance:** A running Neo4j database (version compatible with Cypher syntax used, likely 4.x or 5.x). Must be accessible from the monitor container. Ensure APOC plugin is installed for `apoc.convert.fromJsonList`.
* **Kafka Instance:** A running Kafka broker (or cluster). Must be accessible from the monitor container.
* **Redis Instance:** A running Redis server. The provided `docker-compose.yml` includes a Redis service definition.
* **Python Environment (for local development):** Python 3.x. Required packages listed in `requirements.txt`.

## Project Structure
```text
├── docker-compose.yml  # Docker Compose configuration
├── Dockerfile          # Dockerfile for the monitor service
├── requirements.txt    # Python dependencies
└── experiment_monitor.py # The main Python script
└── cypher_queries.py # Cypher queries for querying and setting neo4j graph information
└── README.md           # This file
```
**Note:** Create `requirements.txt` by running `pip freeze > requirements.txt` in your development environment after installing necessary packages (`neo4j`, `kafka-python`, `redis`, `python-dotenv`, `APScheduler`).

## Configuration

The service is configured using environment variables. You can set these in a `.env` file in the project root or directly within the `environment` section of the `ckn-exp-monitor` service in `docker-compose.yml`.

| Variable                           | Description                                                        | Default Value (in script)                | Example `docker-compose.yml` Value       |
| :--------------------------------- |:-------------------------------------------------------------------|:-----------------------------------------|:-----------------------------------------|
| `REDIS_HOST`                       | Hostname or IP of the Redis server.                                | `localhost`                              | `redis`                                  |
| `REDIS_PORT`                       | Port for the Redis server.                                         | `6379`                                   | `6379`                                   |
| `REDIS_DB`                         | Redis database number.                                             | `0`                                      | `0`                                      |
| `REDIS_ALERTED_SET_KEY`            | Redis key for the set storing IDs of already alerted experiments.  | `experiment_monitor:alerted_experiments` | `experiment_monitor:alerted_experiments` |
| `REDIS_ALERTED_TTL_SECONDS`        | Expiration time (seconds) for alerted IDs in Redis (e.g., 7 days). | `604800`                                 | `604800`                                 |
| `NEO4J_URI`                        | Bolt URI for the Neo4j database.                                   | `bolt://localhost:7687`                  | `bolt://neo4j:7687`                      |
| `NEO4J_USER`                       | Username for Neo4j authentication.                                 | `neo4j`                                  | `neo4j`                                  |
| `NEO4J_PASSWORD`                   | Password for Neo4j authentication.                                 | `password`                               | `your_strong_password`                   |
| `KAFKA_BOOTSTRAP_SERVERS`          | Comma-separated list of Kafka broker addresses.                    | `localhost:9092`                         | `kafka:9092`                             |
| `KAFKA_TOPIC`                      | Kafka topic to send low-accuracy alerts to.                        | `experiment-accuracy-alerts`             | `cameratraps-accuracy-alerts`            |
| `KAFKA_CLIENT_ID`                  | Client ID for the Kafka producer instance.                         | `experiment-monitor-accuracy`            | `experiment-accuracy-monitor`            |
| `ACCURACY_THRESHOLD`               | Accuracy percentage below which an alert is triggered.             | `80.0`                                   | `80.0`                                   |
| `PREDICTION_CONFIDENCE_THRESHOLD`  | Confidence threshold used during accuracy calculation.             | `0.2`                                    | `0.2`                                    |
| `HISTORICAL_ALERT_CHECK_RANGE` | How long ago experiments to consider for alerts (in days)          | `1`                                      | `1`                                      |
| `SCHEDULE_IN_MIN`                  | How often (in minutes) the monitoring tasks should run.            | `15` (Script default if not set)         | `15`                                     |

## How to Run (Using Docker Compose)

1.  **Clone the Repository:**
    ```bash
    git clone <your-repo-url>
    cd <your-repo-directory>
    ```
3.  **Configure Environment:**
    * Edit the `environment` section in the `docker-compose.yml` file.
4.  **Configure Docker Compose Services:**
        * Ensure Neo4j and Kafka are running externally and update the `NEO4J_URI` and `KAFKA_BOOTSTRAP_SERVERS` environment variables in the `ckn-exp-monitor` service to point to their correct addresses.
    * **Redis:** The compose file includes a Redis service definition
5.  **Build and Run:**
    ```bash
    docker-compose up --build -d
    ```
    * `--build` forces a rebuild of the monitor image if the code or Dockerfile changed.
    * `-d` runs the services in detached mode (in the background).
6.  **Check Logs:**
    ```bash
    docker-compose logs -f ckn-exp-monitor
    ```
7.  **Stop Services:**
    ```bash
    docker-compose down
    ```

## Workflow Details

The core logic resides in the `monitor.py` script (or your equivalent). The `APScheduler` runs the main task function (`run_monitoring_tasks`) at the interval defined by `SCHEDULE_IN_MIN`.

Each run executes two main steps sequentially:

1.  **`process_completed_experiments()`:**
    * Queries Neo4j for `Experiment` nodes linked to `Deployment` nodes where `d.end_time` is set, but `ex.end_time` is NULL.
    * For each found experiment:
        * Calculates accuracy using `CYPHER_CALCULATE_ACCURACY`.
        * Rounds the accuracy percentage to 2 decimal places.
        * Updates the `Experiment` node using `CYPHER_UPDATE_COMPLETED_EXPERIMENT`, setting `ex.end_time`, `ex.average_accuracy`, `ex.start_datetime`, `ex.end_datetime`, and `ex.duration`.
    * This process automatically skips experiments that have already been successfully completed because their `ex.end_time` will no longer be NULL.

2.  **`check_low_accuracy_alerts()`:**
    * Checks if required connections (Redis, Neo4j, Kafka) are available; exits if not.
    * Calculates a time threshold based on the current time minus `HISTORICAL_ALERT_CHECK_RANGE` days to define the lookback window.
    * Queries Neo4j using `CYPHER_FIND_LOW_ACCURACY_FOR_ALERT` for experiments completed *after* the calculated time threshold and with accuracy below `ACCURACY_THRESHOLD`.
    * Iterates through the found experiments:
        * Checks if the `experiment_id` exists in the Redis set (`REDIS_ALERTED_SET_KEY`) using `sismember`. If yes, skips (prevents duplicate alerts).
        * If not alerted, constructs an alert event using `create_low_accuracy_kafka_event` (including `experiment_id`, `accuracy`, `model_id`, processed `metadata`, and a `UUID`).
        * Sends the event to the configured Kafka topic (`KAFKA_TOPIC`) with error handling.
        * Adds the `experiment_id` to the Redis alerted set (`REDIS_ALERTED_SET_KEY`) using `sadd` and sets an expiration time using `expire` and `REDIS_ALERTED_TTL_SECONDS`.
    * Logs the results of the check, including the number of candidates found and the number of new alerts sent.
    
## Important Notes & Considerations

* **Data Assumptions:** The script assumes:
    * `Experiment` nodes have a `start_time` property stored as epoch milliseconds.
    * `Deployment` nodes have an `end_time` property stored as epoch milliseconds when finished.
    * `RawImage` nodes are linked via `PROCESSED_BY` to `Experiment`.
    * The `pb.scores` property on the `PROCESSED_BY` relationship is a JSON string representing a list of score objects (e.g., `[{"label": "cat", "probability": 0.95}]`).
    * `Experiment` nodes are linked via `USED` to `Model` nodes which have an `id` property.
* **Idempotency:** The alert mechanism is designed to be idempotent (sending alerts only once) due to the Redis db. 
* The completion mechanism is idempotent for successful completions (won't reprocess if `ex.end_time` is set).
