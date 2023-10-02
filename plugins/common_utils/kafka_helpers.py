from kafka import KafkaProducer, KafkaConsumer
from json import dumps, loads

import logging


class KafkaHelper:
    def __init__(
        self,
        bootstrap_servers,
        plugin_name: str,
    ):
        """Хелпер для упрощения работы с кафкой.

        Args:
            bootstrap_servers (str): сокет кафки в формате ip:port
            plugin_name (str): уникальное имя плагина, совпадающее с именем поднятого контейнера
        """
        self.plugin_name = plugin_name
        self.bootstrap_servers = bootstrap_servers

        logging.info(f"KAFKA connects to {bootstrap_servers}")
        self.kafka_producer = KafkaProducer(
            bootstrap_servers=self.bootstrap_servers,
            value_serializer=lambda x: dumps(x).encode("utf-8"),
        )
        self.init_plugin_topic = "start-plugins"
        self.stop_plugin_topic = "stop-plugins"
        self.out_topic_for_timestamps = "processed-files"

    def send_plugin_init_message(self, plugin_label: str, input_img_size: int):
        """Доставляет в кафку сообщение о ПОДКЛЮЧЕНИИ плагина согласно пункту 1.1 архитектуры.

        Args:
            plugin_label (str): имя плагина отражаемое на фронте
            input_img_size (int): размер максимальной стороны изображения в пикселях для его сжатия
                на стороне фронта.
        """
        data = {"plugin_name": self.plugin_name, "label": plugin_label, "size": input_img_size}

        self.kafka_producer.send(self.init_plugin_topic, value=data).get(timeout=1)
        logging.info(f"KAFKA sent init message: {data} topic {self.init_plugin_topic}")

    def send_plugin_stop_info(self):
        """Доставляет в кафку сообщение об ОТКЛЮЧЕНИИ плагина согласно пункту 1.1 архитектуры."""
        data = {"plugin_name": self.plugin_name}

        self.kafka_producer.send(self.stop_plugin_topic, value=data).get(timeout=1)
        logging.info(f"KAFKA sent stop message: {data} topic {self.stop_plugin_topic}")

    def check_new_uploaded_videos(self) -> dict:
        """Корутина, позволяющая слушать сообщения из топика в бесконечном цикле.

        Формат:
            - "status" : "uploaded",
            - "zipped_images_path" : "40b1fea2-4a91-11ee-be56-0242ac120002/video_name1"

        Yields:
            dict: JSON из сообщения.
        """
        topic = f"{self.plugin_name}-new-files"
        kafka_consumer = KafkaConsumer(
            topic,
            bootstrap_servers=self.bootstrap_servers,
            value_deserializer=lambda x: loads(x.decode("utf-8")),
        )
        logging.info("listening kafka")

        for message in kafka_consumer:
            message_json = message.value
            logging.info(f"KAFKA received: {message_json} topic {topic}")

            is_message_type_ongoing = set(message_json.keys()) == set(
                ["status", "last_zipped_chunk_path", "user_id"]
            )
            is_message_type_processed = set(message_json.keys()) == set(
                ["status", "zipped_chunks_path", "user_id"]
            )
            assert is_message_type_ongoing or is_message_type_processed

            yield message_json

    def send_processed_file_timestamps_info(
        self, user_id: str, timestamps: list[dict[str:int]], zipped_chunks_path: str
    ):
        """формирует сообщение в кафку с выходными таймстампами фрагментов нарезки видео.
        Пункт 3.3 архитектуры.

        Args:
            user_id (str): UUID пользователя,
            timestamps (list[dict[str:int]],): список временных меток вида
                {"start" : 10, "stop" : 30},
            zipped_chunks_path (str): путь временного хранения кадров внутри shared-volume системы.
        """
        assert "\\" not in zipped_chunks_path
        for t in timestamps:
            assert set(t.keys()) == set(["start", "stop"])

        request_uid, video_name = zipped_chunks_path.split("/")

        data = {
            "user_id": user_id,
            "user_request_uid": request_uid,
            "video_name": video_name,
            "plugin_name": self.plugin_name,
            "timestamps": timestamps,
        }

        self.kafka_producer.send(self.out_topic_for_timestamps, value=data).get(timeout=1)
        logging.info(f"KAFKA sent processing result: {data} topic {self.out_topic_for_timestamps}")

    def send_processed_chunk_notification(self, user_id: str, processed_zipped_chunk_path: str):
        """формирует сообщение в кафку о завершении обработки одного чанка для отображения
        информации на фронте.
        Пункт 3.3 архитектуры.

        Args:
            user_id (str): UUID пользователя,
            processed_zipped_chunk_path (str): путь до обработанного zip-файла чанка относительно
                shared-volume (как в приходящем сообщении от бэкенда).
        """

        assert "\\" not in processed_zipped_chunk_path
        request_uid, video_name, processed_chunk = processed_zipped_chunk_path.split("/")

        data = {
            "user_id": user_id,
            "user_request_uid": request_uid,
            "video_name": video_name,
            "plugin_name": self.plugin_name,
            "processed_chunk": processed_chunk,
        }

        self.kafka_producer.send(self.out_topic_for_timestamps, value=data).get(timeout=1)
        logging.info(f"KAFKA sent processing result: {data} topic {self.out_topic_for_timestamps}")
