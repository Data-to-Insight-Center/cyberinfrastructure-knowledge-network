import os
import unittest
import json
import docker
from unittest.mock import MagicMock
from neo4j import GraphDatabase

class TestExampleDaemon(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # Initialize connection to Neo4j
        cls.uri = "bolt://localhost:7687"
        cls.driver = GraphDatabase.driver(cls.uri, auth=("neo4j", "PWD_HERE"))

        cls.mock_producer = MagicMock()
        cls.client = docker.from_env()

        # Load the JSON data
        current_dir = os.path.dirname(os.path.abspath(__file__))
        json_file_path = os.path.join(current_dir, '..', 'event.json')
        with open(json_file_path, 'r') as file:
            cls.json_data = json.load(file)

    @classmethod
    def tearDownClass(cls):
        cls.driver.close()
        cls.client.close()

    def test_node_count(self):
        expected_count = 6

        # Count nodes in Neo4j
        with self.driver.session() as session:
            result = session.run("MATCH (n) RETURN count(n) AS totalNodes")
            actual_count = result.single()["totalNodes"]

        self.assertEqual(actual_count, expected_count,
                         f"Expected {expected_count} nodes, but found {actual_count} in Neo4j")

if __name__ == '__main__':
    unittest.main()