Getting Started with CKN: Building a Temperature Monitoring Use Case
=====================================================================
.. image:: https://img.shields.io/badge/license-BSD%203--Clause-blue.svg
   :target: https://opensource.org/licenses/BSD-3-Clause
   :alt: License: BSD 3-Clause

Welcome to the **Cyberinfrastructure Knowledge Network (CKN)**! This guide will help you create your own use case using CKN's Edge AI Framework. We'll walk you through setting up a temperature monitoring system that streams data from sensors to a knowledge graph using Kafka and Neo4j. This step-by-step tutorial is designed for users with varying technical backgrounds.

Table of Contents
------------------

1. `Set Up Your Environment <#step-1>`_
2. `Create a Kafka Topic for Temperature Events <#step-2>`_
3. `Produce Temperature Events <#step-3>`_
4. `Consume and View Events <#step-4>`_
5. `Connect Kafka to Neo4j <#step-5>`_
6. `Visualize Data in Neo4j <#step-6>`_

Prerequisites
-------------
Before you begin, ensure you have the following installed on your machine:

- **Docker & Docker Compose**: For containerizing services.
- **Python 3.7+**: To run the producer script.
- **Git**: To clone the CKN repository.
- **Basic Command-Line Knowledge**: Familiarity with terminal commands.

.. _step-1:

Step 1: Set Up Your Environment
-------------------------------
1. **Clone the CKN Repository**

   .. code-block:: bash

      git clone https://github.com/Data-to-Insight-Center/cyberinfrastructure-knowledge-network.git
      cd cyberinfrastructure-knowledge-network

2. **Start Services with Docker Compose**

   Launch Kafka, Neo4j, and other necessary services.

   .. code-block:: bash

      make up

   *Wait a few moments for all services to initialize.*

.. _step-2:

Step 2: Create a Kafka Topic for Temperature Events
---------------------------------------------------

We'll create a Kafka topic named ``temperature-sensor-data`` to store temperature events from various sensors.

1. **Update `docker-compose.yml`**

   Open the ``docker-compose.yml`` file in the root directory and add the new topic to the Kafka broker configuration.

   .. code-block:: yaml

      services:
        broker:
          environment:
            KAFKA_CREATE_TOPICS: "temperature-sensor-data:1:1"

2. **Apply Changes**

   Restart the Docker services to create the new topic.

   .. code-block:: bash

      make down
      make up

   *Alternatively, you can use Kafka CLI tools to create the topic without modifying `docker-compose.yml`. But this is not persistent and will be removed once CKN broker is restarted.*

.. _step-3:

Step 3: Produce Temperature Events
----------------------------------

We'll use a Python script to simulate temperature data from different sensors and send it to the Kafka topic.

1. **Install Required Python Libraries**

   In this tutorial, we'll use the `confluent-kafka <https://pypi.org/project/confluent-kafka/>`_ library. You can use other Kafka libraries if you prefer.

   We recommend creating a new virtual environment using venv before installing confluent-kafka. To do so, please follow instructions `here<https://docs.python.org/3/library/venv.html>`_.

   .. code-block:: bash

      pip install confluent-kafka

2. **Create the Producer Script**

   Create a file named ``produce_temperature_events.py`` with the following content:

   .. code-block:: python

      from confluent_kafka import Producer
      import json
      import time

      # configuration to connect to CKN Kafka broker
      kafka_conf = {
          'bootstrap.servers': 'localhost:9092',
      }

      producer = Producer(kafka_conf)

      # Simulate temperature sensor data for 3 dummy sensors
      sensors = ['sensor_1', 'sensor_2', 'sensor_3']

      try:
          for i in range(10):
              for sensor_id in sensors:
                  event = {
                      "sensor_id": sensor_id,
                      "temperature": round(20 + 10 * (0.5 - time.time() % 1), 2),
                      "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
                  }
                  producer.produce('temperature-sensor-data', key=sensor_id, value=json.dumps(event))
              producer.flush()
              time.sleep(1)
          print("Produced 10 events successfully.")
      except Exception as e:
          print(f"An error occurred: {e}")

