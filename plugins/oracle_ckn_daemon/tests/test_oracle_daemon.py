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


@pytest.mark.parametrize("node_label, expected_count", [
    ("Experiment", 1),
    ("EdgeDevice", 1),
    ("Deployment", 1),
    ("User", 1),
    ("Model", 1),
    ("RawImage", 12),
])
def test_node_count(neo4j_driver, node_label, expected_count):
    """
    Test that checks the number of nodes with a specific label in Neo4j.

    Args:
        neo4j_driver (neo4j.Driver): Fixture providing the Neo4j driver instance.
        node_label (str): The label of the node to count.
        expected_count (int): The expected number of nodes with the given label.

    Raises:
        AssertionError: If the actual number of nodes does not match the expected count.
    """

    def count_nodes(tx, label):
        """
        Helper function to execute a Cypher query that counts the number of nodes with a specific label.

        Args:
            tx (neo4j.Transaction): The Neo4j transaction object.
            label (str): The label of the node to count.

        Returns:
            int: The total number of nodes with the specified label.
        """
        result = tx.run(f"MATCH (n:{label}) RETURN count(n) AS totalNodes")
        return result.single()["totalNodes"]

    with neo4j_driver.session() as session:
        actual_count = session.read_transaction(count_nodes, node_label)

    assert actual_count == expected_count, f"Expected {expected_count} {node_label} nodes, but found {actual_count} in Neo4j"
