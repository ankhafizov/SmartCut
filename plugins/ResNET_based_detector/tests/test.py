from kafka import KafkaProducer
from json import dumps
import sys

sys.path.append("..")

from plugins.common_utils.common_helpers import read_config  # noqa: E402


config = read_config("ResNET_based_detector/config.yaml")

topic = topic = f"{config['plugin']['name']}-new-files"
bootstrap_servers = config["kafka"]["bootstrap_servers"]
data = {
    "status": "uploaded",
    "zipped_images_path": "40b1fea2-4a91-11ee-be56-0242ac120002/video_name1",
}

kafka_producer = KafkaProducer(
    bootstrap_servers=bootstrap_servers,
    value_serializer=lambda x: dumps(x).encode("utf-8"),
)

kafka_producer.send(topic, value=data).get(timeout=1)
