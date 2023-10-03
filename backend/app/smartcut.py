import os
import uvicorn
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Request, Response
from plugins import manager
from storage import save_file
from sessions import sessions_manager

app = FastAPI()


def main():
    manager.run()
    uvicorn.run(app, host="0.0.0.0", port=8080)


@app.get("/api/auth")
async def create_session(request: Request, response: Response):
    """
    Аутентифицирует пользователя и создает сеанс для него
    """
    try:
        get_session(request)
        return {"status": "ok"}
    except:
        session = sessions_manager.create()
        response.set_cookie("session_id", session.id, max_age=3600*24*30, path="/", httponly=True)
        return response.render(None)


def get_session(request):
    """
    По входящему HTTP-запросу определяет
    к какому сеансу пользователя он относится
    и возвращает объект этого сеанса
    :return: сеанс пользователя
    """
    session = sessions_manager.get(request.cookies.get("session_id"))
    if session is None:
        raise HTTPException(status_code=403, detail="Ошибка авторизации !")
    return session


@app.get("/api/plugins")
async def get_plugins(request: Request):
    """
    Возвращает фронтенду список активных плагинов
    :param request: HTTP запрос из браузера
    """
    get_session(request)
    return manager.get_plugins()


@app.get("/api/create_request/{user_request_uid}")
async def create_request(user_request_uid, request: Request):
    """
    Открывает запрос на отправку видео и
    добавляет его в сеанс пользователя,
    если это разрешено
    :param user_request_uid: Идентификатор запроса
    """
    session = get_session(request)
    if len(session.requests) >= session.user_requests_limit:
        raise HTTPException(status_code=500, detail="Слишком много активных запросов !")
    session.add_request(user_request_uid)
    return {"status": "ok"}


@app.post("/api/upload_zip")
async def upload_zip(
        request: Request,
        user_request_uid: str = Form(),
        video_file_name: str = Form(),
        plugin_name: str = Form(),
        zip: UploadFile = File(),
        is_last: bool = Form()):
    """
    Принимает zip-файл с кадрами из фронтенда и сохраняет его в хранилище
    и оповещаяет плагин о загрузке файла, отправляя сообщение в Kafka
    :param request: HTTP запрос из браузера
    :param user_request_uid: Идентификатор запроса
    :param video_file_name: Имя видео-файла
    :param plugin_name: Имя плагина
    :param zip: Тело zip-архива
    :param is_last: Является ли данный zip-файл последним для данного видео-файла
    """
    session = get_session(request)

    path = os.path.join(user_request_uid, video_file_name)
    try:
        save_file(path, zip.filename, zip.file)
        request = session.get_request(user_request_uid)
        if request is None:
            raise HTTPException(status_code=500, detail="Запрос не найден !")
        manager.send_message(plugin_name, {
            "status": "in-progress",
            "user_id": session.id,
            "last_zipped_chunk_path": path + "/" + zip.filename
        })
        if is_last:
            manager.send_message(plugin_name, {
                "status": "uploaded",
                "user_id": session.id,
                "zipped_chunks_path": path
            })
        return {"processed_chunks": request["processed_chunks"]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))




@app.get("/api/get_video_intervals/{uid}")
async def get_video_intervals(uid, request: Request):
    """
    Запрашивает результат обработки видео для указанного идентификатора запроса
    :param uid: Идентификатор запроса
    :param request: HTTP запрос из браузера
    """
    session = get_session(request)
    request = session.get_request(uid)
    if request is None:
        raise HTTPException(status_code=500, detail="Запрос не найден")
    result = session.get_result(uid)
    if result is None:
        return {"processed_chunks":request["processed_chunks"]}
    session.delete_request(uid)
    return result


@app.on_event('shutdown')
def shutdown_event():
    """
    При завершении работы FastAPI, завершает все остальные фоновые процессы
    """
    manager.stop()


main()
