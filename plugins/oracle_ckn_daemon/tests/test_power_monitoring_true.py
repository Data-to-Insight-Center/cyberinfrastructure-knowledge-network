import pytest
from neo4j import GraphDatabase

@pytest.fixture(scope="module")
def neo4j_driver():
    """
    Fixture to create a Neo4j driver instance that is shared across tests in the module.

    Yields:
        driver (neo4j.Driver): Neo4j driver instance to connect to the database.
    """
    uri = "bolt://localhost:7687"
    driver = GraphDatabase.driver(uri, auth=("neo4j", "PWD_HERE"))
    yield driver
    driver.close()

def test_power_monitoring_true(neo4j_driver):
    """
    Test that checks if the total_cpu_power_consumption and total_gpu_power_consumption properties are present in the Deployment node.

    Args:
        neo4j_driver (neo4j.Driver): Fixture providing the Neo4j driver instance.

    Raises:
        AssertionError: If the properties are not found in the Deployment node.
    """
    def check_power_monitoring(tx):
        """
        Helper function to execute a Cypher query that checks if the total_cpu_power_consumption and total_gpu_power_consumption properties are present in the Deployment node.

        Args:
            tx (neo4j.Transaction): The Neo4j transaction object.

        Returns:
            bool: True if the properties are present, False otherwise.
        """
        result = tx.run(
            "MATCH (d:Deployment) RETURN properties(d) AS allProperties"
        )
        properties = result.single()["allProperties"]

        return 'total_cpu_power_consumption' in properties and 'total_gpu_power_consumption' in properties

    with neo4j_driver.session() as session:
        assert session.execute_read(check_power_monitoring), (
            "total_cpu_power_consumption or total_gpu_power_consumption NOT found in Deployment node"
        )
