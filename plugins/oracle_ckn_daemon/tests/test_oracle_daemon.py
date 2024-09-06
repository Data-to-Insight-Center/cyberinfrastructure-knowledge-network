import pytest
from neo4j import GraphDatabase

@pytest.fixture(scope="module")
def neo4j_driver():
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
    def count_nodes(tx, label):
        result = tx.run(f"MATCH (n:{label}) RETURN count(n) AS totalNodes")
        return result.single()["totalNodes"]

    with neo4j_driver.session() as session:
        actual_count = session.read_transaction(count_nodes, node_label)

    assert actual_count == expected_count, f"Expected {expected_count} {node_label} nodes, but found {actual_count} in Neo4j"