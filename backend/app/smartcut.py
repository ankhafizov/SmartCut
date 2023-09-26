import os
import uvicorn
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from plugins import manager
from storage import save_file

app = FastAPI()


def main():
    manager.run()
    uvicorn.run(app, host="0.0.0.0", port=8080)


@app.get("/api/plugins")
async def get_plugins():
    """
    Возвращает фронтенду список активных плагинов
    """
    return manager.get_plugins()


@app.post("/api/upload_zip")
async def upload_zip(
        user_request_uid: str = Form(),
        video_file_name: str = Form(),
        plugin_name: str = Form(),
        zip: UploadFile = File(),
        is_last: bool = Form()):
    """
    Принимает zip-файл с кадрами из фронтенда и сохраняет его в хранилище
    и оповещаяет плагин о загрузке файла, отправляя сообщение в Kafka
    :param user_request_uid: Идентификатор запроса
    :param video_file_name: Имя видео-файла
    :param plugin_name: Имя плагина
    :param zip: Тело zip-архива
    :param is_last: Является ли данный zip-файл последним для данного видео-файла
    :return:
    """
    path = os.path.join(user_request_uid, video_file_name)
    try:
        save_file(path, zip.filename, zip.file)
        if is_last:
            manager.send_message(plugin_name, {
                "status": "uploaded",
                "user_id": "user_id1",
                "zipped_chunks_path": path
            })
        else:
            manager.send_message(plugin_name, {
                "status": "in-progress",
                "user_id": "user_id1",
                "last_zipped_chunk_path": path + "/" + zip.filename
             })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return {"status": "ok"}


@app.get("/api/get_video_intervals/{uid}")
async def get_video_intervals(uid):
    """
    Запрашивает результат обработки видео для указанного идентификатора запроса
    :param uid: Идентификатор запроса
    :return:
    """
    result = manager.get_result(uid)
    if result is None:
        raise HTTPException(status_code=404, detail="Item not found")
    else:
        return result


@app.on_event('shutdown')
def shutdown_event():
    """
    При завершении работы FastAPI, завершает все остальные фоновые процессы
    :return:
    """
    manager.stop()


main()
