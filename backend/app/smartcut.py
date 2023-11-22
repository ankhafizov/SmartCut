import os
import uvicorn
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Request, Response
from storage import save_file
from sessions import sessions_manager
from plugins import plugins_manager

app = FastAPI()


def main():
    plugins_manager.run()
    sessions_manager.run()
    uvicorn.run(app, host="0.0.0.0", port=8080)


@app.get("/api/auth")
async def create_session(request: Request, response: Response):
    """
    Аутентифицирует пользователя и создает сеанс для него
    """
    try:
        session = get_session(request)
        return {"status": "ok"}
    except HTTPException:
        ip = request.headers.get(os.getenv("CLIENT_IP_HEADER"))
        session = sessions_manager.create(ip)
        response.set_cookie("session_id", session.id, max_age=3600*24*30, path="/", httponly=True, samesite="strict")
        return response.render(None)


@app.get("/api/plugins")
async def get_plugins(request: Request):
    """
    Возвращает фронтенду список активных плагинов
    :param request: HTTP запрос из браузера
    """
    get_session(request)
    return plugins_manager.get_plugins()


@app.get("/api/create_request/{user_request_uid}")
async def create_request(user_request_uid, request: Request):
    """
    Открывает запрос на отправку видео и
    добавляет его в сеанс пользователя,
    если это разрешено
    :param user_request_uid: Идентификатор запроса
    :param request: HTTP запрос из браузера
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
        archive: UploadFile = File(),
        is_last: bool = Form()):
    """
    Принимает zip-файл с кадрами из фронтенда и сохраняет его в хранилище
    и оповещаяет плагин о загрузке файла, отправляя сообщение в Kafka
    :param request: HTTP запрос из браузера
    :param user_request_uid: Идентификатор запроса
    :param video_file_name: Имя видео-файла
    :param plugin_name: Имя плагина
    :param archive: Тело zip-архива
    :param is_last: Является ли данный zip-файл последним для данного видео-файла
    """
    session = get_session(request)

    path = os.path.join(user_request_uid, video_file_name)
    try:
        request = session.get_request(user_request_uid)
        if request is None:
            raise HTTPException(status_code=500, detail="Запрос не найден !")
        if archive.filename[-4:] != ".zip":
            raise HTTPException(status_code=500, detail="Ошибка в формате файла !")
        save_file(path, archive.filename, archive.file)
        session.report_request_activity(user_request_uid)
        plugins_manager.send_message(plugin_name, {
            "status": "in-progress",
            "user_id": session.id,
            "last_zipped_chunk_path": path + "/" + archive.filename
        })
        if is_last:
            plugins_manager.send_message(plugin_name, {
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
        return {"processed_chunks": request["processed_chunks"]}
    else:
        session.delete_request(uid)
    return result


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


main()
