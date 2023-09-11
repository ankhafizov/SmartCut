from kafka import KafkaProducer
from json import dumps


topic = "my_topic"
bootstrap_servers = "127.0.0.1:9092"
data = {"key": "value"}

kafka_producer = KafkaProducer(
    bootstrap_servers=bootstrap_servers,
    value_serializer=lambda x: dumps(x).encode("utf-8"),
)

kafka_producer.send(topic, value=data).get(timeout=1)
