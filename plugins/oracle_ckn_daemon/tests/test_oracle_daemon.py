import unittest
import json
import docker
from unittest.mock import MagicMock
from neo4j import GraphDatabase

class TestCKNDaemon(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # Initialize connection to Neo4j
        cls.uri = "bolt://localhost:7687"
        cls.driver = GraphDatabase.driver(cls.uri, auth=("neo4j", "PWD_HERE"))

        cls.mock_producer = MagicMock()
        cls.client = docker.from_env()

    @classmethod
    def tearDownClass(cls):
        cls.driver.close()
        cls.client.close()

    def test_raw_image_count(self):
        # Load the JSON file and calculate the total image count
        json_file_path = 'plugins/oracle_ckn_daemon/events/image_mapping_final.json'
        with open(json_file_path, 'r') as file:
            data = json.load(file)
        total_image_count = sum(1 for uuid, info in data.items() if "image_count" in info)

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
        container_name = "oracle-daemon"

        try:
            container = self.client.containers.get(container_name)
            self.assertEqual(container.status, "exited", f"Container {container_name} is not exited.")
        
        except docker.errors.NotFound:
            self.fail(f"Container {container_name} not found.")

if __name__ == '__main__':
    unittest.main()