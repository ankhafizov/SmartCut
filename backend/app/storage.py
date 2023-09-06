# Модуль для работы с файловым хранилищем
import os
import shutil

# Корень хранилища в бэкенде
STORAGE_ROOT = "/data"


def save_file(path, filename, file):
    """
    Сохраняет в хранилище указанный файл
    :param path: Путь назначения относительно корня
    :param filename: Имя файла
    :param file: Тело файла
    :return:
    """
    if not os.path.isdir(os.path.join(STORAGE_ROOT, path)):
        os.makedirs(os.path.join(STORAGE_ROOT, path))
    with open(os.path.join(STORAGE_ROOT, path, filename), "wb") as buffer:
        shutil.copyfileobj(file, buffer)
