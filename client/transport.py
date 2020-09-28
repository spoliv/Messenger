from common.decorators import log
from common.errors import ServerError
from common.constants import *
from common.functions import *
import socket
import sys
import time
import logging
import binascii
import threading
import hashlib
import hmac
from PyQt5.QtCore import pyqtSignal, QObject

sys.path.append('../')

# Логер и объект блокировки для работы с сокетом.
client_logger = logging.getLogger('client')
socket_lock = threading.Lock()


# Класс - Траннспорт, отвечает за взаимодействие с сервером
class ClientTransfer(threading.Thread, QObject):
    # Сигналы новое сообщение и потеря соединения
    new_message = pyqtSignal(dict)
    message_205 = pyqtSignal()
    connection_lost = pyqtSignal()

    def __init__(self, port, ip_address, database, username, passwd, keys):
        # Вызываем конструктор предка
        threading.Thread.__init__(self)
        QObject.__init__(self)

        # Класс База данных - работа с базой
        self.database = database
        # Имя пользователя
        self.username = username
        # Пароль
        self.password = passwd
        # Сокет для работы с сервером
        self.transfer_socket = None
        # Набор ключей для шифрования
        self.keys = keys
        # Устанавливаем соединение:
        self.connection_init(port, ip_address)
        # Обновляем таблицы известных пользователей и контактов
        try:
            self.user_list_update()
            self.contacts_list_update()
        except OSError as err:
            if err.errno:
                client_logger.critical(f'Потеряно соединение с сервером.')
                raise ServerError('Потеряно соединение с сервером!')
            client_logger.error(
                'Timeout соединения при обновлении списков пользователей.')
        except json.JSONDecodeError:
            client_logger.critical(f'Потеряно соединение с сервером.')
            raise ServerError('Потеряно соединение с сервером!')
            # Флаг продолжения работы транспорта.
        self.running = True

        #self.create_message_for_chat()

    # Функция инициализации соединения с сервером
    @log
    def connection_init(self, port, ip):
        # Инициализация сокета и сообщение серверу о нашем появлении
        self.transfer_socket = socket.socket(
            socket.AF_INET, socket.SOCK_STREAM)

        # Таймаут необходим для освобождения сокета.
        self.transfer_socket.settimeout(5)

        # Соединяемся, 5 попыток соединения, флаг успеха ставим в True если
        # удалось
        connected = False
        for i in range(5):
            client_logger.info(f'Попытка подключения №{i + 1}')
            try:
                self.transfer_socket.connect((ip, port))
            except (OSError, ConnectionRefusedError):
                pass
            else:
                connected = True
                break
            time.sleep(1)

        # Если соединится не удалось - исключение
        if not connected:
            client_logger.critical(
                'Не удалось установить соединение с сервером')
            raise ServerError('Не удалось установить соединение с сервером')

        client_logger.debug('Установлено соединение с сервером')

        # Запускаем процедуру авторизации
        # Получаем хэш пароля
        passwd_bytes = self.password.encode('utf-8')
        salt = self.username.lower().encode('utf-8')
        passwd_hash = hashlib.pbkdf2_hmac('sha512', passwd_bytes, salt, 10000)
        passwd_hash_string = binascii.hexlify(passwd_hash)

        # Получаем публичный ключ и декодируем его из байтов
        pubkey = self.keys.publickey().export_key().decode('ascii')

        # Авторизируемся на сервере
        with socket_lock:
            presense = {
                ACTION: PRESENCE,
                TIME: time.time(),
                USER: {
                    ACCOUNT_NAME: self.username,
                    PUBLIC_KEY: pubkey
                }
            }
            # Отправляем серверу приветственное сообщение.
            try:
                send_message(self.transfer_socket, presense)
                ans = get_message(self.transfer_socket)
                # Если сервер вернул ошибку, бросаем исключение.
                if RESPONSE in ans:
                    if ans[RESPONSE] == 400:
                        raise ServerError(ans[ERROR])
                    elif ans[RESPONSE] == 511:
                        # Если всё нормально, то продолжаем процедуру
                        # авторизации.
                        ans_data = ans[DATA]
                        hash = hmac.new(
                            passwd_hash_string, ans_data.encode('utf-8'))
                        digest = hash.digest()
                        my_ans = RESPONSE_511
                        my_ans[DATA] = binascii.b2a_base64(
                            digest).decode('ascii')
                        send_message(self.transfer_socket, my_ans)
                        self.proc_answer(get_message(self.transfer_socket))
            except (OSError, json.JSONDecodeError):
                raise ServerError('Сбой соединения в процессе авторизации.')

    @log
    def proc_answer(self, message):
        client_logger.debug(f'Разбор сообщения от сервера: {message}')

        # Если это подтверждение чего-либо
        if RESPONSE in message:
            if message[RESPONSE] == 200:
                return
            elif message[RESPONSE] == 400:
                raise ServerError(f'{message[ERROR]}')
            elif message[RESPONSE] == 205:
                self.user_list_update()
                self.contacts_list_update()
                self.message_205.emit()
            else:
                client_logger.debug(
                    f'Принят неизвестный код подтверждения {message[RESPONSE]}')

        # Если это сообщение от пользователя добавляем в базу, даём сигнал о
        # новом сообщении
        elif ACTION in message and message[ACTION] == MESSAGE and SENDER in message and DESTINATION in message \
                and MESSAGE_TEXT in message and message[DESTINATION] == self.username:
            client_logger.debug(
                f'Получено сообщение от пользователя {message[SENDER]}:{message[MESSAGE_TEXT]}')
            #self.database.save_message(message[SENDER], 'in', message[MESSAGE_TEXT])
            self.new_message.emit(message)

        # Если это сообщение отправлено в чат, то даем сигнал о новом сообщении в чат
        # elif ACTION in message and message[ACTION] == MESSAGE and SENDER in message and DESTINATION in message \
        #         and MESSAGE_TEXT in message and message[DESTINATION] == 'all':
        #     print(f'Сообщение от {message[SENDER]}:{message[MESSAGE_TEXT]}')



    # Функция обновляющая контакт - лист с сервера
    @log
    def contacts_list_update(self):
        client_logger.debug(
            f'Запрос контакт листа для пользователся {self.name}')
        req = {
            ACTION: GET_CONTACTS,
            TIME: time.time(),
            USER: self.username
        }
        client_logger.debug(f'Сформирован запрос {req}')
        with socket_lock:
            send_message(self.transfer_socket, req)
            ans = get_message(self.transfer_socket)
        client_logger.debug(f'Получен ответ {ans}')
        if RESPONSE in ans and ans[RESPONSE] == 202:
            for contact in ans[LIST_INFO]:
                self.database.add_contact(contact)
        else:
            client_logger.error('Не удалось обновить список контактов.')

    # Функция обновления таблицы известных пользователей.
    @log
    def user_list_update(self):
        client_logger.debug(
            f'Запрос списка известных пользователей {self.username}')
        req = {
            ACTION: USERS_REQUEST,
            TIME: time.time(),
            ACCOUNT_NAME: self.username
        }
        with socket_lock:
            send_message(self.transfer_socket, req)
            ans = get_message(self.transfer_socket)
        if RESPONSE in ans and ans[RESPONSE] == 202:
            self.database.add_users(ans[LIST_INFO])
        else:
            client_logger.error(
                'Не удалось обновить список известных пользователей.')

    # Функция запроса открытого ключа клиента с сервера.
    @log
    def key_request(self, user):
        client_logger.debug(f'Запрос публичного ключа для {user}')
        req = {
            ACTION: PUBLIC_KEY_REQUEST,
            TIME: time.time(),
            ACCOUNT_NAME: user
        }
        with socket_lock:
            send_message(self.transfer_socket, req)
            ans = get_message(self.transfer_socket)
        if RESPONSE in ans and ans[RESPONSE] == 511:
            return ans[DATA]
        else:
            client_logger.error(f'Не удалось получить ключ собеседника{user}.')
    # Функция сообщающая на сервер о добавлении нового контакта
    @log
    def add_contact(self, contact):
        client_logger.debug(f'Создание контакта {contact}')
        req = {
            ACTION: ADD_CONTACT,
            TIME: time.time(),
            USER: self.username,
            ACCOUNT_NAME: contact
        }
        with socket_lock:
            send_message(self.transfer_socket, req)
            self.proc_answer(get_message(self.transfer_socket))

    # Функция удаления клиента на сервере
    @log
    def remove_contact(self, contact):
        client_logger.debug(f'Удаление контакта {contact}')
        req = {
            ACTION: REMOVE_CONTACT,
            TIME: time.time(),
            USER: self.username,
            ACCOUNT_NAME: contact
        }
        with socket_lock:
            send_message(self.transfer_socket, req)
            self.proc_answer(get_message(self.transfer_socket))

    # Функция закрытия соединения, отправляет сообщение о выходе.
    @log
    def transfer_shutdown(self):
        self.running = False
        message = {
            ACTION: EXIT,
            TIME: time.time(),
            ACCOUNT_NAME: self.username
        }
        with socket_lock:
            try:
                send_message(self.transfer_socket, message)
            except OSError:
                pass
        client_logger.debug('Транспорт завершает работу.')
        time.sleep(0.5)

    # Функция отправки сообщения на сервер
    @log
    def send_message(self, to, message):
        message_dict = {
            ACTION: MESSAGE,
            SENDER: self.username,
            DESTINATION: to,
            TIME: time.time(),
            MESSAGE_TEXT: message
        }
        client_logger.debug(f'Сформирован словарь сообщения: {message_dict}')

        # Необходимо дождаться освобождения сокета для отправки сообщения
        with socket_lock:
            send_message(self.transfer_socket, message_dict)
            self.proc_answer(get_message(self.transfer_socket))
            client_logger.info(f'Отправлено сообщение для пользователя {to}')

    def send_message_to_chat(self, message):
        message_dict = {
            ACTION: CHAT,
            SENDER: self.username,
            TIME: time.time(),
            CHAT_TEXT: message
        }
        client_logger.debug(f'Сформирован словарь сообщения: {message_dict}')

        # Необходимо дождаться освобождения сокета для отправки сообщения
        with socket_lock:
            send_message(self.transfer_socket, message_dict)
            self.proc_answer(get_message(self.transfer_socket))
            client_logger.info(f'Отправлено сообщение в чат')

    def get_chat_message(self):
        req = {
            ACTION: GET_CHAT_MESSG,
            TIME: time.time(),
            USER: self.username,
        }
        client_logger.debug(f'Сформирован запрс: {req}')

        # Необходимо дождаться освобождения сокета для отправки сообщения
        with socket_lock:
            send_message(self.transfer_socket, req)
            ans = get_message(self.transfer_socket)
        client_logger.debug(f'Получен ответ {ans}')
        if RESPONSE in ans and ans[RESPONSE] == 202:
            return ans[LIST_INFO]
            # for contact in ans[LIST_INFO]:
            #     print(contact[0])
            #     print(contact[1])
            #     self.database.add_contact(contact)
        else:
            client_logger.error('Не удалось обновить список контактов.')






    def run(self):
        client_logger.debug('Запущен процесс - приёмник собщений с сервера.')
        while self.running:
            # Отдыхаем секунду и снова пробуем захватить сокет.
            # если не сделать тут задержку, то отправка может достаточно долго
            # ждать освобождения сокета.
            time.sleep(1)
            message = None
            with socket_lock:
                try:
                    self.transfer_socket.settimeout(0.5)
                    message = get_message(self.transfer_socket)
                except OSError as err:
                    if err.errno:
                        client_logger.critical(
                            f'Потеряно соединение с сервером.')
                        self.running = False
                        self.connection_lost.emit()
                # Проблемы с соединением
                except (ConnectionError, ConnectionAbortedError, ConnectionResetError, json.JSONDecodeError, TypeError):
                    client_logger.debug(f'Потеряно соединение с сервером.')
                    self.running = False
                    self.connection_lost.emit()
                finally:
                    self.transfer_socket.settimeout(5)
            # Если сообщение получено, то вызываем функцию обработчик:
            if message:
                client_logger.debug(f'Принято сообщение с сервера: {message}')
                self.proc_answer(message)
