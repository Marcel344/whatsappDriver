from PyQt5.QtCore import QThread
from PyQt5 import uic, Qt, QtWidgets, QtCore
import time
try:
    import httplib
except:
    import http.client as httplib


class connectionThread (QThread): # this is a Thread class responsible for checking internet connection

    connectionInterruptSignal = QtCore.pyqtSignal(bool, name="boolSignal") # this is a signal that will trigger the connected function in the main file

    def __init__(self):
        super(connectionThread, self).__init__()


    def run(self):
        while True : # run forever 
            conn = httplib.HTTPConnection("www.google.com", timeout=2) # establish a connection to google with a 2 seconds delay 
            try: # try to ping at google 
                conn.request("HEAD", "/")
                self.connectionInterruptSignal.emit(True) # send a true bool with the signal signifying that there is internet connection
                conn.close()
            except:
                conn.close()
                self.connectionInterruptSignal.emit(False) # send a false bool with the signal signifying that there is no internet connection
            time.sleep(2) # Check for connection every 2 seconds