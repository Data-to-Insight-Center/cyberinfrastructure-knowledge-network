import unittest

class TestServiceConnections(unittest.TestCase):

    def test_kafka(self):
        self._check_service_connection('localhost', 9092)

    def test_neo4j(self):
        self._check_service_connection('localhost', 7687)

    def test_dashboard(self):
        self._check_service_connection('localhost', 8502)

    def _check_service_connection(self, host, port):
        import socket
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            self.assertEqual(s.connect_ex((host, port)), 0)
