# Модуль для работы с плагинами
from threading import Thread
import os
from json import dumps,loads
from kafka import KafkaProducer, KafkaConsumer
import logging
from sessions import sessions_manager

# Флаг, заставляющий остановить фоновую задачу чтения из Kafka
stop_flag = False


class PluginsManager:
    """Класс для взаимодействия с плагинами"""

    def __init__(self):

        # Список активных плагинов.
        # Ключ - plugin_name
        self.plugins = {}

        # Продюсер Kafka для отправки сообщений плагинам
        self.kafka_producer = KafkaProducer(
            bootstrap_servers=os.getenv("KAFKA_BOOTSTRAP_SERVER"),
            value_serializer=lambda x: dumps(x).encode("utf-8")
        )

        # Консьюмеры Kafka для получения сообщений от плагинов
        self.kafka_start_plugins_consumer = KafkaConsumer("start-plugins",
            bootstrap_servers=os.getenv("KAFKA_BOOTSTRAP_SERVER"),
            value_deserializer=lambda x: loads(x.decode("utf-8")),
            consumer_timeout_ms=int(os.getenv("KAFKA_POLL_PERIOD"))*1000
        )
        self.kafka_processed_files_consumer = KafkaConsumer("processed-files",
            bootstrap_servers=os.getenv("KAFKA_BOOTSTRAP_SERVER"),
            value_deserializer=lambda x: loads(x.decode("utf-8")),
            consumer_timeout_ms=int(os.getenv("KAFKA_POLL_PERIOD"))*1000
        )

    def run(self):
        """
        Запускает фоновый поток постоянного
        чтения сообщений из Kafka
        :return:
        """
        Thread(target=self.__kafka_poll_start_plugins).start()
        Thread(target=self.__kafka_poll_processed_files).start()

    def stop(self):
        """
        Останавливает фоновый поток постоянного
        чтения сообщений из Kafka
        """
        global stop_flag
        stop_flag = True

    def get_plugins(self):
        """
        Возвращает список активных плагинов
        :return: Массив плагинов
        """
        return list(self.plugins.values())

    def send_message(self, plugin_name, message):
        """
        Отправляет сообщение плагину через Kafka
        :param plugin_name Имя плагина
        :param message Сообщение
        """
        self.kafka_producer.send(plugin_name+"-new-files", message).get(1)

    def __kafka_poll_start_plugins(self):
        """
        Функция обновляет список плагинов из Kafka
        """
        while True:
            if stop_flag:
                break
            try:
                for message in self.kafka_start_plugins_consumer:
                    if message.value.get("plugin_name"):
                        self.plugins[message.value["plugin_name"]] = message.value
            except Exception as e:
                logging.error(e)

    def __kafka_poll_processed_files(self):
        """
        Функция обновляет список результатов запросов пользователей из Kafka
        """
        while True:
            if stop_flag:
                break
            try:
                for message in self.kafka_processed_files_consumer:
                    if message.value.get("user_request_uid"):
                        session = sessions_manager.get(message.value.get("user_id"))
                        if session is not None:
                            session.set_result(message.value.get("user_request_uid"), message.value)
                sessions_manager.clean_sessions()
            except Exception as e:
                logging.error(e)


manager = PluginsManager()
