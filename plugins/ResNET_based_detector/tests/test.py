from kafka import KafkaProducer
from json import dumps
import sys

sys.path.append("..")

from plugins.common_utils.common_helpers import read_config  # noqa: E402

config = read_config("ResNET_based_detector/configs/app_config.yaml")

topic = topic = f"{config['plugin']['name']}-new-files"
bootstrap_servers = "127.0.0.1:9092"  # config["kafka"]["bootstrap_servers"]
data = {
    "user_id": "user_id1",
    "status": "uploaded",
    "zipped_chunks_path": "8b75eaec-722c-43f2-8b08-8900ca82146a/VID_20180722_113623.mp4",
}

kafka_producer = KafkaProducer(
    bootstrap_servers=bootstrap_servers,
    value_serializer=lambda x: dumps(x).encode("utf-8"),
)

kafka_producer.send(topic, value=data).get(timeout=1)
