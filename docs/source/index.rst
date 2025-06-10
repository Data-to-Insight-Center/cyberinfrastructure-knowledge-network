.. raw:: html

   <div align="center">

.. raw:: html

   <h1>Cyberinfrastructure Knowledge Network</h1>

.. image:: https://img.shields.io/badge/docs-latest-blue.svg
   :target: https://cyberinfrastructure-knowledge-network.readthedocs.io/en/latest/
   :alt: Documentation Status

.. image:: https://github.com/Data-to-Insight-Center/cyberinfrastructure-knowledge-network/actions/workflows/ci.yml/badge.svg
   :target: https://github.com/Data-to-Insight-Center/cyberinfrastructure-knowledge-network/actions
   :alt: Build Status

.. image:: https://img.shields.io/badge/License-BSD%203--Clause-blue.svg
   :target: https://opensource.org/licenses/BSD-3-Clause
   :alt: License

.. raw:: html

   </div>

The **Cyberinfrastructure Knowledge Network (CKN)** is an extensible and portable distributed framework designed to optimize AI at the edge—particularly in dynamic environments where workloads may change suddenly (for example, in response to motion detection). CKN enhances edge–cloud collaboration by using historical data, graph representations, and adaptable deployment of AI models to satisfy changing accuracy–and–latency demands on edge devices.

*Tag: CI4AI, Software, PADI*

===============================================================================

Explanation
-----------

CKN facilitates seamless connectivity between edge devices and the cloud through event streaming, enabling real-time data capture and processing. By leveraging event-stream processing, it captures, aggregates, and stores historical system-performance data in a knowledge graph that models application behaviour and guides model selection and deployment at the edge.

CKN comprises several core components:

- **CKN Daemon** – A lightweight service that resides on each edge server. It manages communication with edge devices, handles requests, captures performance data, and deploys AI models as needed. The daemon connects with the cloud-based CKN system via a pub/sub system, capturing real-time events from edge devices (model usage, resource consumption, prediction accuracy, latency, and more).
- **Event Streaming & Processing** – Stream-processing techniques (for example, tumbling windows) aggregate events and generate real-time alerts from edge-device streams.
- **Knowledge Graph** – A Neo4j graph database that stores historical and provenance information about applications, models, and edge events. This comprehensive view of the system enables CKN to track model usage and analyse performance over time.

The primary objective of CKN is to provide a robust framework for optimising AI-application deployment and resource allocation at the edge. Leveraging real-time event streaming and knowledge graphs, CKN efficiently handles AI workloads, adapts to changing requirements, and supports scalable edge–cloud collaboration.

Refer to this paper for more information: https://ieeexplore.ieee.org/document/10254827

===============================================================================

How-To Guide
------------

See the full documentation at https://cyberinfrastructure-knowledge-network.readthedocs.io/en/latest/ for detailed instructions on creating custom plug-ins and streaming events to the knowledge graph.

Prerequisites
~~~~~~~~~~~~~

- Docker and Docker Compose installed and running.
- Open network access to the following ports:
  - ``7474`` (Neo4j Web UI)
  - ``7687`` (Neo4j Bolt)
  - ``2181`` (ZooKeeper)
  - ``9092`` (Kafka Broker)
  - ``8083`` (Kafka Connect)
  - ``8502`` (CKN dashboard)

Quick-Start
~~~~~~~~~~~

Clone the repository and start services
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: bash

   git clone https://github.com/Data-to-Insight-Center/cyberinfrastructure-knowledge-network.git
   make up

After setup completes, verify that all modules are running:

.. code-block:: bash

   docker compose ps

Stream an example camera-trap event
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: bash

   docker compose -f examples/docker-compose.yml up -d --build

View the streamed data on the CKN dashboard at http://localhost:8502/Camera_Traps or open the Neo4j browser at http://localhost:7474/browser/ and run:

.. code-block:: cypher

   MATCH (n) RETURN n

To shut down services:

.. code-block:: bash

   make down
   docker compose -f examples/docker-compose.yml down

===============================================================================

Topics & Event Types
--------------------

CKN Topic Configuration
^^^^^^^^^^^^^^^^^^^^^^^

