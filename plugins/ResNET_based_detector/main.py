import sys
import hydra
from glob import glob
import cv2
import numpy as np
from omegaconf import DictConfig
import logging

from plugins.ResNET_based_detector.core.FeatureExtractor import FeatureExtractor

sys.path.append("..")

from plugins.common_utils.kafka_helpers import KafkaHelper  # noqa: E402
from plugins.common_utils.common_helpers import unzip_archive  # noqa: E402


@hydra.main(version_base=None, config_path="configs", config_name="app_config")
def main(config: DictConfig) -> None:
    kafka_helper = KafkaHelper(
        bootstrap_servers=config["kafka"]["bootstrap_servers"], plugin_name=config["plugin"]["name"]
    )
    feature_extractor_node = FeatureExtractor(config["feature_extractor_node"])

    kafka_helper.send_plugin_init_message(
        plugin_label=config["plugin"]["label"],
        input_img_size=config["plugin"]["img_size"],
    )

    for message in kafka_helper.check_new_uploaded_videos():
        if message["status"] == "in-progress":
            zipped_chunks_path = (
                f"{config['plugin']['data_folder']}/" + message["zipped_chunks_path"]
            )
            dst_path = unzip_archive(zipped_chunks_path)

            logging.info(f"started to process {len(glob(f'{dst_path}/*jpg'))} files")
            for img_path in glob(f"{dst_path}/*{config['plugin']['img_extention']}"):
                img_bgr = cv2.imread(img_path)
                img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
                feature_vector = feature_extractor_node.extract_feature_vector(img_rgb)
                np.save(img_path.replace(".jpg", ".npy"), feature_vector)
            logging.info(f"finish processing: {zipped_chunks_path}")
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
