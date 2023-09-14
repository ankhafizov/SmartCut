from kafka import KafkaConsumer
from json import loads


plugin_topic = "detector-new-files"
bootstrap_servers = "127.0.0.1:9092"

kafka_consumer = KafkaConsumer(
    plugin_topic,
    bootstrap_servers=bootstrap_servers,
    value_deserializer=lambda x: loads(x.decode("utf-8")),
)

for message in kafka_consumer:
    message = message.value
    print(message)