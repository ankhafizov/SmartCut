from kafka import KafkaProducer, KafkaConsumer
from json import loads, dumps

start_topic = "started_plugins"
plugin_topic = "detector-new-files"

bootstrap_servers = "127.0.0.1:9092"

init_data = {"plugin_name": "detector", "label": "детектор", "size": 640}


kafka_consumer = KafkaConsumer(
    plugin_topic,
    bootstrap_servers=bootstrap_servers,
    value_deserializer=lambda x: loads(x.decode("utf-8")),
    api_version=(0, 10, 2),
)

kafka_producer = KafkaProducer(
    bootstrap_servers=bootstrap_servers,
    value_serializer=lambda x: dumps(x).encode("utf-8"),
    api_version=(0, 10, 2),
    max_block_ms=1200000,
)

def detect():
    return {"classes": []}

# kafka_producer.send(start_topic, value=init_data).get(timeout=120)

for message in kafka_consumer:

    message = message.value

    detect_res = detect()

    kafka_producer.send(start_topic, value=detect_res).get(timeout=120)
