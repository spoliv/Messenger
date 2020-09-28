from common.constants import *
from common.errors import ServerError
from client.start_dialog import UserNameDialog
from client.transport import ClientTransfer, send_message
from client.database import ClientDatabase
from client.del_contact import DelContactDialog
from client.add_contact import AddContactDialog
from client.main_window_conv import Ui_MainClientWindow
from PyQt5.QtWidgets import (
    QMainWindow,
    qApp,
    QMessageBox,
    QApplication,
    QListView,
    QAction,
    QTextEdit,
    QFileDialog,
    QPushButton,
    QLabel,
    QHBoxLayout)
from PyQt5.QtGui import QStandardItemModel, QStandardItem, QBrush, QColor, QIcon, QFont, QPixmap
from PyQt5.QtCore import pyqtSlot, QEvent, Qt, QRect
from Crypto.Cipher import PKCS1_OAEP
from Crypto.PublicKey import RSA
from PIL import Image
import sys
import json
import logging
import time
import base64

sys.path.append('../')

client_logger = logging.getLogger('client')


# Класс основного окна
class ClientMainWindow(QMainWindow):
    def __init__(self, database, transport, keys):
        super().__init__()
        # основные переменные
        self.database = database
        self.transport = transport

        # объект - дешифорвщик сообщений с предзагруженным ключём
        self.decrypter = PKCS1_OAEP.new(keys)

        # Загружаем конфигурацию окна из дизайнера
        self.ui = Ui_MainClientWindow()
        self.ui.setupUi(self)

        # Кнопка "Выход"
        self.ui.menu_exit.triggered.connect(qApp.exit)

        # Кнопка отправить сообщение
        self.ui.btn_send.clicked.connect(self.send_message)

        # "добавить контакт"
        self.ui.btn_add_contact.clicked.connect(self.add_contact_window)
        self.ui.menu_add_contact.triggered.connect(self.add_contact_window)

        # Удалить контакт
        self.ui.btn_remove_contact.clicked.connect(self.delete_contact_window)
        self.ui.menu_del_contact.triggered.connect(self.delete_contact_window)

        # Добавить аватар или выбрать из БД клиента
        self.ui.menu_add_avatar.triggered.connect(self.add_avat_user)
        self.ui.menu_select_avatar.triggered.connect(self.sel_avat_user)
        # Выбрать аватар
        # self.ui.btn_avatar.clicked.connect(self.select_avatar)

        # Кнопка Перейти в чат
        self.ui.btn_chat.clicked.connect(self.create_message_for_chat)

        # Кнопка поиска сообщений по имени пользователя
        self.ui.btn_search.clicked.connect(self.search_mess_on_name)

        # Дополнительные требующиеся атрибуты
        self.contacts_model = None
        self.history_model = None
        self.messages = QMessageBox()
        self.current_chat = None
        self.current_chat_key = None
        self.encryptor = None
        self.ui.list_messages.setHorizontalScrollBarPolicy(
            Qt.ScrollBarAlwaysOff)
        self.ui.list_messages.setWordWrap(True)

        # Даблклик по листу контактов отправляется в обработчик
        self.ui.list_contacts.doubleClicked.connect(self.select_active_user)

        # Добавляем туллбар с форматированием текста и смайликами
        our_bold = QAction(QIcon('img/b.jpg'), 'Bold', self)
        our_bold.triggered.connect(self.actionBold)

        our_italic = QAction(QIcon('img/i.jpg'), 'Italic', self)
        our_italic.triggered.connect(self.actionItalic)

        our_underlined = QAction(QIcon('img/u.jpg'), 'Underlined', self)
        our_underlined.triggered.connect(self.actionUnderlined)

        smile = QAction(QIcon('img/ab.gif'), 'Smile', self)
        smile.triggered.connect(self.actionSmile)

        melancholy = QAction(QIcon('img/ac.gif'), 'Melancholy', self)
        melancholy.triggered.connect(self.actionMelancholy)

        surprise = QAction(QIcon('img/ai.gif'), 'Surprise', self)
        surprise.triggered.connect(self.actionSurprise)

        # avatar = QAction(QIcon('avatar.jpg'), 'Avatar', self)
        # avatar.triggered.connect(self.actionSelectAvat)

        toolBar = self.addToolBar('Formatting')
        toolBar.addAction(our_bold)
        toolBar.addAction(our_italic)
        toolBar.addAction(our_underlined)
        toolBar.addAction(smile)
        toolBar.addAction(melancholy)
        toolBar.addAction(surprise)
        # toolBar.addAction(avatar)

        self.clients_list_update()
        self.set_disabled_input()
        self.show()

    def actionBold(self):
        myFont = QFont()
        myFont.setBold(True)
        self.ui.text_message.setFont(myFont)

    def actionItalic(self):
        myFont = QFont()
        myFont.setItalic(True)
        self.ui.text_message.setFont(myFont)

    def actionUnderlined(self):
        myFont = QFont()
        myFont.setUnderline(True)
        self.ui.text_message.setFont(myFont)

    def actionSmile(self):
        url = 'img/ab.gif'
        self.ui.text_message.setHtml('<img src="%s" />' % url)

    def actionMelancholy(self):
        url = 'img/ac.gif'
        self.ui.text_message.setHtml('<img src="%s" />' % url)

    def actionSurprise(self):
        url = 'img/ai.gif'
        self.ui.text_message.setHtml('<img src="%s" />' % url)

    # def actionSelectAvat(self):
    #     pass

    # Деактивировать поля ввода

    def set_disabled_input(self):
        # Надпись  - получатель.
        self.ui.label_new_message.setText(
            'Для выбора получателя дважды кликните на нем в окне контактов.')
        self.ui.text_message.clear()
        if self.history_model:
            self.history_model.clear()

        # Поле ввода и кнопка отправки неактивны до выбора получателя.
        self.ui.btn_clear.setDisabled(True)
        self.ui.btn_send.setDisabled(True)
        self.ui.text_message.setDisabled(True)

        self.encryptor = None
        self.current_chat = None
        self.current_chat_key = None

    # Заполняем историю сообщений.
    def history_list_update(self):
        # Получаем историю сортированную по дате
        list = sorted(
            self.database.get_history(
                self.current_chat),
            key=lambda item: item[3])
        # Если модель не создана, создадим.
        if not self.history_model:
            self.history_model = QStandardItemModel()
            self.ui.list_messages.setModel(self.history_model)
        # Очистим от старых записей
        self.history_model.clear()
        # Берём не более 20 последних записей.
        length = len(list)
        start_index = 0
        if length > 20:
            start_index = length - 20
        # Заполнение модели записями, так-же стоит разделить входящие и исходящие выравниванием и разным фоном.
        # Записи в обратном порядке, поэтому выбираем их с конца и не более 20
        for i in range(start_index, length):
            item = list[i]
            if item[1] == 'in':
                mess = QStandardItem(
                    f'Входящее от {item[3].replace(microsecond=0)}:\n {item[2]}')
                mess.setEditable(False)
                mess.setBackground(QBrush(QColor(255, 213, 213)))
                mess.setTextAlignment(Qt.AlignLeft)
                self.history_model.appendRow(mess)
            else:
                mess = QStandardItem(
                    f'Исходящее от {item[3].replace(microsecond=0)}:\n {item[2]}')
                mess.setEditable(False)
                mess.setTextAlignment(Qt.AlignRight)
                mess.setBackground(QBrush(QColor(204, 255, 204)))
                self.history_model.appendRow(mess)
        self.ui.list_messages.scrollToBottom()

    # Функция обработчик даблклика по контакту
    def select_active_user(self):
        # Выбранный пользователем (даблклик) находится в выделеном элементе в
        # QListView
        self.current_chat = self.ui.list_contacts.currentIndex().data()
        # вызываем основную функцию
        self.set_active_user()

    # Функция устанавливающяя активного собеседника
    def set_active_user(self):
        # Запрашиваем публичный ключ пользователя и создаём объект шифрования
        try:
            self.current_chat_key = self.transport.key_request(
                self.current_chat)
            client_logger.debug(
                f'Загружен открытый ключ для {self.current_chat}')
            if self.current_chat_key:
                self.encryptor = PKCS1_OAEP.new(
                    RSA.import_key(self.current_chat_key))
        except (OSError, json.JSONDecodeError):
            self.current_chat_key = None
            self.encryptor = None
            client_logger.debug(
                f'Не удалось получить ключ для {self.current_chat}')

        # Если ключа нет то ошибка, что не удалось начать чат с пользователем
        if not self.current_chat_key:
            self.messages.warning(
                self, 'Ошибка', 'Для выбранного пользователя нет ключа шифрования.')
            return

        # Ставим надпись и активируем кнопки
        self.ui.label_new_message.setText(
            f'Введите сообщенние для {self.current_chat}:')
        self.ui.btn_clear.setDisabled(False)
        self.ui.btn_send.setDisabled(False)
        self.ui.text_message.setDisabled(False)

        # Заполняем окно историю сообщений по требуемому пользователю.
        self.history_list_update()

    # Функция обновляющяя контакт лист
    def clients_list_update(self):
        contacts_list = self.database.get_contacts()
        self.contacts_model = QStandardItemModel()
        for i in sorted(contacts_list):
            item = QStandardItem(i)
            item.setEditable(False)
            self.contacts_model.appendRow(item)
        self.ui.list_contacts.setModel(self.contacts_model)

    # Функция добавления контакта
    def add_contact_window(self):
        global select_dialog
        select_dialog = AddContactDialog(self.transport, self.database)
        select_dialog.btn_ok.clicked.connect(
            lambda: self.add_contact_action(select_dialog))
        select_dialog.show()

    # Функция - обработчик добавления, сообщает серверу, обновляет таблицу и
    # список контактов
    def add_contact_action(self, item):
        new_contact = item.selector.currentText()
        self.add_contact(new_contact)
        item.close()

    # Функция добавляющяя контакт в базы
    def add_contact(self, new_contact):
        try:
            self.transport.add_contact(new_contact)
        except ServerError as err:
            self.messages.critical(self, 'Ошибка сервера', err.text)
        except OSError as err:
            if err.errno:
                self.messages.critical(
                    self, 'Ошибка', 'Потеряно соединение с сервером!')
                self.close()
            self.messages.critical(self, 'Ошибка', 'Таймаут соединения!')
        else:
            self.database.add_contact(new_contact)
            new_contact = QStandardItem(new_contact)
            new_contact.setEditable(False)
            self.contacts_model.appendRow(new_contact)
            client_logger.info(f'Успешно добавлен контакт {new_contact}')
            self.messages.information(
                self, 'Успех', 'Контакт успешно добавлен.')

    # Функция удаления контакта
    def delete_contact_window(self):
        global remove_dialog
        remove_dialog = DelContactDialog(self.database)
        remove_dialog.btn_ok.clicked.connect(
            lambda: self.delete_contact(remove_dialog))
        remove_dialog.show()

    # Функция обработчик удаления контакта, сообщает на сервер, обновляет
    # таблицу контактов
    def delete_contact(self, item):
        selected = item.selector.currentText()
        try:
            self.transport.remove_contact(selected)
        except ServerError as err:
            self.messages.critical(self, 'Ошибка сервера', err.text)
        except OSError as err:
            if err.errno:
                self.messages.critical(
                    self, 'Ошибка', 'Потеряно соединение с сервером!')
                self.close()
            self.messages.critical(self, 'Ошибка', 'Таймаут соединения!')
        else:
            self.database.del_contact(selected)
            self.clients_list_update()
            client_logger.info(f'Успешно удалён контакт {selected}')
            self.messages.information(self, 'Успех', 'Контакт успешно удалён.')
            item.close()
            # Если удалён активный пользователь, то деактивируем поля ввода.
            if selected == self.current_chat:
                self.current_chat = None
                self.set_disabled_input()

    # Функция отправки собщения пользователю.
    def send_message(self):
        # Текст в поле, проверяем что поле не пустое затем забирается сообщение
        # и поле очищается
        message_text = self.ui.text_message.toPlainText()
        self.ui.text_message.clear()
        if not message_text:
            return
        # Шифруем сообщение ключом получателя и упаковываем в base64.
        message_text_encrypted = self.encryptor.encrypt(
            message_text.encode('utf8'))
        message_text_encrypted_base64 = base64.b64encode(
            message_text_encrypted)
        try:
            self.transport.send_message(
                self.current_chat,
                message_text_encrypted_base64.decode('ascii'))
            pass
        except ServerError as err:
            self.messages.critical(self, 'Ошибка', err.text)
        except OSError as err:
            if err.errno:
                self.messages.critical(
                    self, 'Ошибка', 'Потеряно соединение с сервером!')
                self.close()
            self.messages.critical(self, 'Ошибка', 'Таймаут соединения!')
        except (ConnectionResetError, ConnectionAbortedError):
            self.messages.critical(
                self, 'Ошибка', 'Потеряно соединение с сервером!')
            self.close()
        else:
            self.database.save_message(self.current_chat, 'out', message_text)
            client_logger.debug(
                f'Отправлено сообщение для {self.current_chat}: {message_text}')
            self.history_list_update()

    # Слот приёма нового сообщений
    @pyqtSlot(dict)
    def message(self, message):
        # Получаем строку байтов
        encrypted_message = base64.b64decode(message[MESSAGE_TEXT])
        # Декодируем строку, при ошибке выдаём сообщение и завершаем функцию
        try:
            decrypted_message = self.decrypter.decrypt(encrypted_message)
        except (ValueError, TypeError):
            self.messages.warning(
                self, 'Ошибка', 'Не удалось декодировать сообщение.')
            return
        # Сохраняем сообщение в базу и обновляем историю сообщений или
        # открываем новый чат.
        self.database.save_message(
            self.current_chat,
            'in',
            decrypted_message.decode('utf8'))

        sender = message[SENDER]
        if sender == self.current_chat:
            self.history_list_update()
        else:
            # Проверим есть ли такой пользователь у нас в контактах:
            if self.database.check_contact(sender):
                # Если есть, спрашиваем и желании открыть с ним чат и открываем
                # при желании
                if self.messages.question(
                    self,
                    'Новое сообщение',
                    f'Получено новое сообщение от {sender}, открыть чат с ним?',
                    QMessageBox.Yes,
                        QMessageBox.No) == QMessageBox.Yes:
                    self.current_chat = sender
                    self.set_active_user()
            else:
                print('NO')
                # Раз нету,спрашиваем хотим ли добавить юзера в контакты.
                if self.messages.question(
                    self,
                    'Новое сообщение',
                    f'Получено новое сообщение от {sender}.\n Данного пользователя нет в вашем контакт-листе.\n Добавить в контакты и открыть чат с ним?',
                    QMessageBox.Yes,
                        QMessageBox.No) == QMessageBox.Yes:
                    self.add_contact(sender)
                    self.current_chat = sender
                    # Нужно заново сохранить сообщение, иначе оно будет потеряно,
                    # т.к. на момент предыдущего вызова контакта не было.
                    self.database.save_message(
                        self.current_chat, 'in', decrypted_message.decode('utf8'))
                    self.set_active_user()

    # Слот потери соединения
    # Выдаёт сообщение о ошибке и завершает работу приложения
    @pyqtSlot()
    def connection_lost(self):
        self.messages.warning(
            self,
            'Сбой соединения',
            'Потеряно соединение с сервером. ')
        self.close()

    # Слот сообщения 205 - требование сервером обновить справочники доступных пользователей и контактов
    # Может получиться так, что удалён текущий собеседник, надо проверить это и закрыть чат с предупреждением.
    # иначе просто обновить список контактов, без выдачи предупреждения
    # пользователю.
    @pyqtSlot()
    def sig_205(self):
        if self.current_chat and not self.database.check_user(
                self.current_chat):
            self.messages.warning(
                self,
                'Сочувствую',
                'К сожалению собеседник был удалён с сервера.')
            self.set_disabled_input()
            self.current_chat = None
        self.clients_list_update()

    def make_connection(self, trans_obj):
        trans_obj.new_message.connect(self.message)
        trans_obj.connection_lost.connect(self.connection_lost)
        trans_obj.message_205.connect(self.sig_205)

        # Функция добавления аватара
    def add_avat_user(self):
        fname = QFileDialog.getOpenFileName(
            self, 'Open file', '/home/picforavat')[0]
        self.fname = fname
        file = Image.open(self.fname)
        width = 60
        height = 50
        # Изменяем размер изображения
        our_pict = file.resize((width, height), Image.BICUBIC)
        our_pict.save("avatar.jpg")

        file = open("avatar.jpg", "rb")
        our_pict = file.read()
        file.close()
        # Добавляем в БД
        self.database.add_avatar(our_pict)

        # Обрезаем изображение
        file = Image.open("avatar.jpg")
        our_pict = file.crop((0, 0, 50, 40))
        our_pict.save("avatar.jpg")

        # Меняем аватар в окне клиента на новый
        pixmap = QPixmap('avatar.jpg')
        self.ui.avatar.setPixmap(pixmap)
        self.ui.avatar.resize(300, 300)
        self.ui.avatar.setGeometry(QRect(300, 425, 45, 35))

        file = open("avatar.jpg", "rb")
        our_pict = file.read()
        file.close()
        # Добавляем в БД
        self.database.add_avatar(our_pict)

    def sel_avat_user(self):
        print('ok')

    def chat_history_update(self):
        if self.history_model:
            self.history_model.clear()

        if not self.history_model:
            self.history_model = QStandardItemModel()
            self.ui.list_messages.setModel(self.history_model)
        list_messages = self.transport.get_chat_message()

        # Берём не более 20 последних записей.
        length = len(list_messages)
        start_index = 0
        if length > 20:
            start_index = length - 20
        for i in range(start_index, length):
            item = list_messages[i]
            mess = QStandardItem(
                f'Сообщение от {item[0]}:\n               {item[1]}')
            mess.setEditable(False)
            #mess.setBackground(QBrush(QColor(255, 213, 213)))
            mess.setTextAlignment(Qt.AlignLeft)
            self.history_model.appendRow(mess)
        self.ui.list_messages.scrollToBottom()

    # Функция отправляет на сервер сообщение, которое направлено в чат
    def create_message_for_chat(self):
        self.chat_history_update()
        # Текст в поле, проверяем что поле не пустое затем забирается сообщение
        # и поле очищается
        message_text = self.ui.text_message.toPlainText()
        self.ui.text_message.clear()
        self.ui.label_new_message.setText(
            f'Введите сообщенние в чат')
        self.ui.text_message.setDisabled(False)
        if not message_text:
            return
        try:
            self.transport.send_message_to_chat(message_text)
            # message_text_encrypted_base64.decode('ascii'))
            pass
        except ServerError as err:
            self.messages.critical(self, 'Ошибка', err.text)
        except OSError as err:
            if err.errno:
                self.messages.critical(
                    self, 'Ошибка', 'Потеряно соединение с сервером!')
                self.close()
            self.messages.critical(self, 'Ошибка', 'Таймаут соединения!')
        except (ConnectionResetError, ConnectionAbortedError):
            self.messages.critical(
                self, 'Ошибка', 'Потеряно соединение с сервером!')
            self.close()
        else:
            self.chat_history_update()

        # Функция поиска истории сообщений по имени пользователя
    def search_mess_on_name(self):
        usv = self.ui.text_message.toPlainText()
        self.ui.text_message.clear()
        self.ui.text_message.setDisabled(False)
        if not usv:
            return
        list_contacts = self.database.get_contacts()
        if usv in list_contacts:
            if self.history_model:
                self.history_model.clear()
            if not self.history_model:
                self.history_model = QStandardItemModel()
                self.ui.list_messages.setModel(self.history_model)
            list_messages = self.database.get_history(usv)
            length = len(list_messages)
            start_index = 0
            if length > 20:
                start_index = length - 20
            for i in range(start_index, length):
                item = list_messages[i]
                if item[1] == 'out':
                    mess = QStandardItem(
                        f'Я:\n    Сообщение от {item[3].replace(microsecond=0)}:\n               {item[2]}')
                    mess.setEditable(False)
                    # mess.setBackground(QBrush(QColor(255, 213, 213)))
                    mess.setTextAlignment(Qt.AlignLeft)
                    self.history_model.appendRow(mess)
                elif item[1] == 'in':
                    mess = QStandardItem(
                        f'{usv}:\n    Сообщение от {item[3].replace(microsecond=0)}:\n               {item[2]}')
                    mess.setEditable(False)
                    # mess.setBackground(QBrush(QColor(255, 213, 213)))
                    mess.setTextAlignment(Qt.AlignLeft)
                    self.history_model.appendRow(mess)

            self.ui.list_messages.scrollToBottom()
        else:
            if self.history_model:
                self.history_model.clear()
            mess = QStandardItem(
                'Пользователя с таким именем у вас в контактах нет')
            mess.setEditable(False)
            mess.setBackground(QBrush(QColor(255, 213, 213)))
            mess.setTextAlignment(Qt.AlignLeft)
            self.history_model.appendRow(mess)


