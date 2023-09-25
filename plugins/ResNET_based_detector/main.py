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
        if message["status"] == "in-progress":
            # TODO code here
            pass
        elif message["status"] == "uploaded":
            # TODO code here
            timestamps = [
                {"start": 10, "stop": 30},
                {"start": 60, "stop": 90},
                {"start": 120, "stop": 150},
            ]

            kafka_helper.send_processed_file_timestamps_info(
                user_id=message["user_id"],
                timestamps=timestamps,
                zipped_chunks_path=message["zipped_chunks_path"],
            )

            pass
        else:
            raise ValueError("Unknown received message status")


if __name__ == "__main__":
    main()
