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

        logging.warning(f"KAFKA connects to {bootstrap_servers}")
        self.kafka_producer = KafkaProducer(
            bootstrap_servers=self.bootstrap_servers,
            value_serializer=lambda x: dumps(x).encode("utf-8"),
        )
        self.init_plugin_topic = "start-plugins"

    def send_plugin_init_message(self, plugin_label: str, input_img_size: int):
        """Доставляет в кафку сообщение о ПОДКЛЮЧЕНИИ плагина согласно пункту 1.1 архитектуры.

        Args:
            plugin_label (str): имя плагина отражаемое на фронте
            input_img_size (int): размер максимальной стороны изображения в пикселях для его сжатия
                на стороне фронта.
        """
        data = {"plugin_name": self.plugin_name, "label": plugin_label, "size": input_img_size}

        self.kafka_producer.send(self.init_plugin_topic, value=data).get(timeout=1)

    def send_plugin_stop_info(self):
        """Доставляет в кафку сообщение об ОТКЛЮЧЕНИИ плагина согласно пункту 1.1 архитектуры."""
        data = {"plugin_name": self.plugin_name}

        self.kafka_producer.send(self.init_plugin_topic, value=data).get(timeout=1)

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

        for message in kafka_consumer:
            message_json = message.value

            for key in message_json:
                assert key in ["status", "zipped_images_path"]

            yield message_json
