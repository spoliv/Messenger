# from PyQt5.QtWidgets import QMainWindow, QToolBar, QMenuBar, QApplication, QPushButton
#
#
#
# class Main(QMainWindow):
#
#     def __init__(self, *args):
#         super().__init__(*args)
#         self.resize(300, 200)
#
#         menu = QMenuBar()
#         menu.addAction("File")
#         menu.addAction("Edit")
#         self.setMenuBar(menu)
#
#         tool = QToolBar()
#         tool.addWidget(QPushButton("Tool 1"))
#         tool.addWidget(QPushButton("Tool 2"))
#
#         self.addToolBar(tool)
#
#
# if __name__ == '__main__':
#     app = QApplication([])
#     w = Main()
#     w.show()
#     app.exec()
import pymongo




a = [(1, 2, 3), (8, 9, 10)]

for b in a:
    print(b)