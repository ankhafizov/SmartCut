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


def remove_folder(path):
    """
    Удаляет указанную папку из хранилища
    вместе со всем содержимым
    :param path: Путь к папке относительно корня
    """
    if os.path.isdir(os.path.join(STORAGE_ROOT, path)):
        shutil.rmtree(os.path.join(STORAGE_ROOT, path), ignore_errors=True)