3. **Run the Producer**

   Execute the script to send temperature events.

   .. code-block:: bash

      python produce_temperature_events.py

   *You should see a confirmation message indicating that 10 events have been produced.*

.. _step-4:

Step 4: Consume and View Events
-------------------------------

To verify that your events are being sent correctly, use a Kafka consumer to view the incoming data.

1. **Access Kafka CLI**

   Enter the Kafka container to run the consumer.

   .. code-block:: bash

      docker exec -it broker bash

   *Ensure to modify the container name (broker) in the command if your Kafka container has a different name.*

2. **Start a Kafka Consumer**

   .. code-block:: bash

      kafka-console-consumer --bootstrap-server localhost:9092 --topic temperature-sensor-data --from-beginning

   *You should see JSON-formatted temperature events being printed.*

3. **Exit the Consumer**

    In Mac or Linux, press ``Ctrl + C`` to stop the consumer. Or in Windows, press ``Ctrl + Break``.

.. _step-5:

Step 5: Connect Kafka to Neo4j
------------------------------

We'll set up a Kafka Connector to stream temperature events into the Neo4j knowledge graph.

1. **Create Connector Configuration**

   Navigate to the ``ckn_broker`` directory and create a configuration file named ``neo4jsink-temperature-connector.json``:

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
          "neo4j.topic.cypher.temperature-sensor-data": "
            MERGE (sensor:Sensor {id: event.sensor_id})
            MERGE (reading:TemperatureReading {timestamp: datetime(event.timestamp)})
            SET reading.temperature = event.temperature
            MERGE (sensor)-[:REPORTED]->(reading)
          "
        }
      }

2. **Add Connector to Docker Compose**

   Place the ``neo4jsink-temperature-connector.json`` file in the appropriate directory (e.g., ``ckn_broker/connectors/``) as per your project structure.

3. **Register the Connector**

   Add the following curl command to the ``setup_connector.sh`` script in the ``ckn_broker`` directory:

   .. code-block:: bash

      curl -X POST -H "Content-Type: application/json" --data @/app/neo4jsink-temperature-connector.json http://localhost:8083/connectors

4. **Restart Docker Compose to Register the Connector**

   After adding the new connector configuration, restart the Docker services to apply the changes.

   .. code-block:: bash

      make down
      make up

   *CKN will automatically register the new connector upon startup.*

5. **Execute the script to send temperature events.**

   .. code-block:: bash

      python produce_temperature_events.py

.. _step-6:

Step 6: Visualize Data in Neo4j
-------------------------------

With the connector in place, temperature events are now being streamed to Neo4j. Let's visualize the data.

1. **Access Neo4j Browser**

   Open your web browser and navigate to `http://localhost:7474/browser/ <http://localhost:7474/browser/>`_.

2. **Log In**

   - **Username:** ``neo4j``
   - **Password:** ``PWD_HERE``

3. **Run a Query to View Data**

   Execute the following Cypher query to view all sensors and their temperature readings:

   .. code-block:: cypher

      MATCH (s:Sensor)-[:REPORTED]->(r:TemperatureReading)
      RETURN s, r

   *You should see nodes representing sensors connected to their respective temperature readings.*

4. **Explore the Graph**

   Use Neo4j's visualization tools to explore relationships, filter data, and gain insights from your temperature monitoring use case.

Troubleshooting
---------------

- **Kafka Services Not Starting:**
  - Ensure Docker is running correctly.
  - Check for port conflicts on ``9092`` (Kafka) and ``7474`` (Neo4j).

- **Connector Registration Fails:**
  - Verify that the ``neo4jsink-temperature-connector.json`` file has correct Neo4j credentials.
  - Ensure Kafka Connect is running on ``localhost:8083``.

- **No Data in Neo4j:**
  - Confirm that the producer is sending events to the correct Kafka topic.
  - Check the Kafka consumer to ensure events are being published.
  - Review connector logs for any errors.

Next Steps
----------

Congratulations! You've successfully set up a temperature monitoring use case with CKN, Kafka, and Neo4j. Here are some ideas to further enhance your setup:

- **Add More Sensors:** Expand the number of sensors to simulate a larger network.
