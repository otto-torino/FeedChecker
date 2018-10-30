import json

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
        self.corrected_hjson = []

    def run_check(self, hjson_path):
        self.hjson_path = hjson_path
        self.start()

    def hook_factory(self, site):
        def response_hook(response, *request_args, **request_kwargs):
            print('========================================================')
            print(response.url)
            print("elapsed time: %.2f" % response.elapsed.total_seconds())
            print("status code: %d" % response.status_code)
            # keep only 200 <= codes < 300
            # redirects (3XX) causes this hook to be fired again, so are
            # not taken into account
            if (response.status_code < 300):
                self.corrected_hjson.append(site)

            return response  # or the modified response
        return response_hook

    def run(self):

        total = 0
        totals = {}
        bad_results = 0

        with open(self.hjson_path) as f:
            sites = json.load(f)

        rs = (grequests.head(s.get('url'), hooks={'response': [self.hook_factory(s)]})
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
        print('Summary')
        print('========================================================')
        print('Total requests: %d' % total)
        print('Bad responses: %d' % bad_results)
        for sc in totals:
            print('Status Code %d: %d' % (sc, totals[sc]))

        self.dispatcher.command_complete.emit(0)

    def get_corrected_hjson(self):
        return self.corrected_hjson
