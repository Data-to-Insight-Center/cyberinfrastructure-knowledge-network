import unittest
from neo4j import GraphDatabase


class TestNeo4jConstraints(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # Initialize connection to Neo4j
        cls.uri = "bolt://localhost:7687"
        cls.driver = GraphDatabase.driver(cls.uri, auth=("neo4j", "PWD_HERE"))

    @classmethod
    def tearDownClass(cls):
        # Close connection
        cls.driver.close()

    def test_edge_device_id_unique(self):
        with self.driver.session() as session:
            # Create a node with a specific device_id
            session.run("CREATE (es:EdgeDevice {device_id: 'device_123'})")

            # Attempt to create another node with the same device_id (should fail)
            with self.assertRaises(Exception):
                session.run("CREATE (es:EdgeDevice {device_id: 'device_123'})")

    def test_raw_image_uuid_unique(self):
        with self.driver.session() as session:
            # Create a node with a specific UUID
            session.run("CREATE (ri:RawImage {UUID: 'uuid_123'})")

            # Attempt to create another node with the same UUID (should fail)
            with self.assertRaises(Exception):
                session.run("CREATE (ri:RawImage {UUID: 'uuid_123'})")

    def test_model_id_unique(self):
        with self.driver.session() as session:
            # Create a node with a specific model_id
            session.run("CREATE (md:Model {model_id: 'model_123'})")

            # Attempt to create another node with the same model_id (should fail)
            with self.assertRaises(Exception):
                session.run("CREATE (md:Model {model_id: 'model_123'})")

    def test_experiment_uuid_unique(self):
        with self.driver.session() as session:
            # Create a node with a specific experiment_id
            session.run(
                "CREATE (ex:Experiment {experiment_id: 'experiment_123'})")

            # Attempt to create another node with the same experiment_id (should fail)
            with self.assertRaises(Exception):
                session.run(
                    "CREATE (ex:Experiment {experiment_id: 'experiment_123'})")

    def test_user_id_unique(self):
        with self.driver.session() as session:
            # Create a node with a specific user_id
            session.run("CREATE (user:User {user_id: 'user_123'})")

            # Attempt to create another node with the same user_id (should fail)
            with self.assertRaises(Exception):
                session.run("CREATE (user:User {user_id: 'user_123'})")

    def test_compiler_app_id_unique(self):
        with self.driver.session() as session:
            # Create a node with a specific name
            session.run("CREATE (app:Application {name: 'app_123'})")

            # Attempt to create another node with the same name (should fail)
            with self.assertRaises(Exception):
                session.run("CREATE (app:Application {name: 'app_123'})")

    def test_compiler_profiler_uuid_unique(self):
        with self.driver.session() as session:
            # Create a node with a specific uuid
            session.run("CREATE (opt:Profiling {uuid: 'uuid_123'})")

            # Attempt to create another node with the same uuid (should fail)
            with self.assertRaises(Exception):
                session.run("CREATE (opt:Profiling {uuid: 'uuid_123'})")

    def test_modelcard_external_id_unique(self):
        with self.driver.session() as session:
            # Create a node with a specific external_id
            session.run("CREATE (mc:ModelCard {external_id: 'mc_123'})")

            # Attempt to create another node with the same external_id (should fail)
            with self.assertRaises(Exception):
                session.run("CREATE (mc:ModelCard {external_id: 'mc_123'})")

    def test_ai_model_external_id_unique(self):
        with self.driver.session() as session:
            # Create a node with a specific external_id
            session.run("CREATE (ai:AIModel {external_id: 'ai_123'})")

            # Attempt to create another node with the same external_id (should fail)
            with self.assertRaises(Exception):
                session.run("CREATE (ai:AIModel {external_id: 'ai_123'})")

    def test_datasheet_external_id_unique(self):
        with self.driver.session() as session:
            # Create a node with a specific external_id
            session.run("CREATE (ds:Datasheet {external_id: 'ds_123'})")

            # Attempt to create another node with the same external_id (should fail)
            with self.assertRaises(Exception):
                session.run("CREATE (ds:Datasheet {external_id: 'ds_123'})")

    def test_deployment_id_unique(self):
        with self.driver.session() as session:
            # Create a node with a specific deployment_id
            session.run("CREATE (depl:Deployment {deployment_id: 'depl_123'})")

            # Attempt to create another node with the same deployment_id (should fail)
            with self.assertRaises(Exception):
                session.run(
                    "CREATE (depl:Deployment {deployment_id: 'depl_123'})")
