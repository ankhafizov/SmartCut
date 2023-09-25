from kafka import KafkaConsumer
from json import loads


topic = "my_topic"
bootstrap_servers = "127.0.0.1:9092"

kafka_consumer = KafkaConsumer(
    topic,
    bootstrap_servers=bootstrap_servers,
    value_deserializer=lambda x: loads(x.decode("utf-8")),
)

for message in kafka_consumer:
    message = message.value
