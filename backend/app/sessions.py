from uuid import uuid4
import os
import time
from storage import remove_folder
from threading import Thread
import logging


class Session:
    """
    Сеанс пользователя
    """
    def __init__(self, ip):
        # Идентификатор сеанса
        self.id = str(uuid4())

        # IP-адрес клиента
        self.ip = ip

        # Список активных запросов
        # Ключ: user_request_uid
        self.requests = {}

        # Максимальное количество запросов пользователя в очереди
        self.user_requests_limit = int(os.getenv("USER_REQUESTS_LIMIT"))

        # Время последней активности пользователя в сеансе
        self.last_activity_time = time.time()

    def add_request(self, request_id):
        """
        Добавляет запрос в список
        :param request_id: Идентификатор запроса
        :return: Созданный запрос пользователя
        """
        request = self.requests.get(request_id)
        if request:
            return request
        self.last_activity_time = time.time()
        self.requests[request_id] = {
            "result": None,
            "last_activity_time": time.time(),
            "processed_chunks": 0
        }
        return self.requests[request_id]

    def delete_request(self, request_id):
        """
        Удаляет запрос из списка
        :param request_id: Идентификатор запроса
        """
        self.last_activity_time = time.time()
        del self.requests[request_id]
        remove_folder(request_id)

    def get_request(self, request_id):
        """
        Возвращает запрос с указанным идентификатором
        :param request_id: Идентификатор запроса
        :return: Запрос пользователя
        """
        self.last_activity_time = time.time()
        return self.requests.get(request_id)

    def get_result(self, request_id):
        """
        Возвращает результат запроса с указанным идентификатором
        или None
        :param request_id: Идентификатор запроса
        :return: Результат запроса пользователя
        """
        if self.requests.get(request_id):
            return self.requests[request_id]["result"]

    def set_result(self, request_id, result):
        """
        Записывает результат для запроса с указанным идентификатором
        :param request_id: Идентификатор запроса
        :param result: Результат запроса
        """
        if self.requests.get(request_id):
            self.last_activity_time = time.time()
            self.requests[request_id]["last_activity_time"] = time.time()
            if "timestamps" in result:
                self.requests[request_id]["result"] = result
            elif result.get("processed_chunk"):
                self.requests[request_id]["processed_chunks"] += 1
                
    def report_request_activity(self, request_id):
        """
        Обновляет время последней активности запроса
        :param request_id: Идентификатор запроса
        """
        if self.requests.get(request_id):
            self.last_activity_time = time.time()
            self.requests[request_id]["last_activity_time"] = time.time()


class SessionsManager:
    """ Менеджер сеансов пользователей"""
    def __init__(self):
        # Список активных сеансов пользователей
        # Ключ: user_id
        self.sessions = {}

        # Максимальное время неактивности сеанса
        self.session_timeout = int(os.getenv("SESSION_TIMEOUT"))
        # Максимальное время обработки запроса
        self.request_timeout = int(os.getenv("REQUEST_TIMEOUT"))
        # Максимальное время хранения результата запроса
        self.result_timeout = int(os.getenv("RESULT_TIMEOUT"))

    def run(self):
        """
        Запускает фоновый поток постоянной
        проверки сеансов пользователей
        :return:
        """
        Thread(target=self.__clean_sessions).start()
        
    def create(self, ip):
        """
        Создает сеанс пользователя
        или если уже есть сеанс с таким IP-адресом,
        то возвращает его
        :param ip: IP-адрес клиента
        :return: Сеанс пользователя
        """
        session = self.get_by_ip(ip)
        if session is None:
            session = Session(ip)
            self.sessions[session.id] = session
        return session

    def get(self, session_id):
        """
        Возвращает сеанс пользователя по идентификатору
        :param session_id: Идентификатор сеанса
        :return: Сеанс пользователя
        """
        session = self.sessions.get(session_id)
        if session:
            session.last_activity_time = time.time()
            return session

    def get_by_ip(self, ip):
        """
        Выполняет поиск сеанса с указанным IP-адресом
        то возвращает его
        :param ip: IP-адрес клиента
        :return: Сеанс пользователя
        """
        for session in self.sessions.values():
            if session.ip == ip:
                return session

    def delete(self, session_id):
        """
        Удаляет сеанс пользователя с указанным идентификатором
        :param session_id: Идентификатор пользователя
        """
        del self.sessions[session_id]

    def __clean_sessions(self):
        """
        Удаляет неактивные сеансы и запросы
        для которых не поступили результаты
        """
        while True:
            try:
                for session_id in list(self.sessions):
                    if time.time() - self.sessions[session_id].last_activity_time > self.session_timeout:
                        self.delete(session_id)
                    else:
                        self.__clean_session_requests(self.sessions[session_id])
            except Exception as e:
                logging.error(f"Sessions cleanup error: {str(e)}")
            time.sleep(5)

    def __clean_session_requests(self, session):
        """
        Удаляет неактивные запросы из указанного сеанса
        :param session: Сеанс пользователя
        """
        for request_id in list(session.requests):
            request = session.requests[request_id]
            if request["result"] is None:
                if time.time() - request["last_activity_time"] > self.request_timeout:
                    session.delete_request(request_id)
            elif time.time() - request["last_activity_time"] > self.result_timeout:
                session.delete_request(request_id)


sessions_manager = SessionsManager()
