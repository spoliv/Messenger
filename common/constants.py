import logging


DEFAULT_PORT = 7777
DEFAULT_ADDRESS = '127.0.0.1'
MAX_CONNECTED = 8
MAX_PACKAGE_SIZE = 1024
ENCODING = 'utf-8'
LOGGING_LEVEL = logging.DEBUG
#SERVER_DATABASE = 'sqlite:///server_base.db3'
# База данных для хранения данных сервера:
SERVER_CONFIG = 'server.ini'

# Ключи протокола JIM
ACTION = 'action'
TIME = 'time'
USER = 'user'
ACCOUNT_NAME = 'account_name'
PRESENCE = 'presence'
RESPONSE = 'response'
ERROR = 'error'
MESSAGE = 'message'
MESSAGE_TEXT = 'mess_text'
CHAT = 'chat'
CHAT_TEXT = 'chat_text'
SENDER = 'from'
DESTINATION = 'to'
EXIT = 'exit'
GET_CONTACTS = 'get_contacts'
GET_CHAT_MESSG = 'get_chat_messages'
LIST_INFO = 'data_list'
REMOVE_CONTACT = 'remove'
ADD_CONTACT = 'add'
USERS_REQUEST = 'get_users'
DATA = 'bin'
PUBLIC_KEY = 'pubkey'
PUBLIC_KEY_REQUEST = 'pubkey_need'


# Словари - ответы:
# 200
RESPONSE_200 = {RESPONSE: 200}
# 400
# 202
RESPONSE_202 = {RESPONSE: 202,
                LIST_INFO:None
                }
RESPONSE_400 = {
    RESPONSE: 400,
    ERROR: None
}

# 205
RESPONSE_205 = {
    RESPONSE: 205
}

# 511
RESPONSE_511 = {
    RESPONSE: 511,
    DATA: None
}
