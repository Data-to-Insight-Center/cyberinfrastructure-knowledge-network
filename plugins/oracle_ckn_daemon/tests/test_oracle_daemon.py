import unittest
import json
import os
import docker
from unittest.mock import MagicMock
from neo4j import GraphDatabase

class TestCKNDaemon(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # Initialize connection to Neo4j
        cls.uri = "bolt://localhost:7687"
        cls.driver = GraphDatabase.driver(cls.uri, auth=("neo4j", "PWD_HERE"))

        # Set up environment variables needed for the shutdown test
        os.environ['EXPERIMENT_END_SIGNAL'] = 'shutdown-signal-uuid'
        cls.file_path = 'test_oracle_events.json'

        # Create a mock producer
        cls.mock_producer = MagicMock()

        # Initialize Docker client
        cls.client = docker.from_env()

    @classmethod
    def tearDownClass(cls):
        # Close Neo4j connection
        cls.driver.close()

        # Close Docker client
        cls.client.close()

        # Clean up the test file
        if os.path.exists(cls.file_path):
            os.remove(cls.file_path)

    def test_raw_image_count(self):
        # Load the JSON file and calculate the total image count
        json_file_path = 'plugins/oracle_ckn_daemon/events/image_mapping_final.json'
        with open(json_file_path, 'r') as file:
            data = json.load(file)

        # Calculate the total number of images
        total_image_count = len(data) - 1

        with self.driver.session() as session:
            # Query to count the number of RawImage nodes
            result = session.run(
                "MATCH (ri:RawImage) RETURN COUNT(ri) AS count")
            count = result.single()["count"]

            # Assert that the count matches the total image count
            self.assertEqual(
                count, total_image_count,
                f"Expected {total_image_count} RawImage nodes but found {count}"
            )

    def test_container_exited(self):
        # Name of the container to check
        container_name = "oracle_ckn_daemon-ckn-daemon-1"

        try:
            # Get the container by name
            container = self.client.containers.get(container_name)
            # Check if the container has exited
            self.assertEqual(container.status, "exited", f"Container {container_name} is not exited.")
        except docker.errors.NotFound:
            self.fail(f"Container {container_name} not found.")

if __name__ == '__main__':
    unittest.main()