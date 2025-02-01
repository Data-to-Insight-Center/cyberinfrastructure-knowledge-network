from json import dumps
from kafka import KafkaProducer

class KafkaIngester:
    """
    Library class for ingesting information into CKN through Kafka.
    """

    def __init__(self, server_list, ckn_topic):
        self.producer = KafkaProducer(bootstrap_servers=[server_list],
                         value_serializer=lambda x: dumps(x).encode('utf-8'))

        self.topic = ckn_topic

    def send_request(self, request, key=None):
        """
        Sends requests to CKN
        """
        self.producer.send(topic=self.topic, value=request, key=key.encode())

    def send_qoe(self, request):
        """
        Sends QoE events to CKN
        """
        self.producer.send(topic=self.topic, value=request)