.. list-table::
   :header-rows: 1
   :widths: 25 10 20 45

   * - Topic Name               - System  - Plugin Directory       - Purpose
   * - oracle-events            - Kafka   - oracle_ckn_daemon     - Inference data from camera-traps application
   * - cameratraps-power-summary- Kafka  - oracle_ckn_daemon     - Aggregated power summary from camera-traps application
   * - cameratraps-accuracy-alerts- Kafka- experiment-alerts     - Alerts for experiments with accuracy below threshold
   * - deployment_info          - Kafka   - ckn_inference_daemon  - Per-inference result & resource metrics
   * - start_deployment         - Kafka   - ckn_inference_daemon  - Marks start of a deployment run
   * - end_deployment           - Kafka   - ckn_inference_daemon  - Marks graceful or abnormal termination
   * - cameratrap/events        - MQTT    - ckn-mqtt-cameratraps  - Publishes camera trap event data
   * - cameratrap/images        - MQTT    - ckn-mqtt-cameratraps  - Publishes image data captured by camera traps
   * - cameratrap/power_summary - MQTT    - ckn-mqtt-cameratraps  - Publishes aggregated power usage summaries

cameratraps-power-summary
^^^^^^^^^^^^^^^^^^^^^^^^^^

.. list-table::
   :header-rows: 1
   :widths: 30 45 15

   * - Field                                      - Description                                   - Example
   * - experiment_id                             - Identifier for the experiment                 - googlenet-iu-animal-classification
   * - image_generating_plugin_cpu_power_consumption
                                                 - CPU power usage for image-generating plugin   - 2.63
   * - image_generating_plugin_gpu_power_consumption
                                                 - GPU power usage for image-generating plugin   - 0.076
   * - power_monitor_plugin_cpu_power_consumption
                                                 - CPU power usage for power-monitor plugin      - 2.59
   * - power_monitor_plugin_gpu_power_consumption
                                                 - GPU power usage for power-monitor plugin      - 0.071
   * - image_scoring_plugin_cpu_power_consumption
                                                 - CPU power usage for image-scoring plugin      - 2.57
   * - image_scoring_plugin_gpu_power_consumption
                                                 - GPU power usage for image-scoring plugin      - 0.082
   * - total_cpu_power_consumption               - Total CPU power usage across all plugins      - 7.79
   * - total_gpu_power_consumption               - Total GPU power usage across all plugins      - 0.229

oracle-events
^^^^^^^^^^^^^

.. list-table::
   :header-rows: 1
   :widths: 25 45 15

   * - Field                      - Description                                   - Example
   * - uuid                       - Unique identifier for the image/event         - 67b83445-2622-50a3-be3b-f7030259576e
   * - image_count                - Sequence number of the image                  - 2
   * - image_name                 - File path or name of the image                - /example_images/baby-red-fox.jpg
   * - ground_truth               - Expected (actual) label for the image         - animal
   * - model_id                   - Model identifier used for inference           - 0
   * - image_receiving_timestamp  - Timestamp when the image was received         - 2024-08-06T20:46:14.130079257+00:00
   * - image_scoring_timestamp    - Timestamp when inference was completed        - 2024-08-06T20:34:47.430327
   * - image_store_delete_time    - Time the image data was removed from storage  - 2024-08-06T20:34:47.438858883+00:00
   * - image_decision             - Action taken on the image (e.g., Save/Delete) - Save
   * - label                      - Predicted label with highest probability      - animal
   * - probability                - Highest confidence score                      - 0.924
   * - flattened_scores           - JSON-stringified array of label–score pairs   - [{"label":"animal","probability":0.924}]
   * - device_id                  - The device that generated the event           - iu-edge-server-cib
   * - experiment_id              - Identifier for the experiment                 - googlenet-iu-animal-classification
   * - user_id                    - User or owner of the experiment               - jstubbs

deployment_info
^^^^^^^^^^^^^^^

.. list-table::
   :header-rows: 1
   :widths: 25 45 15

   * - Field         - Description                                    - Example
   * - timestamp     - Time when the event was recorded               - 2025-01-29T13:40:11.649Z
   * - server_id     - Unique identifier of the server                - edge-server-01
   * - model_id      - Identifier of the deployed model               - resnet152-model
   * - deployment_id - Unique deployment instance ID                  - 123e4567-e89b-12d3-a456-426614174001
   * - service_id    - Name of the deployed service                   - imagenet_image_classification
   * - device_id     - Identifier of the device running the service   - camera-trap-device
   * - ground_truth  - Expected outcome for validation                - cat
   * - req_delay     - Required delay constraint for the inference    - 0.05
   * - req_acc       - Required accuracy constraint                   - 0.90
   * - prediction    - Output prediction result                       - dog
   * - compute_time  - Time taken to compute the prediction           - 1.605
   * - probability   - Confidence score of the prediction             - 0.92956
   * - accuracy      - Binary indicator (0 or 1) for correct pred.    - 1
   * - total_qoe     - Overall Quality of Experience score            - 0.431
   * - accuracy_qoe  - QoE score based on accuracy                    - 0.837
   * - delay_qoe     - QoE score based on delay                       - 0.025
   * - cpu_power     - CPU power consumption in watts                 - 0.0
   * - gpu_power     - GPU power consumption in watts                 - 0.0
   * - total_power   - Total system power consumption in watts        - 0.0

