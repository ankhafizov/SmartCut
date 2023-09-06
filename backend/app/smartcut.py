import os
import uvicorn
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from plugins import get_plugins_list, run_update_plugins_list, stop_update_plugins_list, get_result
from storage import save_file

app = FastAPI()


def main():
    run_update_plugins_list()
    uvicorn.run(app, host="0.0.0.0", port=8080)


@app.get("/api/plugins")
async def get_plugins():
    """
    Возвращает фронтенду список активных плагинов
    """
    return get_plugins_list()


@app.post("/api/upload_zip")
async def upload_zip(
        uid: str = Form(),
        video_file_name: str = Form(),
        zip: UploadFile = File()):
    """
    Принимает zip-файл с кадрами из фронтенда и сохраняет его в хранилище
    :param uid: Идентификатор запроса
    :param video_file_name: Имя видео-файла
    :param zip: Тело zip-архива
    :return:
    """
    save_file(os.path.join(uid, video_file_name), zip.filename, zip.file)
    return {"status": "ok"}


@app.get("/api/post_video_to_plugin/{uid}/{plugin_name}/{video_file_name}")
async def post_video_to_plugin(uid, plugin_name, video_file_name):
    """
    Ставит задачу плагину начать обработку загруженного видео
    (Пока ничего не делает)
    :param uid: Идентификатор запроса
    :param plugin_name: Имя плагина
    :param video_file_name: Имя видео-файла
    :return:
    """
    return {"uid": uid, "plugin_name": plugin_name, "video_file_name": video_file_name}


@app.get("/api/get_video_intervals/{uid}")
async def get_video_intervals(uid):
    """
    Запрашивает результат обработки для указанного идентификатора запроса
    (Пока возвращает статические данные)
    :param uid: Идентификатор запроса
    :return:
    """
    result = get_result(uid)
    if result == None:
        raise HTTPException(status_code=404, detail="Item not found")
    else:
        return result


@app.on_event('shutdown')
def shutdown_event():
    """
    При завершении работы FastAPI, завершает все остальные фоновые процессы
    :return:
    """
    stop_update_plugins_list()


main()
