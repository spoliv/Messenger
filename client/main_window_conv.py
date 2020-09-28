# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'client.ui'
#
# Created by: PyQt5 UI code generator 5.11.3
#
# WARNING! All changes made in this file will be lost!
import sys
from PyQt5 import QtCore, QtGui, QtWidgets

from PyQt5.QtWidgets import QAction, QTextEdit, QLabel
from PyQt5.QtGui import QIcon, QFont


class Ui_MainClientWindow(object):
    def setupUi(self, MainClientWindow):
        MainClientWindow.setObjectName("MainClientWindow")
        MainClientWindow.resize(756, 534)
        MainClientWindow.setMinimumSize(QtCore.QSize(756, 534))
        self.centralwidget = QtWidgets.QWidget(MainClientWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.label_contacts = QtWidgets.QLabel(self.centralwidget)
        self.label_contacts.setGeometry(QtCore.QRect(10, 0, 101, 16))
        self.label_contacts.setObjectName("label_contacts")
        self.btn_add_contact = QtWidgets.QPushButton(self.centralwidget)
        self.btn_add_contact.setGeometry(QtCore.QRect(10, 400, 121, 31))
        self.btn_add_contact.setObjectName("btn_add_contact")
        self.btn_remove_contact = QtWidgets.QPushButton(self.centralwidget)
        self.btn_remove_contact.setGeometry(QtCore.QRect(140, 400, 121, 31))
        self.btn_remove_contact.setObjectName("btn_remove_contact")
        self.label_history = QtWidgets.QLabel(self.centralwidget)
        self.label_history.setGeometry(QtCore.QRect(300, 0, 391, 21))
        self.label_history.setObjectName("label_history")

        self.text_message = QtWidgets.QTextEdit(self.centralwidget)
        self.text_message.setGeometry(QtCore.QRect(300, 360, 441, 60))
        self.text_message.setObjectName("text_message")

        self.label_new_message = QtWidgets.QLabel(self.centralwidget)
        self.label_new_message.setGeometry(
            QtCore.QRect(300, 330, 450, 16))  # Правка тут
        self.label_new_message.setObjectName("label_new_message")
        self.list_contacts = QtWidgets.QListView(self.centralwidget)
        self.list_contacts.setGeometry(QtCore.QRect(10, 20, 251, 370))
        self.list_contacts.setObjectName("list_contacts")
        self.list_messages = QtWidgets.QListView(self.centralwidget)
        self.list_messages.setGeometry(QtCore.QRect(300, 20, 441, 301))
        self.list_messages.setObjectName("list_messages")
        self.btn_send = QtWidgets.QPushButton(self.centralwidget)
        self.btn_send.setGeometry(QtCore.QRect(610, 427, 131, 31))
        self.btn_send.setObjectName("btn_send")
        self.btn_clear = QtWidgets.QPushButton(self.centralwidget)
        self.btn_clear.setGeometry(QtCore.QRect(460, 427, 131, 31))
        self.btn_clear.setObjectName("btn_clear")
        self.btn_chat = QtWidgets.QPushButton(self.centralwidget)
        self.btn_chat.setGeometry(QtCore.QRect(360, 427, 80, 31))
        #self.btn_chat.setGeometry(QtCore.QRect(10, 435, 251, 25))
        self.btn_chat.setObjectName("btn_chat")
        self.btn_search = QtWidgets.QPushButton(self.centralwidget)
        self.btn_search.setGeometry(QtCore.QRect(10, 435, 251, 25))
        self.btn_search.setObjectName("btn_search")
        MainClientWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(MainClientWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 756, 21))
        self.menubar.setObjectName("menubar")
        self.menu = QtWidgets.QMenu(self.menubar)
        self.menu.setObjectName("menu")
        self.menu_2 = QtWidgets.QMenu(self.menubar)
        self.menu_2.setObjectName("menu_2")

        self.menu_3 = QtWidgets.QMenu(self.menubar)
        self.menu_3.setObjectName("menu_3")

        MainClientWindow.setMenuBar(self.menubar)
        self.statusBar = QtWidgets.QStatusBar(MainClientWindow)
        self.statusBar.setObjectName("statusBar")
        MainClientWindow.setStatusBar(self.statusBar)
        self.menu_exit = QtWidgets.QAction(MainClientWindow)
        self.menu_exit.setObjectName("menu_exit")
        self.menu_add_contact = QtWidgets.QAction(MainClientWindow)
        self.menu_add_contact.setObjectName("menu_add_contact")
        self.menu_del_contact = QtWidgets.QAction(MainClientWindow)
        self.menu_del_contact.setObjectName("menu_del_contact")

        self.menu_add_avatar = QtWidgets.QAction(MainClientWindow)
        self.menu_add_avatar.setObjectName("menu_add_avatar")

        self.menu_select_avatar = QtWidgets.QAction(MainClientWindow)
        self.menu_select_avatar.setObjectName("menu_select_avatar")

        self.menu.addAction(self.menu_exit)
        self.menu_2.addAction(self.menu_add_contact)
        self.menu_2.addAction(self.menu_del_contact)
        self.menu_2.addSeparator()

        self.menu_3.addAction(self.menu_add_avatar)
        self.menu_3.addAction(self.menu_select_avatar)


        self.menubar.addAction(self.menu.menuAction())
        self.menubar.addAction(self.menu_2.menuAction())

        self.menubar.addAction(self.menu_3.menuAction())

        self.retranslateUi(MainClientWindow)
        self.btn_clear.clicked.connect(self.text_message.clear)
        QtCore.QMetaObject.connectSlotsByName(MainClientWindow)


        # self.btn_avatar = QtWidgets.QPushButton(self.centralwidget)
        # self.btn_avatar.setIcon(QIcon('avatar.jpg'))
        # self.btn_avatar.setToolTip("Выбрать аватар")
        # self.btn_avatar.setIconSize(QtCore.QSize(70, 60))
        # self.btn_avatar.setGeometry(QtCore.QRect(300, 425, 45, 35))
        # self.btn_avatar.setObjectName("btn_avatar")

        # Отображение аватара в окне клиента
        self.avatar = QLabel(self.centralwidget)
        pixmap = QtGui.QPixmap('avatar.jpg')
        self.avatar.setPixmap(pixmap)
        self.avatar.setGeometry(QtCore.QRect(300, 425, 45, 35))

    def retranslateUi(self, MainClientWindow):
        _translate = QtCore.QCoreApplication.translate
        MainClientWindow.setWindowTitle(
            _translate(
                "MainClientWindow",
                "Чат Программа alpha release"))
        self.label_contacts.setText(
            _translate(
                "MainClientWindow",
                "Список контактов:"))
        self.btn_add_contact.setText(
            _translate(
                "MainClientWindow",
                "Добавить контакт"))
        self.btn_remove_contact.setText(
            _translate(
                "MainClientWindow",
                "Удалить контакт"))
        self.label_history.setText(
            _translate(
                "MainClientWindow",
                "История сообщений:"))
        self.label_new_message.setText(
            _translate(
                "MainClientWindow",
                "Введите новое сообщение:"))
        self.btn_send.setText(
            _translate(
                "MainClientWindow",
                "Отправить сообщение"))

        self.btn_chat.setText(
            _translate(
                "MainClientWindow",
                "Чат"))
        self.btn_search.setText(
            _translate(
                "MainClientWindow",
                "Найти историю переписки"))

        self.btn_clear.setText(_translate("MainClientWindow", "Очистить поле"))
        self.menu.setTitle(_translate("MainClientWindow", "Файл"))
        self.menu_2.setTitle(_translate("MainClientWindow", "Контакты"))

        self.menu_3.setTitle(_translate("MainClientWindow", "Аватар"))

        self.menu_exit.setText(_translate("MainClientWindow", "Выход"))
        self.menu_add_contact.setText(
            _translate(
                "MainClientWindow",
                "Добавить контакт"))
        self.menu_del_contact.setText(
            _translate(
                "MainClientWindow",
                "Удалить контакт"))

        self.menu_add_avatar.setText(
            _translate(
                "MainClientWindow",
                "Добавить аватар"))

        self.menu_select_avatar.setText(
            _translate(
                "MainClientWindow",
                "Выбрать аватар из базы"))
