import unittest
import json
from neo4j import GraphDatabase


class TestRawImageCount(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # Initialize connection to Neo4j
        cls.uri = "bolt://localhost:7687"
        cls.driver = GraphDatabase.driver(cls.uri, auth=("neo4j", "PWD_HERE"))

    @classmethod
    def tearDownClass(cls):
        # Close connection
        cls.driver.close()

    def test_raw_image_count(self):
        # Load the JSON file and calculate the total image count
        json_file_path = 'plugins/oracle_ckn_daemon/events/image_mapping_final.json'
        with open(json_file_path, 'r') as file:
            data = json.load(file)
        
        # Calculate the total number of images
        total_image_count = len(data) - 1

        with self.driver.session() as session:
            # Query to count the number of RawImage nodes
            result = session.run("MATCH (ri:RawImage) RETURN COUNT(ri) AS count")
            count = result.single()["count"]

            # Assert that the count matches the total image count
            self.assertEqual(count, total_image_count, f"Expected {total_image_count} RawImage nodes but found {count}")
