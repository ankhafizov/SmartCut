from kafka import KafkaProducer
from json import dumps


start_topic = "started_plugins"
bootstrap_servers = "127.0.0.1:9092"

plugin_name = "detector"
label = "детектор"
size = 640 # переделать на получение с фронта

data = {"plugin_name": plugin_name, "label": label, "size": size}

kafka_producer = KafkaProducer(
    bootstrap_servers=bootstrap_servers,
    value_serializer=lambda x: dumps(x).encode("utf-8"),
)

kafka_producer.send(start_topic, value=data).get(timeout=1)




