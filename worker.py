import json
import os
import re
import subprocess

import grequests
from PyQt5 import QtCore

from dispatcher import Dispatcher


class EmittingStream(QtCore.QObject):
    text_written = QtCore.pyqtSignal(str)

    def write(self, text):
        self.text_written.emit(str(text))

    def flush(self):
        pass


class Worker(QtCore.QThread):
    def __init__(self, parent=None):
        super(Worker, self).__init__(parent)
        self.exiting = False
        self.dispatcher = Dispatcher.instance()
        self.max_processes = 10

    def run_check(self, hjson_path):
        self.hjson_path = hjson_path
        self.start()

    def run(self):

        total = 0
        totals = {}
        bad_results = 0

        with open(self.hjson_path) as f:
            sites = json.load(f)

        rs = (grequests.head(s.get('url'))
              for s in sites.get('base_urls'))
        for r in grequests.imap(rs, size=20):
            total += 1
            if totals.get(r.status_code):
                totals[r.status_code] += 1
            else:
                totals[r.status_code] = 1
            if r.status_code >= 400:
                bad_results += 1
            print('========================================================')
            print(r.url)
            print("elapsed time: %.2f" % r.elapsed.total_seconds())
            print("status code: %d" % r.status_code)

        print('========================================================')
        print('Summary')
        print('========================================================')
        print('Total requests: %d' % total)
        print('Bad responses: %d' % bad_results)
        for sc in totals:
            print('Status Code %d: %d' % (sc, totals[sc]))

        self.dispatcher.command_complete.emit(0)
