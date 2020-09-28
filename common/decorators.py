import socket
import inspect
import logging
import logs.config_client_log
import logs.config_server_log
import sys
sys.path.append('../')

# метод определения модуля, источника запуска.
if sys.argv[0].find('client') == -1:
    # если не клиент то сервер!
    logger = logging.getLogger('server')
else:
    # ну, раз не сервер, то клиент
    logger = logging.getLogger('client')


def log(func_to_log):
    '''
    Декоратор, выполняющий логирование вызовов функций.
    Сохраняет события типа debug, содержащие
    информацию о имени вызываемой функиции, параметры с которыми
    вызывается функция, и модуль, вызывающий функцию.
    '''
    def log_saver(*args, **kwargs):
        logger.debug(
            'Была вызвана функция {} c параметрами {} , {}. Вызов из модуля {}. Вызов из функции {}'.format(
                func_to_log.__name__,
                args,
                kwargs,
                func_to_log.__module__,
                inspect.stack()[1][3]))
        ret = func_to_log(*args, **kwargs)
        return ret
    return log_saver
# Функция проверки, что клиент авторизован на сервере
# Проверяет, что передаваемый объект сокета находится в списке клиентов.
# Если его там нет закрывает сокет


def login_required(func):
    '''
    Декоратор, проверяющий, что клиент авторизован на сервере.
    Проверяет, что передаваемый объект сокета находится в
    списке авторизованных клиентов.
    За исключением передачи словаря-запроса
    на авторизацию. Если клиент не авторизован,
    генерирует исключение TypeError
    '''
    def checker(*args, **kwargs):
        # Если первый аргумент - экземпляр MessageProcessor
        # А сокет в остальных аргументах
        # Импортить необходимо тут, иначе ошибка рекурсивного импорта.
        from server.core import MessageProcessor
        from common.constants import ACTION, PRESENCE
        if isinstance(args[0], MessageProcessor):
            found = False
            for arg in args:
                if isinstance(arg, socket.socket):
                    # Проверяем, что данный сокет есть в списке names класса
                    # MessageProcessor
                    for client in args[0].names:
                        if args[0].names[client] == arg:
                            found = True

            # Теперь надо проверить, что передаваемые аргументы не presence
            # сообщение
            for arg in args:
                if isinstance(arg, dict):
                    if ACTION in arg and arg[ACTION] == PRESENCE:
                        found = True
            # Если не авторизован и не сообщение начала авторизации, то
            # вызываем исключение.
            if not found:
                raise TypeError

        return func(*args, **kwargs)

    return checker
