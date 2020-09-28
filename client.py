import os
import click
import sys
from click.exceptions import UsageError
from Crypto.PublicKey import RSA
from PyQt5.QtWidgets import QApplication
from common.constants import *
from common.errors import ServerError
from client.database import ClientDatabase
from client.transport import ClientTransfer
from client.main_window import ClientMainWindow
from client.start_dialog import UserNameDialog


client_logger = logging.getLogger('client')




def _show_usage_error(self):
    """ Функция перехват оишибок, выдаваемых click при парсинге командной строки """
    if '--port' in self.format_message():
        client_logger.critical(
            f'Попытка запуска клиента с некорректными параметрами порта сервера. \n'
            f'После параметра -\'port\' необходимо указать номер порта сервера и это должно быть целое число')
    elif '--addr' in self.format_message():
        client_logger.critical(
            f'Попытка запуска клиента с некорректными параметрами адреса сервера. \n'
            f'После параметра \'addr\'- необходимо указать адрес сервера')


UsageError.show = _show_usage_error


@click.command()
@click.option('--port', type=int, default=DEFAULT_PORT)
@click.option('--addr', default=DEFAULT_ADDRESS)
@click.option('--name', '-n', default=None)
@click.option('--password', default='')
def main(port, addr, name, password):
    server_address = addr
    server_port = port
    client_name = name
    client_passwd = password
    print(client_name, password)

    if server_port < 1024 or server_port > 65535:
        client_logger.critical(
            f'Попытка запуска сервера с указанием неподходящего порта {server_port} сервера.'
            f'Допустимы адреса с 1024 до 65535.')
        sys.exit(1)
    # Создаём клиентокое приложение
    client_app = QApplication(sys.argv)

    #Если имя пользователя не было указано в командной строке то запросим его
    start_dialog = UserNameDialog()
    if not client_name or not client_passwd:
        client_app.exec_()
        # Если пользователь ввёл имя и нажал ОК, то сохраняем ведённое и удаляем объект, инааче выходим
        if start_dialog.ok_pressed:
            client_name = start_dialog.client_name.text()
            client_passwd = start_dialog.client_passwd.text()
        else:
            sys.exit(0)

    # Записываем логи
    client_logger.info(
        f'Запущен клиент с парамертами: адрес сервера: {server_address} , порт: {server_port}, имя пользователя: {client_name}')
    # Загружаем ключи с файла, если же файла нет, то генерируем новую пару.
    #dir_path = os.path.dirname(os.path.realpath(__file__))
    dir_path = os.getcwd()
    key_file = os.path.join(dir_path, f'{client_name}.key')
    if not os.path.exists(key_file):
        keys = RSA.generate(2048, os.urandom)
        with open(key_file, 'wb') as key:
            key.write(keys.export_key())
    else:
        with open(key_file, 'rb') as key:
            keys = RSA.import_key(key.read())

    keys.publickey().export_key()
    # Создаём объект базы данных
    database = ClientDatabase(client_name)

    # Создаём объект - транспорт и запускаем транспортный поток
    try:
        transfer = ClientTransfer(server_port, server_address, database, client_name, client_passwd, keys)
    except ServerError as error:
        print(error.text)
        sys.exit(1)
    transfer.setDaemon(True)
    transfer.start()

    # Удалим объект диалога за ненадобностью
    del start_dialog
    # Создаём GUI
    main_window = ClientMainWindow(database, transfer, keys)
    main_window.make_connection(transfer)
    main_window.setWindowTitle(f'Чат Программа alpha release - {client_name}')
    client_app.exec_()

    # Раз графическая оболочка закрылась, закрываем транспорт
    transfer.transfer_shutdown()
    transfer.join()
if __name__ == '__main__':
    main()