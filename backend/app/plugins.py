# Модуль для работы с плагинами
from threading import Thread
import time

# Список активных плагинов
plugins_list = [
    {"plugin_name": "plugin1", "label": "плагин 1", "size": 640},
    {"plugin_name": "plugin2", "label": "плагин 2", "size": 244}
]

# Список результатов обработки видео. В качестве ключей используются
# идентификаторы запросов (uid)
results = {}

# Периодичность обновления списка активных плагинов
UPDATE_PLUGINS_PERIOD = 5

# Флаг, заставляющий остановить фоновую задачу обновления списка плагинов
stop_flag = False


def get_plugins_list():
    """
    Возвращает список активных плагинов
    :return:
    """
    return plugins_list

def update_plugins_list():
    """
    Функция обновления списка активных плагинов
    Запускает процедуру обновления периодически
    (Пока ничего не делает)
    :return:
    """
    while True:
        if (stop_flag):
            return
        time.sleep(UPDATE_PLUGINS_PERIOD)


thread = Thread(target=update_plugins_list)

def run_update_plugins_list():
    """
    Запускает фоновый поток постоянного
    обновления списка активных плагинов
    :return:
    """
    thread.start()


def stop_update_plugins_list():
    """
    Останавливет фоновый поток обновления списка
    активных плагинов
    :return:
    """
    global stop_flag
    stop_flag = True


def update_results():
    """
    Запрашивает результаты обработки видео запросов
    и обновляет словарь "results"
    (Пока ничего не делает)
    """
    pass


def get_result(uid):
    """
    Возвращает результат обработки видео по указанному
    идентификатору запроса
    (Пока возвращает статические данные)
    :param uid: Идентификатор запроса
    :return:
    """
    return {
        "user_id": "user_id1",
        "video_name": "video_name1",
        "plugin_name": "plugin1",
        "timestamps": [
            {"start": 10, "stop": 30},
            {"start": 60, "stop": 90},
            {"start": 120, "stop": 150}
        ]
}
