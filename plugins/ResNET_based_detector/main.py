import sys

sys.path.append("..")

from plugins.common_utils.kafka_helpers import KafkaHelper  # noqa: E402
from plugins.common_utils.common_helpers import read_config  # noqa: E402


config = read_config("ResNET_based_detector/config.yaml")
kafka_helper = KafkaHelper(
    bootstrap_servers=config["kafka"]["bootstrap_servers"], plugin_name=config["plugin"]["name"]
)


kafka_helper.send_plugin_init_message(
    plugin_label=config["plugin"]["label"],
    input_img_size=config["plugin"]["img_size"],
)

for message in kafka_helper.check_new_uploaded_videos():
    print(message)
