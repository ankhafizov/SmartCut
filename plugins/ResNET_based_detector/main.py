import sys
import os
import hydra
from glob import glob
import cv2
import numpy as np
from omegaconf import DictConfig
import logging

sys.path.append("..")

from plugins.ResNET_based_detector.core.FeatureExtractor import FeatureExtractor  # noqa: E402
from plugins.ResNET_based_detector.core.TimestampExtractor import TimestampExtractor  # noqa: E402
from plugins.common_utils.kafka_helpers import KafkaHelper  # noqa: E402
from plugins.common_utils.common_helpers import unzip_archive  # noqa: E402


@hydra.main(version_base=None, config_path="configs", config_name="app_config")
def main(config: DictConfig) -> None:
    kafka_helper = KafkaHelper(
        bootstrap_servers=config["kafka"]["bootstrap_servers"], plugin_name=config["plugin"]["name"]
    )
    feature_extractor = FeatureExtractor(config["feature_extractor_node"])
    timestamp_extractor = TimestampExtractor(config["timestamp_extractor"])

    kafka_helper.send_plugin_init_message(
        plugin_label=config["plugin"]["label"],
        input_img_size=config["plugin"]["img_size"],
    )

    temp_data_folder = f"{config['plugin']['data_folder']}/"

    for message in kafka_helper.check_new_uploaded_videos():
        if message["status"] == "in-progress":
            zipped_chunks_path = temp_data_folder + message["last_zipped_chunk_path"]
            dst_path = unzip_archive(zipped_chunks_path)

            img_paths_to_process = [
                img_path
                for img_path in glob(f"{dst_path}/*{config['plugin']['img_extention']}")
                if not os.path.isfile(img_path.replace(config["plugin"]["img_extention"], "npy"))
            ]

            logging.info(f"processing {len(img_paths_to_process)} files in {dst_path}")
            for img_path in img_paths_to_process:
                img_bgr = cv2.imread(img_path)
                img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
                feature_vector = feature_extractor.extract_feature_vector(img_rgb)
                np.save(img_path.replace(".jpg", ".npy"), feature_vector)
            logging.info(f"finish processing: {zipped_chunks_path}. Removing it")

            os.remove(zipped_chunks_path)
        elif message["status"] == "uploaded":
            timestamps = timestamp_extractor.get_events_timestamps(
                temp_data_folder + message["zipped_chunks_path"]
            )

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
