import logging
import os
import sys
import hydra
import shutil

from omegaconf import DictConfig

sys.path.append("..")


from plugins.YOLO_based_detector.yolo_utils import (
    init_yolo_model,
    merge_timestamps,
    process_chunk,
)

from plugins.common_utils.common_helpers import unzip_archive

from plugins.common_utils.kafka_helpers import KafkaHelper  # noqa: E402


@hydra.main(version_base=None, config_path="configs", config_name="app_config")
def main(config: DictConfig) -> None:
    kafka_helper = KafkaHelper(
        bootstrap_servers=config["kafka"]["bootstrap_servers"],
        plugin_name=config["plugin"]["name"],
    )

    kafka_helper.send_plugin_init_message(
        plugin_label=config["plugin"]["label"],
        input_img_size=config["plugin"]["img_size"],
    )

    model = init_yolo_model()

    temp_data_folder = f"{config['plugin']['data_folder']}/"
    result_dict = {}

    for message in kafka_helper.check_new_uploaded_videos():
        if message["status"] == "in-progress":
            zipped_chunks_path = temp_data_folder + message["last_zipped_chunk_path"]
            req_id = (message["last_zipped_chunk_path"].split("/"))[0]

            if req_id not in result_dict:
                result_dict[req_id] = {}
                result_dict[req_id]["result_detection_list"] = []
                result_dict[req_id]["result_timestamps_list"] = []
            try:

                unpacked_content_path = unzip_archive(zipped_chunks_path)

                detections, chunk_timestamps = process_chunk(
                    model, unpacked_content_path, config["plugin"]["detect_class"], kafka_helper, message)

                result_dict[req_id]["result_detection_list"].extend(detections)
                result_dict[req_id]["result_timestamps_list"].extend(chunk_timestamps)
            except Exception as e:
                logging.error(f"could not process {zipped_chunks_path}, error: {str(e)}")
                pass
            finally:
                logging.info(f"finish processing: {zipped_chunks_path}. Removing it")
                if os.path.isfile(zipped_chunks_path):
                    os.remove(zipped_chunks_path)

        elif message["status"] == "uploaded":
            req_id = (message["zipped_chunks_path"].split("/"))[0]

            result_dict[req_id]["timestamps"] = merge_timestamps(
                result_dict[req_id]["result_detection_list"],
                result_dict[req_id]["result_timestamps_list"],
                config['timestamp_extractor']['min_pair_resolution_secs'],
                config['timestamp_extractor']['min_pair_length_secs']
            )

            kafka_helper.send_processed_file_timestamps_info(
                user_id=message["user_id"],
                timestamps=result_dict[req_id]["timestamps"],
                zipped_chunks_path=message["zipped_chunks_path"],
            )

            del result_dict[req_id]
            shutil.rmtree(os.path.join(temp_data_folder, req_id))

        else:
            raise ValueError("Unknown received message status")


if __name__ == "__main__":
    main()