start_deployment
^^^^^^^^^^^^^^^^

.. list-table::
   :header-rows: 1
   :widths: 25 45 15

   * - Field         - Description                                   - Example
   * - deployment_id - Unique ID of the deployment instance             - 123e4567-e89b-12d3-a456-426614174001
   * - server_id     - Unique identifier of the server                  - edge-server-01
   * - service_id    - Name of the deployed service                     - imagenet_image_classification
   * - device_id     - Identifier of the device initiating              - camera-trap-device
   * - model_id      - Identifier of the model being deployed           - resnet152-model
   * - status        - Indicates the current state                      - RUNNING
   * - start_time    - Timestamp of deployment initiation               - 2025-01-29T13:08:48.401Z

end_deployment
^^^^^^^^^^^^^^^^

.. list-table::
   :header-rows: 1
   :widths: 25 45 15

   * - Field         - Description                                 - Example
   * - deployment_id - Unique ID of the deployment instance        - 123e4567-e89b-12d3-a456-426614174001
   * - status        - Indicates the deployment has stopped        - STOPPED
   * - end_time      - Timestamp of deployment termination         - 2025-01-29T13:20:10.100Z

===============================================================================

Tutorial: Create a Custom CKN Plug-in
-------------------------------------

Create a CKN Topic
^^^^^^^^^^^^^^^^^^

We will create a CKN topic named ``temperature-sensor-data`` to store temperature events. The CKN topics and their details are mentioned in ``docs/topics.md``.

Update ``docker-compose.yml`` and add:

.. code-block:: yaml

   services:
     broker:
       environment:
         KAFKA_CREATE_TOPICS: "temperature-sensor-data:1:1"

Apply the change:

.. code-block:: bash

   make down
   make up

Produce Events
^^^^^^^^^^^^^^

Create ``produce_temperature_events.py``:

.. code-block:: python

   from confluent_kafka import Producer
   import json, time

   producer = Producer({"bootstrap.servers": "localhost:9092"})

   try:
       for i in range(10):
           for sensor_id in ["sensor_1", "sensor_2", "sensor_3"]:
               event = {
                   "sensor_id": sensor_id,
                   "temperature": round(20 + 10 * (0.5 - time.time() % 1), 2),
                   "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
               }
               producer.produce("temperature-sensor-data", key=sensor_id, value=json.dumps(event))
           producer.flush()
           time.sleep(1)
       print("Produced 10 events successfully.")
   except Exception as e:
       print(f"An error occurred: {e}")

Open a shell inside the broker container and start the consumer:

.. code-block:: bash

   kafka-console-consumer --bootstrap-server localhost:9092 --topic temperature-sensor-data --from-beginning

Connect to a Data Sink
^^^^^^^^^^^^^^^^^^^^^

Create ``ckn_broker/connectors/neo4jsink-temperature-connector.json``:

.. code-block:: json

   {
     "name": "Neo4jSinkConnectorTemperature",
     "config": {
       "topics": "temperature-sensor-data",
       "connector.class": "streams.kafka.connect.sink.Neo4jSinkConnector",
       "errors.retry.timeout": "-1",
       "errors.retry.delay.max.ms": "1000",
       "errors.tolerance": "all",
       "errors.log.enable": true,
       "errors.log.include.messages": true,
       "key.converter": "org.apache.kafka.connect.storage.StringConverter",
       "key.converter.schemas.enable": false,
       "value.converter": "org.apache.kafka.connect.json.JsonConverter",
       "value.converter.schemas.enable": false,
       "neo4j.server.uri": "bolt://neo4j:7687",
       "neo4j.authentication.basic.username": "neo4j",
       "neo4j.authentication.basic.password": "PWD_HERE",
       "neo4j.topic.cypher.temperature-sensor-data": "MERGE (sensor:Sensor {id: event.sensor_id}) MERGE (reading:TemperatureReading {timestamp: datetime(event.timestamp)}) SET reading.temperature = event.temperature MERGE (sensor)-[:REPORTED]->(reading)"
     }
   }

Register the connector
^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: bash

   curl -X POST -H "Content-Type: application/json" --data @/app/neo4jsink-temperature-connector.json http://localhost:8083/connectors

Restart CKN and run the producer again:

.. code-block:: bash

   make down
   make up

   python produce_temperature_events.py

Open the Neo4j browser at http://localhost:7474/browser/ to view streamed data.

===============================================================================

License
-------

See ``LICENSE.txt`` for license details.

Acknowledgements
----------------

Funded by NSF award #2112606 (ICICLE) and the Data to Insight Center at Indiana University.

