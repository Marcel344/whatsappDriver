import unicodedata
from PyQt5.QtCore import QThread
from PyQt5 import uic, Qt, QtWidgets, QtCore
from PyQt5.QtWidgets import QApplication, QWidget, QInputDialog, QLineEdit, QFileDialog
from datetime import datetime
import sys
import json
import os
import csv
import forwader
import globalVariables as variables
import connectionThread
import shutil

class driver(Qt.QWidget):
    def __init__(self):
        super(driver, self).__init__()
        uic.loadUi('ui/main.ui', self)
        self.show()
        self.setWindowTitle("Whatsapp Forwader")
        self.imgPath = ""
        self.Message = ""
        self.Forwards = ""
        self.errorWindow = errorWindow()
        self.connErr = errorWindow()
        self.loadedJsonFile = None
        self.loadedCsvFile = None
        self.importedNamesCsvFile = None
        self.contactDict = {}
        self.importedContactDict = {}
        self.remainingContactDict = {}
        self.WhatsappForwader = forwader.WhatsappForwader()
        self.connectionThread = connectionThread.connectionThread()
        self.connectionThread.connectionInterruptSignal.connect(self.checkConnection)
        self.WhatsappForwader.strContactSignal.connect(self.appendName)
        self.WhatsappForwader.updatePBsignal.connect(self.updatePB)
        self.loadRecordBtn.clicked.connect(self.load_record)
        self.startBtn.clicked.connect(self.runThread)
        self.imageBtn.clicked.connect(self.chooseImg)
        self.importNamesBtn.clicked.connect(self.importNames)
        self.recordList.currentRowChanged.connect(self.enableLoadBtn)
        self.searchTxt.textChanged.connect(self.searchContacts)
        if (not os.path.isdir('records')):
            os.mkdir('records')
        self.setUpViews()
        self.WhatsappForwader.loadWebsite()
        self.connectionThread.start()

    def setUpViews(self):
        baseStyleSheet = "background-color: #cbcbcb; color : black;"
        btnStyleSheet = "background-color: white;  border: 1px solid #139e2d; border-radius: 10px; font-size: 12px;color: #139e2d;text-align: center;"
        widgetsStyleSheet = "background-color : white; border: 1px solid #139e2d"
        self.progressBar.setVisible(False)
        self.progressLbl.setVisible(False)
        self.loadRecordBtn.setEnabled(False)
        self.loadRecordBtn.setStyleSheet(
            "background-color: white;  border: 1px solid #ababab; border-radius: 10px; font-size: 12px;color: #ababab;text-align: center;")
        self.setStyleSheet(baseStyleSheet)
        self.imageLbl.setScaledContents(True)
        self.imageLbl.setStyleSheet(widgetsStyleSheet)
        self.recordList.setStyleSheet(widgetsStyleSheet)
        self.contactList.setStyleSheet(widgetsStyleSheet)
        self.searchTxt.setStyleSheet(widgetsStyleSheet)
        self.forwardsTxt.setStyleSheet(widgetsStyleSheet)
        self.messageTxt.setStyleSheet(widgetsStyleSheet)
        self.imageBtn.setStyleSheet(btnStyleSheet)
        self.importNamesBtn.setStyleSheet(btnStyleSheet)
        self.startBtn.setStyleSheet(btnStyleSheet)
        self.getFiles()
        self.show()

    def runThread(self):
        self.Message = self.messageTxt.toPlainText()
        self.Forwards = self.forwardsTxt.toPlainText()

        if self.Message == "" and self.imgPath == "":
            self.errorWindow.setErrorMsg(
                "Please fill in at least one of the two :\n-Image path\n-Text Message\nOtherwise the program will not run")
            self.errorWindow.show()

        elif self.Forwards == "":
            self.errorWindow.setErrorMsg(
                "Please set the number of forwards")
            self.errorWindow.show()

        elif (not self.is_number(self.Forwards)) or int(self.Forwards) < 1:
            self.errorWindow.setErrorMsg(
                "Please enter a valid number of forwards")
            self.errorWindow.show()

        elif (self.loadedCsvFile != None and self.loadedJsonFile != None and self.importedNamesCsvFile == None):
            self.WhatsappForwader.setForwards(self.Forwards)
            self.WhatsappForwader.setImagePath(self.imgPath)
            self.WhatsappForwader.setMessage(self.Message)
            self.WhatsappForwader.setFileName(self.loadedFileName)
            self.WhatsappForwader.setContactMode(variables.NEW_NAMES)
            self.MODE = variables.NEW_NAMES
            self.WhatsappForwader.setContactDict(self.contactDict)
            self.WhatsappForwader.setPreviewMode(
                self.previewCheckBox.isChecked())
            self.WhatsappForwader.setIsDelayMode(self.delayCheckBox.isChecked())
            self.WhatsappForwader.start()
            self.startBtn.setStyleSheet(
            "background-color: white;  border: 1px solid #ababab; border-radius: 10px; font-size: 12px;color: #ababab;text-align: center;")

        elif (self.loadedCsvFile == None and self.loadedJsonFile == None and self.importedNamesCsvFile != None):
            currentDate = datetime.today().strftime("%Y-%m-%d %H:%M:%S")
            os.makedirs(f'records/{currentDate}')
            jsonFile = open(f'records/{currentDate}/record.json', 'w+')
            if self.importedNamesCsvFile != None:
                open(f'records/{currentDate}/importedNames.csv', 'w+')
                shutil.copy2(self.importedNamesCsvFile.name, f'records/{currentDate}/importedNames.csv')
            jsonData = {
                "date": currentDate,
                "Forwards": self.Forwards,
                "Message": self.Message,
                "imagePath": self.imgPath,
                "importedNames": 'False' if self.importedNamesCsvFile == None else 'True'
            }
            json.dump(jsonData, jsonFile)
            self.progressBar.setVisible(True)
            self.progressLbl.setVisible(True)
            self.WhatsappForwader.setContactMode(variables.IMPORTED_NAMES)
            self.MODE = variables.IMPORTED_NAMES
            self.progressLbl.setText(f"0/{self.Forwards}")
            self.progressBar.setMaximum(int(self.Forwards))
            self.progressBar.setMinimum(0)
            self.progressBar.setValue(len(self.importedContactDict))
            self.WhatsappForwader.setForwards(self.Forwards)
            self.WhatsappForwader.setImagePath(self.imgPath)
            self.WhatsappForwader.setContactDict(self.importedContactDict)
            self.WhatsappForwader.setMessage(self.Message)
            self.WhatsappForwader.setFileName(currentDate)
            self.WhatsappForwader.loadCsvFile()
            self.WhatsappForwader.setPreviewMode(
                self.previewCheckBox.isChecked())
            self.WhatsappForwader.setIsDelayMode(self.delayCheckBox.isChecked())
            self.WhatsappForwader.start()
            self.startBtn.setStyleSheet(
            "background-color: white;  border: 1px solid #ababab; border-radius: 10px; font-size: 12px;color: #ababab;text-align: center;")

        elif (self.loadedCsvFile != None and self.loadedJsonFile != None and self.importedNamesCsvFile != None):
            self.WhatsappForwader.setForwards(self.Forwards)
            self.WhatsappForwader.setImagePath(self.imgPath)
            self.WhatsappForwader.setMessage(self.Message)
            self.WhatsappForwader.setFileName(self.loadedFileName)
            self.WhatsappForwader.setContactMode(variables.IMPORTED_NAMES)
            self.MODE = variables.IMPORTED_NAMES
            self.WhatsappForwader.setContactDict(self.remainingContactDict)
            self.WhatsappForwader.setPreviewMode(
                self.previewCheckBox.isChecked())
            self.WhatsappForwader.start()
            self.WhatsappForwader.setIsDelayMode(self.delayCheckBox.isChecked())
            self.startBtn.setStyleSheet(
            "background-color: white;  border: 1px solid #ababab; border-radius: 10px; font-size: 12px;color: #ababab;text-align: center;")

        else:
            currentDate = datetime.today().strftime("%Y-%m-%d %H:%M:%S")
            os.makedirs(f'records/{currentDate}')
            jsonFile = open(f'records/{currentDate}/record.json', 'w+')
            jsonData = {
                "date": currentDate,
                "Forwards": self.Forwards,
                "Message": self.Message,
                "imagePath": self.imgPath,
                "importedNames": 'False' if self.importedNamesCsvFile == None else 'True'
            }
            json.dump(jsonData, jsonFile)
            self.progressBar.setVisible(True)
            self.progressLbl.setVisible(True)
            self.WhatsappForwader.setContactMode(variables.NEW_NAMES)
            self.MODE = variables.NEW_NAMES
            self.progressLbl.setText(f"0/{self.Forwards}")
            self.progressBar.setMaximum(int(self.Forwards))
            self.progressBar.setMinimum(0)
            self.progressBar.setValue(len(self.contactDict))
            self.WhatsappForwader.setForwards(self.Forwards)
            self.WhatsappForwader.setImagePath(self.imgPath)
            self.WhatsappForwader.setMessage(self.Message)
            self.WhatsappForwader.setFileName(currentDate)
            self.WhatsappForwader.loadCsvFile()
            self.WhatsappForwader.setPreviewMode(
                self.previewCheckBox.isChecked())
            self.WhatsappForwader.setIsDelayMode(self.delayCheckBox.isChecked())
            self.WhatsappForwader.start()
            self.startBtn.setStyleSheet(
            "background-color: white;  border: 1px solid #ababab; border-radius: 10px; font-size: 12px;color: #ababab;text-align: center;")

    def load_record(self):
        if self.importedNamesCsvFile == None :
            if self.loadedCsvFile == None:
                if (self.recordList.currentItem()):
                    self.loadRecordBtn.setText("unload")
                    self.loadedFileName = str(self.recordList.currentItem().text())
                    self.loadedJsonFile = open(
                        f'records/{self.loadedFileName}/record.json', 'r')
                    self.loadedCsvFile = open(
                        f'records/{self.loadedFileName}/record.csv', 'r')
                    data = json.load(self.loadedJsonFile)
                    self.messageTxt.setText(data["Message"])
                    self.forwardsTxt.setText(data["Forwards"])
                    self.imgPath = data["imagePath"]

                    if data["importedNames"] == "True" :
                        self.importedNamesCsvFile = open(
                            f'records/{self.loadedFileName}/importedNames.csv', 'r')
                        self.forwardsTxt.setText(data["Forwards"])

                    if self.imgPath != "":
                        self.imageLbl.setPixmap(Qt.QPixmap(self.imgPath))
                    self.disableInputs()
                    self.populateContactList()
                    forwards = int(data["Forwards"])
                    self.Forwards = forwards
                    self.progressBar.setMaximum(forwards)
                    self.progressBar.setMinimum(0)
                    self.progressBar.setValue(len(self.contactDict))
                    self.progressLbl.setText(f"{len(self.contactDict)}/{forwards}")
                    self.progressBar.setVisible(True)
                    self.progressLbl.setVisible(True)

            else:
                self.enableInputs()
                self.loadRecordBtn.setText("load")
        else:
            self.enableInputs()
            self.loadRecordBtn.setText("load")
        

    def disableInputs(self):
        btnDisabledStyleSheet = "background-color: white;  border: 1px solid #ababab; border-radius: 10px; font-size: 12px;color: #ababab;text-align: center;"
        self.forwardsTxt.setEnabled(False)
        self.messageTxt.setEnabled(False)
        self.imageBtn.setStyleSheet(btnDisabledStyleSheet)
        self.imageBtn.setEnabled(False)
        self.importNamesBtn.setStyleSheet(btnDisabledStyleSheet)
        self.importNamesBtn.setEnabled(False)
        self.progressBar.setVisible(True)
        self.progressLbl.setVisible(True)

    @QtCore.pyqtSlot(bool, name="boolSignal")
    def checkConnection (self, connected):
        if (not connected):
            self.connErr.setErrorMsg(
                    "You appear to be offline, once you're connected to the internet the program will resume automatically")
            self.connErr.show()
            self.connErr.okBtn.setVisible(False)
            self.startBtn.setEnabled(False)
            self.startBtn.setStyleSheet("background-color: white;  border: 1px solid #ababab; border-radius: 10px; font-size: 12px;color: #ababab;text-align: center;")
            self.WhatsappForwader.state = False
            
        else :
            self.connErr.close()
            self.connErr.okBtn.setVisible(True)
            print(self.WhatsappForwader.isRunning())
            if not self.WhatsappForwader.isRunning() :
                self.startBtn.setEnabled(True)
                self.startBtn.setStyleSheet(
                "background-color: white;  border: 1px solid #139e2d; border-radius: 10px; font-size: 12px;color: #139e2d;text-align: center;")
            self.WhatsappForwader.state = True





    def enableLoadBtn(self):
        self.loadRecordBtn.setStyleSheet(
            "background-color: white;  border: 1px solid #139e2d; border-radius: 10px; font-size: 12px;color: #139e2d;text-align: center;")
        self.loadRecordBtn.setEnabled(True)
        self.forwardsTxt.setEnabled(True)
        self.forwardsTxt.setText("")


    def disableLoadBtn(self):
        self.loadRecordBtn.setEnabled(False)
        self.forwardsTxt.setEnabled(False)
        self.loadRecordBtn.setStyleSheet("background-color: white;  border: 1px solid #ababab; border-radius: 10px; font-size: 12px;color: #ababab;text-align: center;")

    def importNames(self):
        if (self.importedNamesCsvFile == None):
            filepicker = filePicker()
            filePath= filepicker.getFilePath()
            if filePath != "":
                self.importedNamesCsvFile = open(
                        filePath, 'r')
                self.populateContactList()
                self.disableLoadBtn()
                self.forwardsTxt.setText(str(len(self.importedContactDict)))
                self.importNamesBtn.setText("Unload")
        else :
            self.importedContactDict = {}
            self.importedNamesCsvFile = None
            self.contactList.clear()
            self.importNamesBtn.setText("Targeted Clients")
            self.enableLoadBtn()

    def searchContacts(self):
        # We search for anything that matches the search input in our List of
        # Contact names
        searchValue = self.searchTxt.toPlainText()
        matchedNames = self.contactList.findItems(
            searchValue, QtCore.Qt.MatchContains)
        listItems = [self.contactList.item(i)
                     for i in range(self.contactList.count())]
        for name in listItems:
            if name not in matchedNames:
                name.setHidden(True)
            else:
                name.setHidden(False)

    def populateContactList(self):  
        if self.importedNamesCsvFile == None and self.loadedCsvFile != None :
            reader = csv.DictReader(self.loadedCsvFile)
            for row in reader:
                self.contactDict[row['Name']] = 1
                item = QtWidgets.QListWidgetItem(row['Name'])
                self.contactList.addItem(item)

        elif self.importedNamesCsvFile != None and self.loadedCsvFile == None :
            reader = csv.DictReader(self.importedNamesCsvFile)
            for row in reader:
                self.importedContactDict[row['Name']] = 1
                item = QtWidgets.QListWidgetItem(row['Name'])
                color = Qt.QColor()
                color.setRgb(236,192,192)
                item.setBackground(color)
                self.contactList.addItem(item)
            
        elif self.importedNamesCsvFile != None and self.loadedCsvFile != None :
            reader = csv.DictReader(self.importedNamesCsvFile)
            readerScanned = csv.DictReader(self.loadedCsvFile)
            for row in reader:
                self.importedContactDict[row['Name']] = 1
            for row in readerScanned:
                self.contactDict[row['Name']] = 1
            
            for key in self.importedContactDict:
                if self.contactDict.get(key):
                    item = QtWidgets.QListWidgetItem(key)
                    color = Qt.QColor()
                    color.setRgb(195,236,192)
                    item.setBackground(color)
                    self.contactList.addItem(item)
                else :
                    item = QtWidgets.QListWidgetItem(key)
                    color = Qt.QColor()
                    color.setRgb(236,192,192)
                    self.remainingContactDict[key] = 1
                    item.setBackground(color)
                    self.contactList.addItem(item)

    @QtCore.pyqtSlot(str, name="strSignal")
    def appendName(self, name):
        if self.MODE == variables.NEW_NAMES:
            item = QtWidgets.QListWidgetItem(name)
            self.contactList.addItem(item)
        elif self.MODE == variables.IMPORTED_NAMES:
            listElement = self.contactList.findItems(name, QtCore.Qt.MatchExactly)
            if len(listElement) > 0:
                color = Qt.QColor()
                color.setRgb(195,236,192)
                listElement[0].setBackground(color)

    @QtCore.pyqtSlot(int, name="intSignal")
    def updatePB(self, val):
        self.progressBar.setValue(val)
        self.progressLbl.setText(f"{val}/{self.Forwards}")

    def is_number(self, s):
        try:
            int(s)
            return True
        except ValueError:
            return False

    def enableInputs(self):
        btnActiveStyleSheet = "background-color: white;  border: 1px solid #139e2d; border-radius: 10px; font-size: 12px;color: #139e2d;text-align: center;"
        self.forwardsTxt.setEnabled(True)
        self.forwardsTxt.setText("")
        self.contactDict = {}
        self.messageTxt.setEnabled(True)
        self.progressBar.setVisible(False)
        self.progressLbl.setVisible(False)
        self.progressBar.setValue(0)
        self.messageTxt.setText("")
        self.imageBtn.setStyleSheet(btnActiveStyleSheet)
        self.imageBtn.setEnabled(True)
        self.importNamesBtn.setStyleSheet(btnActiveStyleSheet)
        self.importNamesBtn.setEnabled(True)
        self.imageLbl.setPixmap(Qt.QPixmap(""))
        self.contactList.clear()
        self.imgPath = ""
        self.Forwards = ""
        self.Message = ""
        self.loadedCsvFile = None
        self.loadedJsonFile = None
        self.loadedFileName = None
        self.importedNamesCsvFile = None
        self.contactDict = {}
        self.importedContactDict = {}

    def getFiles(self):
        records = os.listdir("records/")
        for record in records:
            if record != '.DS_Store':
                self.recordList.addItem(
                    QtWidgets.QListWidgetItem(
                        os.path.splitext(record)[0]))

    def chooseImg(self):
        filepicker = filePicker()
        self.imgPath = filepicker.getFilePath()
        if self.imgPath != "":
            self.imageLbl.setPixmap(Qt.QPixmap(self.imgPath))


class filePicker(Qt.QWidget):

    def __init__(self):
        super().__init__()
        self.title = 'Choose File'
        self.left = 10
        self.top = 10
        self.width = 640
        self.height = 480
        self.filePath = ""
        self.initUI()

    def initUI(self):
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)
        self.openFileNameDialog()
        self.show()

    def openFileNameDialog(self):
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        fileName, _ = QFileDialog.getOpenFileName(
            self, "QFileDialog.getOpenFileName()", "", "All Files (*)", options=options)
        if fileName:
            self.filePath = fileName

    def getFilePath(self):
        return self.filePath


class errorWindow(Qt.QWidget):
    def __init__(self):
        Qt.QWidget.__init__(self)
        uic.loadUi('ui/error.ui', self)
        self.setWindowFlags(QtCore.Qt.FramelessWindowHint)
        self.warningImg.setScaledContents(True)
        self.warningImg.setPixmap(Qt.QPixmap("ui/warning.png"))
        self.okBtn.clicked.connect(self.exitWindow)
        self.errorTxt.setWordWrap(True)

    def setErrorMsg(self, msg):
        self.errorTxt.setText(msg)

    def exitWindow(self):
        self.close()


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = driver()
    app.exec_()
