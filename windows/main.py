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

class driver(Qt.QWidget):
    def __init__(self):
        super(driver, self).__init__()
        uic.loadUi(r'F:\whatsapp\ui\main.ui', self)
        self.show()
        self.setWindowTitle("Whatsapp Forwader")
        self.imgPath = ""
        self.Message = ""
        self.Forwards = ""
        self.isFileLoaded = False
        self.loadedJsonFile = None
        self.loadedCsvFile = None
        self.contactDict = {}
        self.WhatsappForwader = forwader.WhatsappForwader()
        self.WhatsappForwader.strContactSignal.connect(self.appendName)
        self.WhatsappForwader.updatePBsignal.connect(self.updatePB)
        self.loadRecordBtn.clicked.connect(self.load_record)
        self.startBtn.clicked.connect(self.runThread)
        self.imageBtn.clicked.connect(self.chooseImg)
        self.errorWindow = errorWindow()
        self.recordList.currentRowChanged.connect(self.enableLoadBtn)
        self.searchTxt.textChanged.connect(self.searchContacts)
        if (not os.path.isdir('records')):
            os.mkdir('records')
        self.setUpViews()
        self.WhatsappForwader.loadWebsite()

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
        self.startBtn.setStyleSheet(btnStyleSheet)
        self.getFiles()

    def runThread(self):

        self.Message = self.messageTxt.toPlainText()
        self.Forwards = self.forwardsTxt.toPlainText()

        if self.Message == "" and self.imgPath == "":
            self.errorWindow.setErrorMsg(
                "Please fill in at least one of the two :\n-Image path\n-Text Message\nOtherwise the program will not work")
            self.errorWindow.show()

        elif self.Forwards == "":
            self.errorWindow.setErrorMsg(
                "Please set the number of forwards (number of contacts to message)")
            self.errorWindow.show()

        elif int(self.Forwards) < 1:
            self.errorWindow.setErrorMsg(
                "Please enter a valid number for the forwards field")
            self.errorWindow.show()

        elif (self.isFileLoaded):
            self.WhatsappForwader.setForwards(self.Forwards)
            self.WhatsappForwader.setImagePath(self.imgPath)
            self.WhatsappForwader.setMessage(self.Message)
            self.WhatsappForwader.setFileName(self.loadedFileName)
            self.WhatsappForwader.setContactDict(self.contactDict)
            self.WhatsappForwader.setPreviewMode(
                self.previewCheckBox.isChecked())
            self.WhatsappForwader.start()
            self.startBtn.setStyleSheet(
            "background-color: white;  border: 1px solid #ababab; border-radius: 10px; font-size: 12px;color: #ababab;text-align: center;")


        else:
            currentDate = datetime.today().strftime("%Syo")
            os.makedirs(f'records/{currentDate}')
            jsonFile = open(f'records/{currentDate}/record.json', 'w+')

            jsonData = {
                "date": currentDate,
                "Forwards": self.Forwards,
                "Message": self.Message,
                "imagePath": self.imgPath
            }
            json.dump(jsonData, jsonFile)
            self.progressBar.setVisible(True)
            self.progressLbl.setVisible(True)
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
            self.WhatsappForwader.start()
            self.startBtn.setStyleSheet(
            "background-color: white;  border: 1px solid #ababab; border-radius: 10px; font-size: 12px;color: #ababab;text-align: center;")

    def load_record(self):
        if not self.isFileLoaded:
            if (self.recordList.currentItem()):
                self.isFileLoaded = True
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
            self.isFileLoaded = False
            self.enableInputs()
            self.loadRecordBtn.setText("load")

    def disableInputs(self):
        self.forwardsTxt.setEnabled(False)
        self.messageTxt.setEnabled(False)
        self.imageBtn.setStyleSheet(
            "background-color: white;  border: 1px solid #ababab; border-radius: 10px; font-size: 12px;color: #ababab;text-align: center;")
        self.imageBtn.setEnabled(False)
        self.progressBar.setVisible(True)
        self.progressLbl.setVisible(True)

    def enableLoadBtn(self):
        self.loadRecordBtn.setStyleSheet(
            "background-color: white;  border: 1px solid #139e2d; border-radius: 10px; font-size: 12px;color: #139e2d;text-align: center;")
        self.loadRecordBtn.setEnabled(True)

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
        reader = csv.DictReader(self.loadedCsvFile)
        for row in reader:
            self.contactDict[row['Name']] = 1
            item = QtWidgets.QListWidgetItem(row['Name'])
            self.contactList.addItem(item)

    @QtCore.pyqtSlot(str, name="strSignal")
    def appendName(self, name):
        item = QtWidgets.QListWidgetItem(name)
        self.contactList.addItem(item)

    @QtCore.pyqtSlot(int, name="intSignal")
    def updatePB(self, val):
        self.progressBar.setValue(val)
        self.progressLbl.setText(f"{val}/{self.Forwards}")

    def enableInputs(self):
        self.forwardsTxt.setEnabled(True)
        self.forwardsTxt.setText("")
        self.contactDict = {}
        self.messageTxt.setEnabled(True)
        self.progressBar.setVisible(False)
        self.progressLbl.setVisible(False)
        self.progressBar.setValue(0)
        self.messageTxt.setText("")
        self.imageBtn.setStyleSheet(
            "background-color: white;  border: 1px solid #139e2d; border-radius: 10px; font-size: 12px;color: #139e2d;text-align: center;")
        self.imageBtn.setEnabled(True)
        self.imageLbl.setPixmap(Qt.QPixmap(""))
        self.contactList.clear()
        self.imgPath = ""
        self.Forwards = ""
        self.Message = ""

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
        uic.loadUi(r'F:\whatsapp\ui\error.ui', self)
        self.setWindowFlags(QtCore.Qt.FramelessWindowHint)
        self.warningImg.setScaledContents(True)
        self.warningImg.setPixmap(Qt.QPixmap(r'F:\whatsapp\ui\warning.png'))
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
