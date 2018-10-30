#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Feed Checker
MIT License
@author abidibo <abidibo@gmail.com>
Company Otto srl <https://www.otto.to.it>
"""

import json
import os
import sys

from PyQt5 import QtCore
from PyQt5.QtGui import QIcon, QMovie, QTextCursor
from PyQt5.QtWidgets import (QAction, QApplication, QDesktopWidget,
                             QFileDialog, QInputDialog, QLabel, QMainWindow,
                             QMenu, QMessageBox, QPushButton, QSystemTrayIcon,
                             QTextEdit, QVBoxLayout, QWidget, qApp)

from dialog_info import InfoDialog
from dispatcher import Dispatcher
from utils import bundle_dir, icon, style
from worker import EmittingStream, Worker


class MainWindow(QMainWindow):
    """ Main Application Window"""

    def __init__(self):
        super(MainWindow, self).__init__()
        # event dispatcher
        self.dispatcher = Dispatcher.instance()
        # translations
        self.translate = QtCore.QCoreApplication.translate
        self.interval = 'daily'
        self.hjson_value = None
        # thread which runs rsnapshot
        self.worker = Worker()
        # is rsnapshot still running?
        self.busy = False

        # connect to events
        self.dispatcher.error.connect(self.command_error)
        self.dispatcher.command_complete.connect(self.command_complete)

        # Install the custom output stream
        sys.stdout = EmittingStream(text_written=self.log_command)

        # init ui
        self.init_ui()

    def closeEvent(self, event):
        """ Do not close the app if rsnapshot is still running """
        if not self.busy:
            event.accept()
        else:
            event.ignore()
            QMessageBox.warning(
                self, 'Feed Checker',
                self.translate("MainWindow", "You badass, I'm still running!"),
                QMessageBox.Ok)

    def init_ui(self):
        # styles
        ssh_file = style()
        with open(ssh_file, "r") as fh:
            self.setStyleSheet(fh.read())
        # dimensions and positioning
        self.resize(800, 500)
        self.center()
        # window props
        self.setWindowTitle('Feed Checker')
        self.setWindowIcon(QIcon(icon('icon.png')))
        # system tray icon
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(QIcon(icon('icon.png')))
        quit_action = QAction(self.translate('MainWindow', 'Quit'), self)
        quit_action.triggered.connect(qApp.quit)
        tray_menu = QMenu()
        tray_menu.addAction(quit_action)
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()
        # info
        infoAct = QAction(QIcon(icon('info-icon.png')), 'Exit', self)
        infoAct.triggered.connect(self.open_info_dialog)
        # toolbar
        self.toolbar = self.addToolBar('Toolbar')
        self.toolbar.addAction(infoAct)
        # layout
        self.wid = QWidget(self)
        self.setCentralWidget(self.wid)
        self.main_layout = QVBoxLayout()
        self.main_layout.setSpacing(20)
        self.init_ui_body()
        self.wid.setLayout(self.main_layout)

        # show
        self.show()

    def center(self):
        """ Place the window in the center of the screen """
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def init_ui_body(self):
        """ The ui body """
        # text info (displays rsnapshot output)
        self.text_info = QTextEdit()
        self.text_info.setReadOnly(True)
        self.text_info.setText('choose an hjson file, gringo!')
        # start button
        self.start_button = QLabel('<img src="%s" />' % icon('start-icon.png'))
        self.start_button.mousePressEvent = self.start
        self.start_button.setFixedSize(128, 136)
        # select file
        self.hjson_button = QPushButton(
            self.translate('MainWindow', 'choose hjson file'))
        self.hjson_button.clicked.connect(self.choose_hjson)
        self.hjson_button.setProperty('buttonClass', 'hjsonButton')
        self.hjson_button.setFixedSize(200, 40)
        self.hjson_value_label = QLabel('')
        self.hjson_value_label.setProperty('labelClass', 'hjsonValue')
        # loading icon
        self.loading_movie = QMovie(icon('loader.gif'))
        self.loading = QLabel()
        self.loading.setAlignment(QtCore.Qt.AlignCenter)
        self.loading.setMovie(self.loading_movie)
        self.loading.setHidden(True)

        # add all the stuff to the layout
        self.main_layout.addWidget(self.start_button)
        self.main_layout.addWidget(self.hjson_button)
        self.main_layout.addWidget(self.hjson_value_label)
        self.main_layout.addWidget(self.loading)
        self.main_layout.addWidget(self.text_info)
        self.main_layout.setAlignment(self.start_button, QtCore.Qt.AlignCenter)
        self.main_layout.setAlignment(self.hjson_button, QtCore.Qt.AlignCenter)
        self.main_layout.setAlignment(self.hjson_value_label,
                                      QtCore.Qt.AlignCenter)

    def open_info_dialog(self):
        """ opens the info window """
        info_dialog = InfoDialog()
        info_dialog.exec_()

    def choose_hjson(self):
        fname = QFileDialog.getOpenFileName(
            self, self.translate('MainWindow', 'Open file'),
            os.path.expanduser('~'))

        if fname[0]:
            self.hjson_value = fname[0]
            self.hjson_value_label.setText(self.hjson_value)
            self.text_info.setText(
                'what are you waiting for? Push the button asshole!')

    def start(self, event):
        """ Starts the check if not yet busy """
        if not self.hjson_value:
            QMessageBox.information(
                self, 'Feed Checker',
                self.translate(
                    'MainWindow',
                    'Fuck, have you understood you must select an hjson file?'
                ), QMessageBox.Ok)
        elif not self.busy:
            self.set_busy(True)
            self.text_info.setText(
                'starting checking feeds, keep calm and drink water...\n')
            self.worker.run_check(self.hjson_value)

    def log_command(self, text):
        """ Logs sys.stdout in the text field """
        cursor = self.text_info.textCursor()
        cursor.movePosition(QTextCursor.End)
        cursor.insertText(text)
        self.text_info.setTextCursor(cursor)
        self.text_info.ensureCursorVisible()

    def command_error(self, message):
        """ Used to filter rsnapshot errors and perform actions or display
            info in some cases """
        if message == 'error-cannot-find-dest':
            reply = QMessageBox.warning(
                self, 'Feed Checker',
                self.translate('MainWindow', '''An error occurred.'''),
                QMessageBox.Ok)
            if reply == QMessageBox.Ok:
                self.text_info.setText('ready...')

    def command_complete(self, returncode):
        """ rsnapshot command complete """
        self.set_busy(False)
        # success with or without warnings
        if returncode == 0 or returncode == 2:
            # save last sync
            # show success dialog
            text, ok = QInputDialog.getText(
                self, self.translate('MainWindow', 'Ok buddy'),
                self.translate(
                    'MainWindow',
                    'If you want to save the corrected hjson list enter the file path and press enter, otherwise 🖕'
                ))
            if ok:
                corrected_hjson = self.worker.get_corrected_hjson()
                with open(text, 'w') as outfile:
                    json.dump(
                        corrected_hjson,
                        outfile,
                        sort_keys=True,
                        indent=4,
                        ensure_ascii=False)

    def set_busy(self, busy):
        """ Is the application busy? """
        if busy:
            self.hjson_button.setDisabled(True)
            self.loading.setHidden(False)
            self.loading_movie.start()
        else:
            self.hjson_button.setDisabled(False)
            self.loading.setHidden(True)
            self.loading_movie.stop()
        self.busy = busy


def setup():
    """ Init folder and files if necessary """
    pass


if __name__ == '__main__':
    app = QApplication(sys.argv)
    translator = QtCore.QTranslator(app)
    lc_path = os.path.join(
        bundle_dir, 'i18n',
        'feedchecker_%s.qm' % QtCore.QLocale.system().name()[:2])
    translator.load(lc_path)
    app.installTranslator(translator)
    main_window = MainWindow()
    sys.exit(app.exec_())
