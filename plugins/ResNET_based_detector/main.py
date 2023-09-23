import sys
import hydra
from omegaconf import DictConfig

sys.path.append("..")

from plugins.common_utils.kafka_helpers import KafkaHelper  # noqa: E402


@hydra.main(version_base=None, config_path="configs", config_name="app_config")
def main(config: DictConfig) -> None:
    kafka_helper = KafkaHelper(
        bootstrap_servers=config["kafka"]["bootstrap_servers"], plugin_name=config["plugin"]["name"]
    )

    kafka_helper.send_plugin_init_message(
        plugin_label=config["plugin"]["label"],
        input_img_size=config["plugin"]["img_size"],
    )

    for message in kafka_helper.check_new_uploaded_videos():
        print(message)


if __name__ == "__main__":
    main()
