.. Cyberinfrastructure Knowledge Network documentation master file, created by
   sphinx-quickstart on Tue Dec  3 17:43:28 2024.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Cyberinfrastructure Knowledge Network (CKN)
============================================
.. image:: https://img.shields.io/badge/license-BSD%203--Clause-blue.svg
   :target: https://opensource.org/licenses/BSD-3-Clause
   :alt: License: BSD 3-Clause

Create your own plugin for CKN
---------------------------------

Follow these steps to stream custom events to the CKN knowledge graph:

1. **Create a Kafka topic to store your events**

   Update the `KAFKA_CREATE_TOPICS` environment variable in the `docker-compose.yml <https://github.com/Data-to-Insight-Center/cyberinfrastructure-knowledge-network/blob/main/docker-compose.yml>`_ to include a new topic for your events.

   .. code-block:: yaml

      broker:
        environment:
          KAFKA_CREATE_TOPICS: "my-custom-topic:1:1"

   Replace `my-custom-topic` with the desired topic name. Ensure the format follows: `topic_name:partitions:replication_factor`.

2. **Define a Neo4j connector**

   Create a Neo4j Sink Connector configuration file in the `ckn_broker <https://github.com/Data-to-Insight-Center/cyberinfrastructure-knowledge-network/tree/main/ckn_broker>`_ directory.

   For example, create a file named `neo4jsink-my-custom-topic-connector.json` with the following content:

   .. code-block:: json

      {
        "name": "Neo4jSinkConnectorMyCustomTopic",
        "config": {
          "topics": "my-custom-topic",
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
          "neo4j.topic.cypher.my-custom-topic": "
            MERGE (event:CustomEvent {id: event.event_id})
            SET event += {
              name: event.name,
              timestamp: datetime(event.timestamp),
              data: event.data
            }
          "
        }
      }

   Replace `my-custom-topic` with your topic name and customize the Cypher query to map your event structure to the Neo4j schema.

3. **Register the connector**

   Update the `setup_connector.sh <https://github.com/Data-to-Insight-Center/cyberinfrastructure-knowledge-network/blob/main/ckn_broker/setup_connector.sh>`_ script in the `ckn_broker` directory to include a `curl` command for registering the new connector:

   .. code-block:: bash

      curl -X POST -H "Content-Type: application/json" \
           --data @/app/neo4jsink-my-custom-topic-connector.json \
           http://localhost:8083/connectors

4. **Restart services**

   Navigate to the root directory and restart the Docker Compose setup to apply the changes:

   .. code-block:: bash

      docker-compose down
      make up

5. **Produce events to the topic**

   Use a Kafka producer to send events to your custom topic. For example:

   .. code-block:: bash

      kafka-console-producer --broker-list localhost:9092 --topic my-custom-topic

   Enter event data in JSON format. Example:

   .. code-block:: json

      {"event_id": "123", "name": "Test Event", "timestamp": "2024-12-03T12:34:56Z", "data": {"key": "value"}}

6. **Visualize the data**
   You can view the streamed data on the `CKN dashboard <http://localhost:8502/Camera_Traps>`_.

   Access the `Neo4j Browser <http://localhost:7474/browser/>`_ using `neo4j`and `PWD_HERE` as the username and password.
   Run ```MATCH (n) RETURN n``` to view the streamed data in the knowledge graph.
