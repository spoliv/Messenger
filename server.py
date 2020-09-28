import os
import click
from click.exceptions import UsageError
import sys
import configparser
from common.functions import *
from server.core import MessageProcessor
from server.db_server import ServerStorage
from server.main_window import MainWindow
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt
sys.path.append('../')



server_logger = logging.getLogger('server')

# Флаг что был подключён новый пользователь, нужен чтобы не мучать BD
# постоянными запросами на обновление


def _show_usage_error(self):
    """ Функция перехвата оишибок, выдаваемых click при парсинге командной строки """
    if '-p' in self.format_message():
        server_logger.critical(
            f'Попытка запуска сервера с некорректными параметрами порта. \n'
            f'После параметра \'p\' необходимо указать номер порта и это должно быть целое число')
    elif '-a' in self.format_message():
        server_logger.critical(
            f'Попытка запуска сервера с некорректными параметрами адреса. \n'
            f'После параметра \'a\'- необходимо указать адрес, который будет слушать сервер.')


UsageError.show = _show_usage_error


def config_load():
    config = configparser.ConfigParser()
    #dir_path = os.path.dirname(os.path.realpath(__file__))
    dir_path = os.getcwd()
    config.read(f"{dir_path}/{'server.ini'}")
    # Если конфиг файл загружен правильно, запускаемся, иначе конфиг по
    # умолчанию.
    if 'SETTINGS' in config:
        return config
    else:
        config.add_section('SETTINGS')
        config.set('SETTINGS', 'Default_port', str(DEFAULT_PORT))
        config.set('SETTINGS', 'Listen_Address', '')
        config.set('SETTINGS', 'Database_path', '')
        config.set('SETTINGS', 'Database_file', 'server_database.db3')
        return config


@click.command()
@click.option('-p', default=int(config_load()['SETTINGS']['Default_port']))
@click.option('-a', default=config_load()['SETTINGS']['Listen_Address'])
@click.option('--no_gui')
def main(p, a, no_gui):
    # Загрузка файла конфигурации сервера
    config = config_load()
    listen_port = p
    listen_address = a
    gui_flag = no_gui
    # Инициализация базы данных
    database = ServerStorage(
        os.path.join(
            config['SETTINGS']['Database_path'],
            config['SETTINGS']['Database_file']))

    # Создание экземпляра класса - сервера и его запуск:
    server = MessageProcessor(listen_address, listen_port, database)
    server.daemon = True
    server.start()
    # Если  указан параметр без GUI то запускаем простенький обработчик
    # консольного ввода
    if gui_flag:
        while True:
            command = input('Введите exit для завершения работы сервера.')
            if command == 'exit':
                # Если выход, то завршаем основной цикл сервера.
                server.running = False
                server.join()
                break

    # Если не указан запуск без GUI, то запускаем GUI:
    else:
        # Создаём графическое окуружение для сервера:
        server_app = QApplication(sys.argv)
        server_app.setAttribute(Qt.AA_DisableWindowContextHelpButton)
        main_window = MainWindow(database, server, config)

        # Запускаем GUI
        server_app.exec_()

        # По закрытию окон останавливаем обработчик сообщений
        server.running = False


if __name__ == '__main__':
    main()
    #print(sys.path)
