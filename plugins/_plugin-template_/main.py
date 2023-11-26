import sys
import os
import hydra
from glob import glob
import numpy as np
from omegaconf import DictConfig
import logging
from PIL import Image
import shutil
import time

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
    time.sleep(3)
    kafka_helper.send_plugin_init_message(
        plugin_label=config["plugin"]["label"],
        input_img_size=config["plugin"]["img_size"],
    )
    temp_data_folder = f"{config['plugin']['data_folder']}/"

    # сначала загружаем вообще все, превращаем в вектора, затем вообще по всем векторам считаем среднее
    for message in kafka_helper.check_new_uploaded_videos():
        if message["status"] == "in-progress":
            # пока загружается обрабатываем чанки
            zipped_chunks_path = temp_data_folder + message["last_zipped_chunk_path"]
            try:
                dst_path = unzip_archive(zipped_chunks_path)

                img_paths_to_process = [
                    img_path
                    for img_path in glob(f"{dst_path}/*{config['plugin']['img_extention']}")
                    if not os.path.isfile(img_path.replace(config["plugin"]["img_extention"], "npy"))
                ]

                # логируем сколько обработали и сколько осталось
                logging.info(f"processing {len(img_paths_to_process)} files in {dst_path}")
                for img_path in img_paths_to_process:
                    try:
                        img = Image.open(img_path)
                        # извлекаем фича вектор
                        feature_vector = feature_extractor.extract_feature_vector(img)
                        # заменяем картинку на фича вектор
                        np.save(img_path.replace(".jpg", ".npy"), feature_vector)
                        # отправляем инфу о том что обработали чанк
                        kafka_helper.send_processed_chunk_notification(
                            user_id=message["user_id"],
                            processed_zipped_chunk_path=message["last_zipped_chunk_path"],
                        )
                    except Exception as e:
                        logging.error(f"Could not process image {img_path}, error: {str(e)}")
            except Exception as e:
                logging.error(f"could not process {zipped_chunks_path}, error: {str(e)}")
                pass
            finally:
                # удаляем этот чанк
                logging.info(f"finish processing: {zipped_chunks_path}. Removing it")
                if os.path.isfile(zipped_chunks_path):
                    os.remove(zipped_chunks_path)
        # если все видео уже обработано
        elif message["status"] == "uploaded":
            timestamps = timestamp_extractor.get_events_timestamps(
                temp_data_folder + message["zipped_chunks_path"]
            )

            kafka_helper.send_processed_file_timestamps_info(
                user_id=message["user_id"],
                timestamps=timestamps,
                zipped_chunks_path=message["zipped_chunks_path"],
            )

            req_id = (message["zipped_chunks_path"].split('/'))[0]
            shutil.rmtree(os.path.join(temp_data_folder, req_id))
        else:
            raise ValueError("Unknown received message status")


if __name__ == "__main__":
    main()
