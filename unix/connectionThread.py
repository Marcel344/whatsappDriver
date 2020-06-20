from PyQt5.QtCore import QThread
from PyQt5 import uic, Qt, QtWidgets, QtCore
import time
try:
    import httplib
except:
    import http.client as httplib


class connectionThread (QThread):

    connectionInterruptSignal = QtCore.pyqtSignal(bool, name="boolSignal")

    def __init__(self):
        super(connectionThread, self).__init__()


    def run(self):
        while True :
            conn = httplib.HTTPConnection("www.google.com", timeout=2)
            try:
                conn.request("HEAD", "/")
                self.connectionInterruptSignal.emit(True)
                conn.close()
            except:
                conn.close()
                self.connectionInterruptSignal.emit(False)
            time.sleep(2) # Check for connection every 2 seconds