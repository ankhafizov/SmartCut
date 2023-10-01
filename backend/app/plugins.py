# Модуль для работы с плагинами
from threading import Thread
import time
import os
from json import dumps,loads
from kafka import KafkaProducer, KafkaConsumer
import logging

# Флаг, заставляющий остановить фоновую задачу чтения из Kafka
stop_flag = False


class PluginsManager:
    """Класс для взаимодействия с плагинами"""

    def __init__(self):

        # Список активных плагинов.
        # Ключ - plugin_name
        self.plugins = {}

        # Кэш результатов запросов пользователей
        # Ключ - user_request_id
        self.results = {}

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

        # Максимальное время хранения результата запроса пользователя в кэше (секунды)
        self.RESULT_TIME_TO_LIVE = int(os.getenv("RESULT_TIME_TO_LIVE"))

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

    def get_result(self, uid):
        """
        Возвращает результат обработки видео по указанному
        идентификатору запроса
        :param uid: Идентификатор запроса пользователя
        :return: Результат запроса как JSON или ничего
        """
        if self.results.get(uid):
            return self.results[uid]
        else:
            return None

    def __kafka_poll_start_plugins(self):
        """
        Функция обновляет список плагинов из Kafka
        :return:
        """
        while True:
            if stop_flag:
                break
            try:
                for message in self.kafka_start_plugins_consumer:
                    if message.value.get("plugin_name"):
                        self.plugins[message.value["plugin_name"]] = message.value
                self.__clean_results()
            except Exception as e:
                logging.error(e)

    def __kafka_poll_processed_files(self):
        """
        Функция обновляет список результатов запросов пользователей из Kafka
        :return:
        """
        while True:
            if stop_flag:
                break
            try:
                for message in self.kafka_processed_files_consumer:
                    if message.value.get("user_request_uid"):
                        self.results[message.value["user_request_uid"]] = message.value
                        self.results[message.value["user_request_uid"]]["time"] = time.time()
                self.__clean_results()
            except Exception as e:
                logging.error(e)

    def __clean_results(self):
        """
        Очищает кэш результатов запросов пользователей
        Удаляет результаты, которые пользователи не забирают
        слишком долго (дольше чем self.RESULT_TIME_TO_LIVE)
        """
        for key in list(self.results):
            if time.time() - self.results[key]["time"] > self.RESULT_TIME_TO_LIVE:
                del self.results[key]


manager = PluginsManager()