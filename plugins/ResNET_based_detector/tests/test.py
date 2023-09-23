from kafka import KafkaProducer
from json import dumps
import yaml


def read_config(path: str) -> dict:
    with open(path, "r") as f:
        config = yaml.safe_load(f)

    return config


config = read_config("ResNET_based_detector/configs/app_config.yaml")

topic = topic = f"{config['plugin']['name']}-new-files"
bootstrap_servers = "127.0.0.1:9092"  # config["kafka"]["bootstrap_servers"]
data = {
    "status": "uploaded",
    "zipped_images_path": "40b1fea2-4a91-11ee-be56-0242ac120002/video_name1",
}

kafka_producer = KafkaProducer(
    bootstrap_servers=bootstrap_servers,
    value_serializer=lambda x: dumps(x).encode("utf-8"),
)

kafka_producer.send(topic, value=data).get(timeout=1)
